from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from time import sleep
import os
import datetime

url = "http://www.ambienteveneto.it/incendi/index.html"
folder = "maps"

def get_image():

    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-ssl-errors=yes')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--headless')

    driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)

    print("Getting main page")
    driver.get(url)
    sleep(5)

    print("Looking for svg")
    svg = driver.find_element_by_xpath('//*[@id="svgVeneto"]')
    driver.close()

    if(svg):
        return svg.get_attribute("outerHTML")
    else:
        return False


def download(svg):

    if svg == False: return

    # create folder "maps" if does not exist
    if not os.path.exists(folder):
        os.makedirs(folder)

    # create file name
    now = datetime.datetime.now()
    file_name = "map" + now.strftime("%Y%m%d_%H%M%S") + ".svg"
    
    # define file path
    file_path = os.path.join(folder, file_name)
     
    # write
    with open(file_path, "w") as f:
        f.write("hi")

s = get_image()
if s:
    download(s)