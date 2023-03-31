from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager

url = "https://www.ambienteveneto.it/incendi/index.html"

driver = webdriver.Chrome(ChromeDriverManager().install())

driver.get(url)