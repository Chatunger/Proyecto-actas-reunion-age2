import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

def send_email_with_attachment(filepath, context):
    try:
        # Cargar variables de entorno
        sender_email = os.getenv("SENDER_EMAIL")
        sender_password = os.getenv("EMAIL_PASSWORD")  # Contraseña de aplicación
        recipient_email = os.getenv("RECIPIENT_EMAIL", sender_email)

        # Construir mensaje
        message_text = (
            f"Adjunto el acta de la reunión.\n\n"
            f"Cliente: {context.get('cliente', 'No especificado')}\n"
            f"Proyecto: {context.get('nombre', 'No especificado')}\n"
            f"Fecha: {context.get('fecha', 'No especificada')}\n\n"
            f"Tareas principales:\n"
        )
        for tarea in context.get('tareas', []):
            message_text += f"- {tarea.get('tarea', '')} (Responsable: {tarea.get('responsable', '')}, Fecha: {tarea.get('fecha', '')})\n"

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = f"Acta de Reunión - {context.get('cliente', '')} - {context.get('fecha', '')}"
        msg.attach(MIMEText(message_text, 'plain'))

        # Adjuntar archivo
        with open(filepath, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename="{os.path.basename(filepath)}"')
        msg.attach(part)

        # Enviar email usando SMTP seguro
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)

        return True
    except Exception as e:
        print(f"Error al enviar correo: {e}")
        return False
