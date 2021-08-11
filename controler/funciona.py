from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


url = "http://www.duoc.cl/inicio"

# Asignar ejecutable para abrir internet Explorer
driver = webdriver.Ie('etc/IEDriverServer.exe')

# El scrapping esperara X segundos maximo por cada busqueda de elemento
driver.implicitly_wait(1)

# Abrir navegador e ir a la pagina de Orpak
driver.get(url)

driver.title