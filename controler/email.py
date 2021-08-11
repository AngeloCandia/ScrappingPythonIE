#########################################################################
import smtplib as mail
import email.message
from string import Template
#########################################################################

# Recibe fecha del archivo alerta.txt
def send(ultima_fecha):
    
    # Configuracion del correo
    dictionary = {
        'to': '@',
        'another_to': '',
        'subject': '',
        'from_email': '',
        'email': '',
        'login_email': '',
        'password': '',
    }

    # Configurar correo para envio a GMAIL
    server = mail.SMTP('smtp.gmail.com',587)
    
    # Instanciar un objeto mensaje
    msg = email.message.Message()

    # Contenido del mensaje
    email_content = f"""Estimado Angelo Candia, se a detectado una anomalia
                        en la ejecucion del scrapping a partir de las 
                        {ultima_fecha} horas, considere realizar una 
                        revision
                    """

    # Asignar configuracion del correo con la del diccionario
    msg['From'] = dictionary['from_email']
    msg['To'] = dictionary['to']
    msg['ATo'] = dictionary['another_to']
    msg['Subject'] = dictionary['subject']

    # Contenido del correo
    email_content = str(email_content)
    
    # Configuracion adicional del correo
    msg.add_header('Content-Type', 'text/html')
    msg.set_payload(email_content, 'utf-8')
    
    try:
        # Envio del correo
        server.starttls()
        server.login(dictionary['login_email'], dictionary['password'])
        server.sendmail(msg['From'], msg['To'], msg.as_string())
        server.sendmail(msg['From'], msg['ATo'], msg.as_string())
        server.quit()

    except Exception as e:
        # Mensaje error
        print(f"[controller.send_email.send] Error envio de mail")