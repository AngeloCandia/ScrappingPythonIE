#########################################################################
from os import walk
import datetime 
import locale
from pytz import timezone
from tzlocal import get_localzone
import time 
import sys 
import os
#########################################################################
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import pandas as pd
#########################################################################
from .alert import run_log_error
#########################################################################

def get_date():
    
    timezoneAM = 'America/Santiago'

    try:
        
        now_time = datetime.datetime.now(timezone(timezoneAM))
    
    except:
    
        now_time = datetime.now(timezone(timezoneAM))
    
    return now_time

def scrap_page():

    # Url a la pagina Orpak
    url = "https://mlp.orpak-la.com/"

    # Asignar ejecutable para abrir internet Explorer
    driver = webdriver.Ie('etc/IEDriverServer.exe')
    
    # El scrapping esperara X segundos maximo por cada busqueda de elemento
    driver.implicitly_wait(15)
    
    # Abrir navegador e ir a la pagina de Orpak
    driver.get(url)
    
    # Retorna el objeto driver
    return driver

def select_columns(driver):
    
    # Lista con los valores de cada campo a seleccionar
    order_list = (1, 2, 3, 4, 6, 8, 15, 19)

    # Variable de tipo indice
    num_colum = 1

    # Variable que retorna al final de la funcion, indicando si funciono o no 
    fallido = False

    # Loop de order_list
    for ol in order_list:
    
        # El scrapping descansa 1 segundo
        time.sleep(1)
        
        # Las columnas 15 y 19 son casos excepcionales
        if ol  == 15 or ol == 19 : #VALIDAMOS COLUMNA 7 Y 8 DE ESTA MANERA POR QUE NO SE PUEDE BAJAR EL SCROLL
        
            # Buscamos el campo checkbox de la columna en base a 'ol' que es 'ordr_list'
            order = driver.find_element_by_id(f'order_{str(ol)}')

            # Le asignamos un valor numero, este valor indica el orden de las columnas del documento a descargar
            # el -1 siempre va
            driver.execute_script(f"arguments[0].value = {str(num_colum-1)};", 
                                    order) 
            
            try:
        
                # Validamos si 'order' + 1 no es igual a num_colum
                if int(order.get_attribute('value')) + 1 != num_colum :
        
                    # Si no fueran iguales, el orden de las columnas es erronea, por lo que se volveria a ejecutar
                    # mas adelante

                    #Variable si indica si esta correcto o no
                    fallido = True

                #colum = int(order.get_attribute('value')) + 1

            except ValueError:
            
                print("[controller.functions.select_columns] Error columnas Orpak")

        else :
            
            # Para el resto de numeros

            # Buscamos la casilla en base a 'ol'
            order = driver.find_element_by_id('order_'+str(ol))
        
            # Le damos click al campo
            order.click()

            try:
            
                # Al igual que el if anterior, validamos que 'order' sea distinto a 'num_colum'
                if int(order.get_attribute('value')) != num_colum :

                    # Si son distintos, la ejecucion de la funcion fue fallida y se volvera a ejecutar
                    fallido = True
    
            except ValueError:
            
                print("[controller.functions.select_columns] Error columnas Orpak")

        num_colum += 1

    # Retorna fallido, si es True , se volvera a ejecutar , si es False, volvera a ejecutarse 
    return fallido

def current_week(anterior=False):
    
    # Este codigo permite que el scrapping funcione correctamente los Domingos
    locale.setlocale(locale.LC_ALL, 'Spanish_Spain.1252')

    #MODO PRUEBA
    #year = 2020
    #month = 1
    #day = 1

    # Obtener el año , mes y dia de hoy
    year = int(time.strftime("%Y"))
    month = int(time.strftime("%m"))
    day = int(time.strftime("%d"))

    # Validar que el mes sea igual a 12 y dia sea mayor a 24 o mes igual a 1 y menor a 15
    ##############################################################################################
    # Cuando se entra en el if, en vez de sacar sacar el numero de semana normalmente
    # se usara un pkl con estos datos (mes y dia ) por defecto para obtener el numero de la semana
    # esto porque las ultimas y primeras semanas del año, el scrapping falla en el calendario
    ##############################################################################################
    if month == 12 and day > 24 or month == 1 and day < 15 :
        
        # Validar que el dia a sacar el de hoy o el de ayer
        if anterior:
        
            # Obtener el dia de ayer
            #day = day - 1
            day = int(time.strftime("%d")) - 1

            # Validar si el dia es 0
            if day == 0 :
        
                # Obtener la fecha del año y mes actual y por defecto poner el dia 1
                # puesto que si es 0 le sumas 1
                before_date = datetime.datetime.strptime(str(year) + '-' + str(month) + '-' + '01', '%Y-%m-%d') + datetime.timedelta(days=0)
                
                # Le restamos a la fecha 1 dia
                before_date = datetime.datetime.strptime(str(before_date.date()),  '%Y-%m-%d') - datetime.timedelta(days=1)
                
                # Obtenemos el año , mes y dia   de before_date
                year = int(before_date.strftime('%Y'))
                month = int(before_date.strftime('%m'))
                day = int(before_date.strftime('%d'))

            # Se lee el pkl con columnas fecha y numero de semana
            bd_date = pd.read_pickle(os.getcwd()+"/document/other/last_week_year.pkl")
            
            # Se busca el numero de semana con el año , mes y dia obtenidos anteriormente
            num_semana = bd_date.loc[str(year)+"-"+str(month)+"-"+str(day)][0]

            # Devuelve num semana , dia y mes
            return num_semana, day, month

        # Si el dia es el de hoy
        else:
        
            # Obtener el dia de hoy actual
            #day = day
            day = int(time.strftime("%d"))

            # Se lee el pkl con columnas fecha y numero de semana
            bd_date = pd.read_pickle(os.getcwd()+"/document/other/last_week_year.pkl")
            
            # Se busca el numero de semana con el año , mes y dia obtenidos anteriormente
            num_semana = bd_date.loc[str(year)+"-"+str(month)+"-"+str(day)][0]
            
            # Devuelve num semana , dia y mes
            return num_semana, day, month

    # Para el resto de dias
    else:
        
        # Calcular dia de ayer
        if anterior: 

            # Obtener el dia - 1
            #day = day -1
            day = int(time.strftime("%d")) -1

            # Valida si el dia es 0
            if day == 0 :

                # Obtiene la fecha del mes y año actual con el dia 1 por fecto
                before_date = datetime.datetime.strptime(str(year) + '-' + str(month) + '-' + '01', '%Y-%m-%d') + datetime.timedelta(days=0)
                
                # Le restamos un dia a esa fecha
                before_date = datetime.datetime.strptime(str(before_date.date()),  '%Y-%m-%d') - datetime.timedelta(days=1)
                
                # Obtener año , mes y dia a partir de la fecha obtenida
                year = int(before_date.strftime('%Y'))
                month = int(before_date.strftime('%m'))
                day = int(before_date.strftime('%d'))
                
        # Para el resto de dias
        else:
            
            # Obtener el dia actual
            #day = day
            day = int(time.strftime("%d"))

        # Obtenemos el nombre del dia ["Lunes","Martes","etc"] a partir del dia , mes y año
        dia_semana = datetime.datetime.strptime(str(day)+'-'+str(month)+'-'+str(year), '%d-%m-%Y').strftime('%A') #%A = Nombre del dia ["Miercoles","Jueves","etc"]

        #Validar si el dia es el de ayer
        if anterior: 

            # Se valida si el dia es "lunes" y el dia no sea el de ayer
            if dia_semana == "lunes" and anterior == False: #VALIDAR QUE EL DIA DE HOY SEA LUNES NOOO EL DE AYER
                
                # Obtener el numero de la semana
                current_week = datetime.date(year, month, day).isocalendar()[1]  

            # Validar si el dia es "domingo"
            elif dia_semana == "domingo":

                # Obtener el numero de la semana
                current_week = datetime.date(year, month, day).isocalendar()[1] 

            # Para el resto de dias "martes" a "sabado"
            else:

                # Obtener el numero de la semana - 1
                current_week = datetime.date(year, month, day).isocalendar()[1] - 1
        
        # Cuando el dia sea el de hoy
        else:
            
            # Si el dia de la semana es "domingo"
            if dia_semana == "domingo":

                # Obtener el numero de la semana
                current_week = datetime.date(year, month, day).isocalendar()[1] 

            # Para el resto de dias
            else:

                # Obtener el numero de semana -1
                current_week = datetime.date(year, month, day).isocalendar()[1] - 1

        # Retornar el numero de semana , dia y mes
        return current_week, day, month

def document_week(driver, class_name, numero_semana, dia, mes, h, m): #funcion que mueve el calendario hoy y ayer
    
    # Diccionario con la lista de meses en y su valor numerico correspondiente
    month_orpak = { 
        'January': 1, 'February': 2, 'March': 3,
        'April': 4, 'May': 5, 'June': 6,
        'July': 7, 'August': 8, 'September': 9,
        'October': 10, 'November': 11, 'December': 12
    }

    timeout = 10 #tiempo de espera a que calendario este disponible

    diferencia = 0 #la diferenecia del mes actual con el que se busca
    #ejemplo:
        #marzo 2020 : 0 (es el actual)
        #enero 2020 : 2 (dos meses antes del actual)

    current_year = int(time.strftime('%Y')) #obtener el año actual

    driver.find_element_by_id(class_name).click() #buscar calendario orpack

    try:
    
        element_present = EC.presence_of_element_located((By.CLASS_NAME, 'calendar')) #validar que este presente el calendario
    
        WebDriverWait(driver, timeout).until(element_present) #esperar 10 segundos

    except TimeoutException:

        return False #devuelve False si el calendario no esta disponible

    finally:
        
        try:

            calendar = driver.find_element_by_class_name("calendar") #guardar calendario en variable

        except:

            return False #devuelve False si se cae

    list_days = list() # Lista vacia que contendra los dias de la semana

    week = calendar.find_elements_by_css_selector("tr[class='daysrow']") #GET CURRENT WEEKS OF THE CURRENT MONTH

    mes_orpack = calendar.find_element_by_class_name('title').text #obtiene titulo mes actual
    
    for month, values in month_orpak.items() : #recorre el diccionario month_orpack

        if mes_orpack.find(month) != -1 : #valida que mes_orpack(del calendario web) sea igual a month (nombre mes del diccionario)
            
            mes_cal = values
            
            #diferencia = diferencia + 1
            #Comente esta linea (la de arriba) porque hubo problemas para scrapear el dia '01-03-2020' cuando era hoy
            #el dia de ayer lo sacaba como 26-01-2020
            #queda verificar que el scrapping siga funcionado que el resto de cada mes cuado sea el primer dia

            #Nota 2: la linea de arriba fue para evitar problemas con el dia 01-01-2020, que queda en un buvle infinito
            
            break
        
        # Si no es igual
        else:
            
            # Suma diferencia + 1
            diferencia += 1

    # En todos los casos a diferencia se le suma + 1 y se le resta el numero de meses de diferencia
    diferencia = ( diferencia + 1 ) - mes

    #print("Diferencia: " + str(diferencia))

    # Validar si el mes del calendario es igual al mes actual
    if mes_cal ==  mes : 

        pass
    
    else: #CAMBIAR CALENDARIO AL MES ANTERIOR

        # Buscar el boton para moverse entre meses
        move_cal =  calendar.find_elements_by_css_selector("td[class='button nav']")
        
        # Loop de barra opciones del calendario
        for x in move_cal:
            
            # Validar que el texto sea del icono para retroceder
            if x.text == "‹":
                
                if diferencia == -1: #VALIDA QUE LA DIFERENCIA -1, ESTO OCURRE CUANDO SE BUSCAN DATOS FUTUROS QUE NO EXISTEN

                    sys.exit(0) #se finaliza el scrapping si los datos son futuros

                # Si diferencia no es igual a -1, hay que mover el calendario al pasado
                else:

                    # Validar que el mes sea a 1 o 11,  son casos excepcionales
                    if mes == 1 and diferencia == 11:

                        # Le restamos diferencia a 1
                        diferencia -= 1

                    # Validar que diferencia sea igual a - 10
                    elif diferencia == -10 : #VALIDA QUE EL DIA ANTERIOR SEA EL AÑO PASADO

                        # Diferencia se vuelve igual a 1
                        diferencia = 1

                    # While que valida que diferencia sea distinto a 0
                    while diferencia !=0:
                        # Click al boton para retroceder el calendario
                        x.click()

                        # Restar diferencia -1
                        diferencia -= 1
                    
                    # Termina el loop para mover el calendario al pasado
                    break

    for w in week: #RECORRE TODAS LAS SEMANAS DEL MES
    
        n_week = w.find_element_by_css_selector("td[class=' day wn']").text  #numero de semana del año 

        if int(n_week) == numero_semana: #valida que el numero semana de hoy, sea el que se busca
        
            day = w.find_elements_by_class_name("day") #GET ALL DAYS OF THE WEEKEND

            day.pop(0) #borra el primer elemento de la lista, el primer elemento es el numero de la semana NO UN DIA!!

            for d in day: #recorre los dias de la semana
            
                if d.text == " ": 
                    
                    print("[controller.functions.document_week] Dia vacio")
                
                # Validar que el dia del calendario sea igual al del dia ingresado y la hora e minuto sean igual al deseado
                elif int(d.text) == int(dia) and h == "23" and m == "59"\
                    or int(d.text) == int(dia) and h == "00" and m == "00":
                    #MOVE HOUR TO 00       
                    hour = calendar.find_element_by_class_name("hour")
                    
                    # Validar que hora sea distinto a 23 o 00
                    while hour.text!= h:
                        # Click al boton para cambiar la hora
                        hour.click()
                    
                    #MOVE MINUTE TO 00
                    minute = calendar.find_element_by_class_name("minute")
                    
                    # Validar que minuto sea distinto a 59 y 00
                    while minute.text != m:
                        # Click al boton para cambiar la hora
                        minute.click()
                    
                    # Click al boton del dia
                    d.click()

                    # Retorna True , significa que funciono perfectamente
                    return True
                    
                # Valida que el dia del calendario sea menor igual a 32
                elif int(d.text)<=32:
                    # Se agrega el dia a una lista de dias
                    list_days.append(d)
                
    #SI EL FOR NO ENCUNETRA EL ULTIMO DIA QUE ES FIN DE SEMANA, SE BUSCA MEDIANTE OTRA CLASE
    last_week = calendar.find_elements_by_css_selector("td[class=' day weekend']")
    
    # Obtiene el ultimo dia de la semana de forma bruta
    last_week[-1].click()

    # Retorna True
    return True

def create_html_document(driver, popup, document_page, main_page, name):
    # Variable con la ruta base del sistema hasta la carpeta del proyecto
    ruta_fija = os.getcwd().replace("\\", "/") + "/" # = C:/Users/Angelo/Documents/cosmos_scraping/

    # Obtener la fecha de hoy
    current_date_2 = datetime.datetime.now()
    
    # Definir un timeout de 30 segundos
    timeout = 30

    try:
    
        # Seleccionamos el elemento 'report_prev'
        element_present = EC.presence_of_element_located((By.ID, 'report_prev'))
        
        # Lo obtenemos dentro del timeout que se definio anteriormente
        WebDriverWait(driver, timeout).until(element_present)

    # Si el timeout pasa
    except TimeoutException as e:
    
        # Obtener la linea de error , tipo error y nombre del error
        line_error, name_error, d_name_error = 'Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e

        try:

            # Llamar a la funcion run_log_error
            run_log_error(line_error, name_error, d_name_error, False)

        except Exception as e:
            # Llama a la funcion run_log_error si se cae dentro del try
            run_log_error(line_error, name_error, d_name_error, True)

        # Finalizamos la ejecucion del scrapping
        driver.quit()

        # Se detiene la ejecucion del programa abruptamente
        sys.exit(0)

    # Si encuentra el elemento a buscar
    finally:
        # Click al elemento 'report_prev' que contiene los datos que necesitamos en HTML
        driver.find_element_by_id("report_prev").click()
    
    # Definir una variable indice igual a 0
    i = 0
    
    # Mientra i sea menor igual a 250
    while i<=250: 
        # Actualizamos la variable popup por cada iteracion
        popup = driver.window_handles
    
        # Si el largo de popup es mayor igual a 3, significa que la pagina ya cargo    
        if len(popup) >= 3:
            # Termina el while
            break
        
        # Sumamos indice + 1
        i += 1

    # En caso de que popup sea menor igual a 2 , siginifica que la pagina no cargo bien , hacemos otro loop
    while len(popup) <=2 :
        # Volver a buscar el boton 'report_prev'
        driver.find_element_by_id("report_prev").click()
        
        # Confirmar si popup es mayor igual a 3
        popup = driver.window_handles

    # Obtenemos las 3 ventanas que estan abiertas actualmente
    c_main_page, c_document_page, html_table = popup

    # Cambiamos a la ventana html_table
    driver.switch_to.window(html_table)

    # la variable popup_len vuelve a ser 0
    popup_len = 0
    
    # Validar que el titulo de la ventana sea el correcto
    while driver.title != "SiteOmat - Custom report":
        # Validar el largo de popup_len = 0
        if popup_len == 0  :

            # Asumimos que la ventana que buscamos sea la primera
            html_table, _, _ = popup

            # Camibar la primera ventana
            driver.switch_to.window(html_table)

        # Validar el largo de popup_len = 1
        elif popup_len == 1 :
            
            # Asumimos que la ventana que buscamos sea la segunda
            _, html_table, _ = popup

            # Cambiar a la segunda ventana
            driver.switch_to.window(html_table)

        # Validar el largo de popup_len = 2
        elif popup_len == 2 :
            # Asumimos que la ventana que buscamos sea la tercera
            _, _, html_table = popup

            # Cambiar a la tercera ventana
            driver.switch_to.window(html_table)

        # Si no es ninguna de las tres
        else:
            # Rompemos el while
            break

        # Se suma popup_len + 1
        popup_len += 1

    # Buscamos el contenido html de la pagina
    html = driver.find_element_by_tag_name('html')

    # Abrimos un archivo html 'filename.html' nuevo
    Html_file= open("document/filename.html", "w")

    # Escribir en el archivo nuevo todo el contenido HTML obtenido en la paventana
    Html_file.write(html.get_attribute('innerHTML'))

    # Cerrar el archivo
    Html_file.close()

    # Dataframe que contendra todo el contenido del dia
    final = None

    # Fecha de hoy
    current_date = time.strftime("%Y-%m-%d-%H-%M")
    
    # Realziamos un scrapping al archivo HTML local
    soup = BeautifulSoup(open(ruta_fija+"document/filename.html"), "html.parser")

    # Buscamos todas las talas HTML
    tbl =soup.findAll("table")

    # Cargamos la primera tabla que se encuentra en un DataFrame
    table_frame = pd.read_html(str(tbl),header=[0])[1] 
    
    # Definir columnas a utilizar
    table_frame.columns =  ['Ser. No', 'Station Name', "Fecha", 'Time',
                            'Flota', 'Equipo', 'Cantidad', "Department",
                            'Pump']

    # Concatenamos final con el DataFrame nuevo
    final = pd.concat([final, table_frame]) # Creo que la variable final no se esta utilizando

    # Pasamos los datos a un PKL y se guarda momentaneamente en local
    final.to_pickle(ruta_fija+f"document/new_data{name}.pkl")
    
    # Se cierra la ventana del boton 'report_prev'
    driver.close()
    
    # Volvemos a la pagina anterior 'El formulario'
    driver.switch_to.window(document_page)