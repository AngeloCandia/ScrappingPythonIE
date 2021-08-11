#########################################################################
import os
import time
import datetime
from pytz import timezone
import warnings
warnings.filterwarnings('ignore')
#########################################################################
import pandas as pd
#########################################################################

# 'alerta.txt': archivo que contiene la hora ultima que se ejecuto el scrapping
# 'log_error.pkl': archivo que contiene todos los errores que a gatillado el scrapping

    
############################## TIME LOG ERROR ##############################
def read_log(): #se usa
    # Abre archivo alerta.txt
    f = open("document/Alerts/alerta.txt", "r")
    
    # Lee contenido del archivo
    mensaje = f.read()
    
    # Genera la fecha actual, para luego guardarlo en el archivo "alerta.txt"
    nuevo_mensaje = datetime.datetime.strptime(mensaje, "%Y-%m-%d %H:%M:%S")
    
    # Cierra el archivo "alerta.txt"
    f.close()
    
    # Retorna la fecha que sera guardado en "alerta.txt"
    return nuevo_mensaje

# Funcion para crear el archivo 'alerta.txt'
def create_log():
    
    # Obtener fecha actual
    current_date = datetime.datetime.now(timezone("America/Santiago"))
    
    # Abre o crea un archivo txt
    f = open("document/Alerts/alerta.txt", "w")
    
    # Variable con la fecha de hoy
    alerta = current_date.strftime("%Y-%m-%d %H:%M:%S")

    # Se escribe en el archivo la fecha registrada anteriormente
    f.write(alerta)    
    
    # Se cierra el archivo txt
    f.close()

# Funcion que borra el archivo 'alerta.txt'
def del_log_error():
    # Borra el archivo alerta.txt , esto ocurre cuando se envia un correo de scrapping anomalia
    os.remove("document/Alerts/alerta.txt")
    
    # Vuelve a crear el archivo
    create_log()
        
############################### LOG ERROR #################################

# Funcion que crea el log de errores
def create_log_error(): 
    # Retorna DataFrame vacio
    return pd.DataFrame()

# Funcion que guarda los cambios de log error
def save_log_error(frame):  
    try:
        # Los ordena por fecha de mayor a manor    
        frame.sort_values(by=['Fecha'], inplace=True, ascending=False )
        
        # Sobreescribe el pkl anterior
        frame.to_pickle("document/Alerts/log_error.pkl")
    
    except Exception as e:
        # Mensaje si se cae, actualmente nunca a ocurrido
        print(e)

# Funcion que lee el log de errores
def read_log_error():
    # Lee el archivo pkl
    frame = pd.read_pickle("document/Alerts/log_error.pkl")
    
    # Lo retorna
    return frame

# Funcion que recibe la linea de error, el nombre, detalle y si el archivo existe o no
def run_log_error(line_error, name_error, d_name_error, Nuevo=True):
    
    try:
        # Obtiene la fecha actual
        current_date = datetime.datetime.now()
        
        # Valida si el archivo existe o no            
        if Nuevo:
            # Si es nuevo lo crea
            frame = create_log_error()

        else: 
            # Si ya existe , lo lee
            frame = read_log_error()

        # Guarda el nuevo error en el archivo 'log_error.pkl'
        frame = frame.append(pd.DataFrame([[current_date, str(line_error), str(name_error), str(d_name_error)]], columns=["Fecha", "Linea error", "Error", "Texto"]))

        # Valida nuevamente si es nuevo o no
        if Nuevo:
            # Si el archivo es nuevo, pasa
            pass

        else :
            # Resetea los index 
            frame.reset_index(inplace=True, drop=True)
            
            # Ordenar los errores por fecha
            frame.sort_values(by=["Fecha"], inplace=True, ascending=False)

            # Calcula la diferencia de minutos entre el error actual con el anterior
            frame["Diferencia minutos"] = frame["Fecha"].diff(-1).dt.total_seconds() / 60

        # Llamo al metodo save_log_error para guardar los cambios
        save_log_error(frame)

    except Exception as e:
        # Si se cae la funcion, el scrapping continua su flujo
        print("[controller.alert.run_log_error] Error en la funcion")