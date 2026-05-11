import os
import json
import asyncio
from bs4 import BeautifulSoup
import pandas as pd
from telegram import Bot, InputMediaPhoto
from datetime import datetime
import numpy as np
import imgkit
from dotenv import load_dotenv

from collectors import VenetoConnector

# locale.setlocale(locale.LC_TIME, 'it_IT')

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
        connector = VenetoConnector(
            "zone.json",
            verify_ssl=os.getenv("VENETO_SOURCE_VERIFY_SSL", "false").lower() == "true",
        )
        bulletin = connector.parse_bulletin(connector.fetch_source())
        date = bulletin.valid_for_date.strftime("%d/%m/%y")
        df = pd.DataFrame([entry.to_dict() for entry in bulletin.entries])
        df.rename(columns={"zone_id": "id", "zone_name": "name", "fwi": "FWI", "indice": "INDICE", "risk_level": "RISCHIO"}, inplace=True)

        ## MAP
        map_soup = BeautifulSoup(connector.fetch_map_svg(), 'lxml')
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

        output_day = bulletin.valid_for_date.strftime("%Y%m%d")
        table_path = 'media/%s_table.jpg'%(output_day)
        map_path = 'media/%s_map.jpg'%(output_day)

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
            caption="🔥🌲<b>NUOVO BOLLETTINO %s</b>\nOgni giorno un nuovo bollettino di pericolo incendi boschivi.\n<a href=\"https://www.ambienteveneto.it/incendi/index.html\">Ulteriori informazioni</a>\nProssimo bollettino domani pomeriggio!"%(date))
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
    
