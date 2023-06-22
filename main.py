import requests
import json
import asyncio
from bs4 import BeautifulSoup
import pandas as pd
from telegram import Bot
import dataframe_image as dfi
from CREDS import GROUP_CHAT_ID, BOT_TOKEN
import matplotlib.pyplot as plt
import matplotlib as mpl


bot = Bot(token=BOT_TOKEN)

def risk_condition(v):
    if v < 20:
        return "LOW"
    elif v < 30:
        return "MEDIUM"
    return "HIGH"

def color_row(row):
    if row['FWI'] < 10:
        return ['background-color: #00ff00'] * len(row)
    elif 10 <= row['FWI'] < 20:
        return ['background-color: #ffff00'] * len(row)
    elif 20 <= row['FWI'] < 30:
        return ['background-color: #ffaa00'] * len(row)
    else:
        return ['background-color: #ff0000'] * len(row)


async def main():
    with open("zone.json", "r") as f:
        zone = json.load(f)

    if not zone:
        return
    df = pd.DataFrame(zone, columns=['id', 'name'])

    # get zone danger
    a = requests.get("https://www.ambienteveneto.it/incendi/dati/FWI.json", verify=False).json()
    data = a["GIORNI"][0]["ZONE"]
    d_danger = pd.DataFrame(data)
    df = pd.merge(df, d_danger, how='inner', left_on='id',right_on='ZONA')
    df.drop('id', axis=1, inplace=True)
    df.to_html('index.html', index=False)

    print(df)

    
    formatted_table = df.sort_values('name')[['name', 'FWI']]
    styled_df = formatted_table.style.apply(color_row, axis=1)


    styled_html = styled_df.to_html(index=False)
    import imgkit

    # with open('index.html', 'w') as f:
    #     f.write(styled_html)



    image_path = 'o.jpg'
    a = imgkit.from_string(styled_html, image_path)
    await bot.send_photo(GROUP_CHAT_ID,photo=open(image_path, 'rb'))



    # Format the DataFrame as a pretty table

    

if __name__ == "__main__":
    asyncio.run(main())
    