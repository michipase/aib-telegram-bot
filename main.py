import os
import requests
import json
import asyncio
from bs4 import BeautifulSoup
import pandas as pd
from telegram import Bot, InputMediaPhoto
import dataframe_image as dfi
from CREDS import GROUP_CHAT_ID, BOT_TOKEN
import matplotlib.pyplot as plt
import matplotlib as mpl
import locale
from datetime import datetime
import numpy as np
import imgkit

# locale.setlocale(locale.LC_TIME, 'it_IT')


bot = Bot(token=BOT_TOKEN)
MAX_LOW = 16    #! TO CHECK
MAX_MEDIUM = 24 #! TO CHECK
MAX_HIGH = 32   #! TO CHECK

def risk_condition(v):
    if v < MAX_LOW:
        return "BASSO"
    elif v < MAX_MEDIUM:
        return "MEDIO"
    return "ALTO"

def color_row(row):
    if row['FWI'] < MAX_LOW:
        return ['background-color: #00ff00'] * len(row)
    elif MAX_LOW <= row['FWI'] < MAX_MEDIUM:
        return ['background-color: #ffff00'] * len(row)
    elif MAX_MEDIUM <= row['FWI'] < MAX_HIGH:
        return ['background-color: #ffaa00'] * len(row)
    else:
        return ['background-color: #ff0000'] * len(row)

def calc_risk(fwi):
    if fwi < MAX_LOW:
        return "BASSO"
    elif MAX_LOW <= fwi < MAX_MEDIUM:
        return "MEDIO"
    elif MAX_MEDIUM <= fwi < MAX_HIGH:
        return "ALTO"
    else:
        return "MOLTO ALTO"
def set_fill(id,df):
    a = df.loc[df['ZONA'] == id, 'FWI']
    fwi = a.iloc[0]

    if fwi < MAX_LOW:
        return "#00ff00"
    elif MAX_LOW <= fwi < MAX_MEDIUM:
        return "#ffff00"
    elif MAX_MEDIUM <= fwi < MAX_HIGH:
        return "#ffaa00"
    else:
        return "#ff0000"



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

        df['RISCHIO'] = df.apply(lambda x: calc_risk(x['FWI']), axis=1)

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
        formatted_table = df.sort_values('name', ignore_index=True)[['name', 'FWI', 'RISCHIO']]
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
            caption="🔥🌲<b>NUOVO BOLLETTINO %s</b>\nOgni giorno un nuovo bollettino di pericolo incendi boschivi.\n<a href=\"https://www.ambienteveneto.it/stazioni/incendi/index.html\">Ulteriori informazioni</a>\nProssimo bollettino ore 15:00 di domani!"%(date))
        )
        media.append(InputMediaPhoto(media=open(table_path, 'rb')))

        await bot.send_media_group(
            GROUP_CHAT_ID,
            media=media,
        )

    

if __name__ == "__main__":
    asyncio.run(main())
    