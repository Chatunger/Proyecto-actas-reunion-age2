import os
import base64
import re
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# Configuración de OAuth 2.0
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def get_gmail_service():
    """Obtiene el servicio de Gmail autenticado utilizando OAuth 2.0"""
    creds = None
    
    # El archivo token.json almacena los tokens de acceso y actualización
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # Si no hay credenciales válidas disponibles, el usuario debe iniciar sesión
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Guarda las credenciales para la próxima ejecución
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    return build('gmail', 'v1', credentials=creds)

def send_email_with_attachment(filepath, context):
    try:
        # Configuración del correo
        sender_email = os.getenv("SENDER_EMAIL", "tu_email@gmail.com")
        recipient_email = os.getenv("RECIPIENT_EMAIL", sender_email)
        
        service = get_gmail_service()
        message_text = (
            f"Adjunto encontrarás el acta de reunión generada automáticamente.\n\n"
            f"Detalles:\n"
            f"Cliente: {context.get('cliente', 'No especificado')}\n"
            f"Proyecto: {context.get('nombre', 'No especificado')}\n"
            f"Fecha: {context.get('fecha', 'No especificada')}\n\n"
            f"Tareas principales:\n"
        )
        
        # Añadir tareas al cuerpo del correo
        for tarea in context.get('tareas', []):
            message_text += f"- {tarea.get('tarea', '')} (Responsable: {tarea.get('responsable', '')}, Fecha: {tarea.get('fecha', '')}\n"
        
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = f"Acta de Reunión - {context.get('cliente', '')} - {context.get('fecha', '')}"
        msg.attach(MIMEText(message_text, 'plain'))
        
        # Adjuntar el acta
        with open(filepath, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename="{os.path.basename(filepath)}"')
        msg.attach(part)
        
        # Enviar el correo
        raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        message = service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()
        
        return True
    except Exception as e:
        print(f"Error al enviar correo: {e}")
        return False