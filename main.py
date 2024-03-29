import os
import requests
import json
import asyncio
from bs4 import BeautifulSoup
import pandas as pd
from telegram import Bot, InputMediaPhoto
from datetime import datetime
import numpy as np
import imgkit
from dotenv import load_dotenv

# locale.setlocale(locale.LC_TIME, 'it_IT')

BOT_TOKEN = os.environ["BOT_TOKEN"]
GROUP_CHAT_ID = os.environ["GROUP_CHAT_ID"]
try:
    BOT_TOKEN = os.environ['BOT_TOKEN']
    GROUP_CHAT_ID = os.environ['GROUP_CHAT_ID']
except:
    load_dotenv()
    BOT_TOKEN = os.getenv('BOT_TOKEN')    
    GROUP_CHAT_ID = os.getenv('GROUP_CHAT_ID')    

if BOT_TOKEN is None or GROUP_CHAT_ID is None:
    print('Missing Tokens')
    quit()
bot = Bot(token=BOT_TOKEN)

def color_row(row):
    try:
        if row['INDICE'] <= 2:
            return ['background-color: #00ff00'] * len(row)
        elif row['INDICE'] == 3:
            return ['background-color: #ffff00'] * len(row)
        elif row['INDICE'] == 4:
            return ['background-color: #ffaa00'] * len(row)
        else:
            return ['background-color: #ff0000'] * len(row)
    except:
        return ['background-color: #cccccc'] * len(row)

def calc_risk(indice):
    try:
        if indice <= 2:
            return "BASSO"
        elif indice == 3:
            return "MEDIO"
        elif indice == 4:
            return "ALTO"
        else:
            return "MOLTO ALTO"
    except:
        return "ND"

def set_fill(id,df):
    try:
        a = df.loc[df['ZONA'] == id, 'INDICE']
        indice = a.iloc[0]

        if indice <= 2:
            return "#00ff00"
        elif indice == 3:
            return "#ffff00"
        elif indice == 4:
            return "#ffaa00"
        else:
            return "#ff0000"
    except:
        return "#cccccc"



async def main():
    with open("log.txt", "w+") as log:
        
        with open("zone.json", "r") as f:
            zone = json.load(f)

        if not zone:
            return
        
        # create zone dataframe from file
        df = pd.DataFrame(zone, columns=['id', 'name'])

        # get zone danger
        a = requests.get("https://www.ambienteveneto.it/incendi/dati/FWI.json", verify=False).json()

        d = datetime.strptime(str(a['GIORNI'][0]['GIORNO']), "%Y%m%d")
        date = d.strftime("%d/%m/%y")

        # extract date
        data = a["GIORNI"][0]["ZONE"]

        # create danger dataframe
        d_danger = pd.DataFrame(data)

        # merge zone names dataframe to danger dataframe
        df = pd.merge(df, d_danger, how='inner', left_on='id',right_on='ZONA')
        df['id'] = pd.to_numeric(df['id'], errors='coerce')
        # filter for useful id
        df = df[df['id'] <= 26]

        df['RISCHIO'] = df.apply(lambda x: calc_risk(x['INDICE']), axis=1)

        df['name'] = np.where(df['name'].str.contains('Non Montana'),
                            df['name'].str.replace('Non Montana ', '') + ' Non Montana',
                            df['name'])

        ## MAP
        veneto_map = requests.get("https://www.ambienteveneto.it/stazioni/incendi/venetorischio.html", verify=False).content
        map_soup = BeautifulSoup(veneto_map, 'lxml')
        gs = map_soup.find_all(name="g", id=lambda value: value and "GI_" in value)
        for g in gs:
            g['fill'] = set_fill(g['id'][3:],df)
        map_svg = map_soup.prettify()

        # make it cool
        formatted_table = df.sort_values('name', ignore_index=True)[['name', 'FWI', 'INDICE', 'RISCHIO']]

        print(formatted_table)

        styled_df = formatted_table.style \
            .apply(color_row, axis=1) \
            .format(precision=2, thousands=".", decimal=",") \
            .set_caption("Rischio incendio 🔥🌲</br>Aggiornamento: <b>%s</b>"%(date))


        styled_html = styled_df.to_html(index=False, classes="df_style.css")

        table_path = 'media/%s_table.jpg'%(str(a['GIORNI'][0]['GIORNO']))
        map_path = 'media/%s_map.jpg'%(str(a['GIORNI'][0]['GIORNO']))

        table = imgkit.from_string(
            styled_html,
            table_path,
            options={
                "width": 600
            },
            css="style/df_style.css",
        )
        map = imgkit.from_string(
            map_svg,
            map_path,
            options={
                "width": 600
            }
        )

        media = []
        media.append(InputMediaPhoto(
            media=open(map_path, 'rb'),
            parse_mode="HTML", 
            caption="🔥🌲<b>NUOVO BOLLETTINO %s</b>\nOgni giorno un nuovo bollettino di pericolo incendi boschivi.\n<a href=\"https://www.ambienteveneto.it/stazioni/incendi/index.html\">Ulteriori informazioni</a>\nProssimo bollettino domani pomeriggio!"%(date))
        )
        media.append(InputMediaPhoto(media=open(table_path, 'rb')))

        await bot.send_media_group(
            GROUP_CHAT_ID,
            media=media,
        )

    

if __name__ == "__main__":
    if not os.path.exists("media"):
        os.makedirs("media")

    asyncio.run(main())
    
