import configparser
import os
import sys
import time
import warnings
from datetime import datetime, timedelta
from pytz import timezone
import boto3
import pandas as pd
from bs4 import BeautifulSoup
from controler import (Bucket, create_html_document, create_log,
                       current_week, del_log_error,document_week, 
                       email, read_log, run_log_error,scrap_page, 
                       select_columns, get_date)
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

warnings.filterwarnings('ignore')

def run():

    # Ruta fija desde el sistema operativo hasta la carpeta del proyecto
    ruta_fija = os.getcwd().replace("\\","/") + "/"

    # Variable conf
    config = configparser.ConfigParser()

    # leer archivo ini
    config.read('etc/config.ini')
    
    # Obtener fecha hoy
    fecha_hoy = get_date()
    
    # Obtener fecha ayer
    fecha_ayer = get_date() - timedelta(days=1)
    
    try:
        
        # Obtener fecha actual
        current_date_2 = datetime.now(timezone("America/Santiago")).strftime("%Y-%m-%d %H:%M:%S")
        
        # Pasar current_date_2 a dateTime
        current_date_2 = datetime.strptime(current_date_2 ,"%Y-%m-%d %H:%M:%S") + timedelta(days=0)

        # Obtener la fecha actual del archivo 'alerta.txt' , usando funcion read_log()
        ultima_fecha = read_log()

        # Resta la fecha actual con la fecha del archivo 'alerta.txt'
        total = current_date_2 - ultima_fecha 

        # Obtener hora , en base a la resta anterior
        total = int ( round( ( total.total_seconds()  / 3600), 0) )

        # Valida que la hora este en un valor entre 8 y 9
        if total >= 8 and total < 9:  
            email.send(str(ultima_fecha))

            # Borra el archivo 'alerta.txt' y crea uno nuevo con la fecha actual
            del_log_error()

    except Exception as e:

        print("[app.run.alert] Error al generar alert")

    try:

        # Variable indice, se usa para whiles
        i  = 0

        # Instanciar funciones del scrapping

        # Iniciar scrapping
        driver = scrap_page()

        # Obtiene las ventanas que abre Orpak
        popup = driver.window_handles 

        # Asignamos las dos ventanas a dos variables
        main_page, login_page = popup

        # Cambiar a la ventana Login
        driver.switch_to.window(login_page)

        # Validar que la ventana que se cambio sea efectivamente la del login
        if driver.title == "Enlace - SiteOmat" :
            print("[app.run] Error al cambiar pagina login")

        else:
            # Cambiarse a la otra ventana que si es la del login  
            driver.switch_to_window(main_page)

        # Buscar el input del user
        user = driver.find_element_by_id("User")

        usuario = config['Orpak']['user']
        passwd = config['Orpak']['passwd']

        # Insertar el usuario en el input , mediante javascript
        driver.execute_script(f"arguments[0].value = '{usuario}';", user) 

        # Buscar el input de la clave
        password = driver.find_element_by_id("Password")
    
        # Insertar la clave en el input , mediante javascript
        driver.execute_script(f"arguments[0].value = '{passwd}';", password) 

        # Click al boton login
        driver.find_element_by_id('loginbut').click()

        # Se usa un while para esperar la actualizacion de ventanas de orpack 
        # (Ahora seran 2)
        while i<=100: 

            # Variable con las ventanas de ORPACK
            popup = driver.window_handles
            
            # Se sube el valor del inidice
            i += 1

        if len(popup) == 2:

            pass

        else: 
            
            popup.pop(0)

        # Se guardan las 2 ventanas de orpack en diferentes variables
        _, document_page = popup

        # Valida que "document_page" efectivamente sea la pagina de documento
        if document_page == main_page or document_page == login_page:
    
            # Invierte la asignacion de variables
            document_page, _ = popup

    ##
        # En el proyecto de orpack a ocurrido en incontables ocasiones que las variables ventanas
        # de Orpak tienen un orden aleatorio en todos los casos
    ##

        # Cambiar a la pagina de document
        driver.switch_to.window(document_page)

        # Se cambia al frame "main"
        driver.switch_to.frame("main")

        # Click al boton de la izquierda
        driver.find_element_by_id('fho_icon').click()
        
        # En el servidor AWS. se requiere un tiempo de espera para tabs
        time.sleep(5)
        
        # Se cambia al frame "tabs"
        tabs = driver.switch_to.frame("tabs")
        
        # Click al tap opcion 2 mediante Javascript
        driver.execute_script('Tab_onclick(tab2)')
        
        # Cambiamos al contenido por defecto
        driver.switch_to.default_content()
        
        # Cambiar al frame de "main"
        driver.switch_to.frame("main")

        #WAIT TO FIEL_ORDER AVALIBLE
        try:

            # Se detiene la ejecucion hasta que el scrapping detecte que el elemento field_order1 este disponible
            # Si lo encuentra pasa inmediatamente fuera del try
            element_present = EC.presence_of_element_located((By.ID, 'field_order1'))

            # Tiempo de espera para que este dispnible
            WebDriverWait(driver, 60).until(element_present)

        except TimeoutException as e:

            # El scrapping es detenido
            driver.quit()

            # Guardo la linea donde se cayo
            line_error, name_error, d_name_error = 'Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e

            try:

                #Guardamos el error en un PJK, Si exte existe, lo actualiza, Si no existe, gatilla el try para crearlo
                run_log_error(line_error, name_error, d_name_error,False)

            except Exception as e:

                # Guardamos el error en un pkl que no existe, se crea desde 0
                run_log_error(line_error, name_error, d_name_error,True)

            # Cierro el navegador Internet Explorer
            os.system("TASKKILL /F /IM iexplore.exe") # -> Esto cierra IE    

        finally:
                
            # Si lo encuentra, hace click al boto de 'field_order1' que limpia el formulario
            driver.find_element_by_id("field_order1").click()

        #WAIT FOR FIELD_ORDER AVALIBLE
        
        # Busca el elemento 'rows_in_page'
        rows_page = driver.find_element_by_id('rows_in_page')

        # Inserta un valor maximo mediante javascript '10000'
        driver.execute_script("arguments[0].value = '10000';", rows_page) 

        # Llama la funcion select_columns, que recibe el drive
        fallido = select_columns(driver)

        # Valida si la funcion 'select_columns()' funciono correctamente
        while fallido : 

            # Vuelve a limpiar el formulario
            driver.find_element_by_id("field_order1").click()
            
            # Llama la funcion select_columns, que recibe el drive , si es True, vuelve a ejecutar el while
            fallido = select_columns(driver)

        # La ejecucion descansa 1 segundo
        time.sleep(1)

        # Busca el campo para ordenar 
        sort_by = Select(driver.find_element_by_id('sortBy'))

        # Busca la opcion con 'Fecha y hora'
        sort_by.select_by_visible_text('Fecha y hora')

        # Funcion que retorna el dia de hoy
        t_numero_semana, t_dia, t_mes = current_week()
        
        # Funcion que retorna el dia de ayer
        y_numero_semana, y_dia, y_mes = current_week(True)

        ## FECHA HOY
        ## NO INVERTIR EL ORDEN, EL CODIGO FUNCIONA EN BASE A QUE LA PRIMERA FECHA A USAR SEA LA MAYOR Y LA SIGUENTE LA MENOR
        try:

            # Abre el calendario 'hasta' de la pagina web        
            Abierto = document_week(driver, "date_end_img", t_numero_semana, t_dia, t_mes, "23", "59") #RECIBE EL DRIVER , FECHA INICIO , ELEMENT (NUMERO SEMANA ) Y BUSCA EL PRIMER DIA DE LA SEMANA , HORA Y MINUTO

            # Valida que se haya abierto el calendario
            while Abierto == False :
                
                # Vuelve a ejecutar la funcion
                Abierto = document_week(driver, "date_end_img", t_numero_semana, t_dia, t_mes, "23", "59")

            # Abre el calendario 'desde' de la pagina web
            Abierto = document_week(driver, "date_start_img", t_numero_semana, t_dia, t_mes, "00", "00") #RECIBE EL DRIVER , FECHA INICIO , ELEMENT (NUMERO SEMANA ) Y BUSCA EL PRIMER DIA DE LA SEMANA , HORA Y MINUTO

            # Valida que se haya abierto el calendario
            while Abierto == False :
                
                # Vuelve a ejecutar la funcion
                Abierto = document_week(driver, "date_start_img", t_numero_semana, t_dia, t_mes, "00", "00")

            # Llama a la funcion create_html_document para generar un PKL con los datos obtenidos
            create_html_document(driver, popup, document_page, main_page, "Y") # <- Creo que deberia ser 'T' no 'Y'

            ## FECHA AYER , Se repiten los pasos en un 80% similar

            # Seleccionamos el frame 'tabs'
            tabs = driver.switch_to.frame("tabs")
            time.sleep(1)

            # Click al frame 'tabs' mediante javascript
            driver.execute_script('Tab_onclick(tab2)')
            time.sleep(1)

            # Cambiar al frame por defecto
            driver.switch_to.default_content()
            time.sleep(1)

            # Seleccionar iFrame 'main'
            driver.switch_to.frame("main")

            # Abrimos el calendario hasta nuevamente
            Abierto = document_week(driver, "date_end_img", y_numero_semana, y_dia, y_mes, "23", "59") #RECIBE EL DRIVER , FECHA INICIO , ELEMENT (NUMERO SEMANA ) Y BUSCA EL PRIMER DIA DE LA SEMANA , HORA Y MINUTO

            # Validar que el calendario este abierto
            while Abierto == False :
                
                # Volver a abrir el calendario
                Abierto = document_week(driver, "date_end_img", y_numero_semana, y_dia, y_mes, "23", "59")

            # Abrir calendario desde nuevamente
            Abierto = document_week(driver, "date_start_img", y_numero_semana, y_dia, y_mes, "00", "00") #RECIBE EL DRIVER , FECHA INICIO , ELEMENT (NUMERO SEMANA ) Y BUSCA EL PRIMER DIA DE LA SEMANA , HORA Y MINUTO

            s3 = Bucket()
            key = f"orpak/{fecha_hoy.year}{fecha_hoy.month}{fecha_hoy.day}{fecha_hoy.hour}{fecha_hoy.minute}{fecha_hoy.second}{fecha_hoy.microsecond}.html"
            filename = ruta_fija+f"document/filename.html"
            s3.upload(filename, key)

            # Validar que calendario este abrierto
            while Abierto == False :
                
                # Volver a abrir calendario
                Abierto = document_week(driver, "date_start_img", y_numero_semana, y_dia, y_mes, "00", "00")            

            # Se crea el documento pkl con el contenido a obtener
            create_html_document(driver, popup, document_page, main_page, "T")
        
        except Exception as e:

            # Guarda en variable la liena , el nombre y detalle del error    
            line_error, name_error, d_name_error = 'Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e

            try:

                # Ejecutar funcion 'run_log_error'
                run_log_error(line_error, name_error, d_name_error, False)

            except Exception as e:

                # Si cae dentro del try se vuelve a ejecutar 'run_log_error'
                run_log_error(line_error, name_error, d_name_error, True)

            # Se cierra el scrapping abruptamente
            driver.quit()

            # Se detiene la ejecucion del software
            sys.exit(0)

        # Finalizamos la ejecucion del scrapping correctamente
        driver.quit()

        try:

            # Cargar datos del dia anterior
            new_dataY = pd.read_pickle(ruta_fija+"document/new_dataY.pkl")
            
            # Cargar datos del dia de hoy
            new_dataT = pd.read_pickle(ruta_fija+"document/new_dataT.pkl")

            # borrar nan y realizar formato de fecha. consultar a Pamela
            new_dataY.dropna(subset=['Equipo'], inplace=True)
            new_dataY.Fecha = new_dataY.Fecha.astype('str').str.strip()
            new_dataY.Fecha = pd.to_datetime(new_dataY.Fecha, format='%d/%m/%Y')   

            # borrar nan y realizar formato de fecha. consultar a Pamela
            new_dataT.dropna(subset=['Equipo'], inplace=True)
            new_dataT.Fecha = new_dataT.Fecha.astype('str').str.strip()
            new_dataT.Fecha = pd.to_datetime(new_dataT.Fecha, format='%d/%m/%Y')     

            key = f"orpak/{fecha_ayer.year}{fecha_ayer.month}{fecha_ayer.day}{fecha_ayer.hour}{fecha_ayer.minute}{fecha_ayer.second}{fecha_ayer.microsecond}.html"
            filename = ruta_fija+f"document/filename.html"
            s3.upload(filename, key)

        except ValueError as e:

            # Si se cae , borra el archivo 'filename.html'
            os.remove(ruta_fija+"document/filename.html")

        try: #TO DELETE ORIGIN DATA

                # Borra pkl datos de hoy
                os.remove(ruta_fija+"document/new_dataT.pkl")
                
                # Borra pkl datos de ayer
                os.remove(ruta_fija+"document/new_dataY.pkl")
                
                # Borra pkl datos HTML bruto si todavia existe
                os.remove(ruta_fija+"document/filename.html")

        except FileNotFoundError:
            
            # Si se cae el try , se omite
            print("[app.run] Error borrar datos RAW")
            
        # Llamar a la funcion 'create_log'
        create_log()

    except Exception as e:

        # Cerrar el scrapping abruptamente
        driver.quit()

        # Guardar en variable la linea , nombre y detalle del error
        line_error, name_error, d_name_error = 'Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e

        try:

            # Ejecutar funcion 'run_log_error'
            run_log_error(line_error, name_error, d_name_error, False)

        except Exception as e:

            # Si se cae , volver a ejecutar la funcion 'run_log_error'
            run_log_error(line_error, name_error, d_name_error, True)

        # Messague error
        print("[app.run]Error run RPA Process")
        print("[app.run] " + line_error)
        print("[app.run] " + name_error)
        print("[app.run] " + str(d_name_error))

        # Cerramos internet explorer
        os.system("TASKKILL /F /IM iexplore.exe") # -> Esto cierra IE
    
if __name__ == '__main__':
    run()
    print("[app.run]Finish RPA Process")
