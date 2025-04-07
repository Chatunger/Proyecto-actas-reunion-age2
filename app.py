from flask import Flask, request, jsonify, render_template,send_from_directory
import subprocess
import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime
from oauth2 import get_gmail_service, send_email_with_attachment
import sys
import re

load_dotenv()
app = Flask(__name__)

# Configuración de rutas
SCRIPT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "generar_acta.py")
DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datos_acta.json")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")

# Configuración de OpenAI
api_key = os.getenv("OPENAI_API_KEY")
cliente = OpenAI(api_key=api_key)

# Crear directorio de salida si no existe
os.makedirs(OUTPUT_DIR, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route("/ejecutar_script", methods=["POST"])
def ejecutar_script():
    try:
        # Primero intenta obtener datos del POST
        datos = request.get_json()
        if not datos:
            # Si no hay datos en POST, carga del archivo
            with open(DATA_PATH, "r", encoding="utf-8") as f:
                datos = json.load(f)
        
        print(f"📑 JSON recibido correctamente:\n{json.dumps(datos, indent=4)}")

        # Guardar JSON en archivo para ser procesado
        with open(DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=4)

        # Ejecutar el script de generación de acta
        if os.path.exists(SCRIPT_PATH):
            result = subprocess.run(
                [sys.executable, SCRIPT_PATH, DATA_PATH],
                check=True,
                capture_output=True,
                text=True
            )
            
            # Obtener la ruta del archivo generado desde la salida del script
            acta_path = result.stdout.strip()
            
            if not os.path.exists(acta_path):
                raise FileNotFoundError(f"El archivo generado no existe en {acta_path}")
            
            # Obtener solo el nombre del archivo (sin la ruta completa)
            filename = os.path.basename(acta_path)
            
            # Enviar el acta por correo
            if send_email_with_attachment(acta_path, datos):
                print("✅ Correo enviado correctamente")
                return jsonify({
                    "status": "success", 
                    "message": "Acta generada y enviada correctamente",
                    "file_name": filename  # Cambiado de file_path a file_name
                }), 200
            else:
                return jsonify({
                    "status": "warning",
                    "message": "Acta generada pero no se pudo enviar por correo",
                    "file_name": filename  # Cambiado de file_path a file_name
                }), 200
        else:
            return jsonify({"status": "error", "message": f"El archivo {SCRIPT_PATH} no existe"}), 404
            
    except subprocess.CalledProcessError as e:
        error_msg = f"Error al ejecutar el script: {e.stderr}"
        print(error_msg)
        return jsonify({"status": "error", "message": error_msg}), 500
    except FileNotFoundError as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    

@app.route("/procesar_transcripcion", methods=["POST"])
def procesar_transcripcion():
    try:
        data = request.json
        transcript = data.get("transcript", "")
        
        if not transcript:
            return jsonify({"error": "No se proporcionó transcripción"}), 400
        
        # Extraer datos estructurados usando OpenAI
        datos_estructurados = extract_structured_data(transcript)
        
        with open(DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(datos_estructurados, f, ensure_ascii=False, indent=4)
        
        # Redirigir a la vista previa inicial
        return jsonify({
            "status": "success",
            "preview_url": "/preview_initial"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/preview_initial')
def preview_initial():
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            datos = json.load(f)
        return render_template("preview_initial.html", acta=datos)
    except Exception as e:
        return render_template("error.html", mensaje=f"Error al cargar vista previa: {str(e)}"), 500

@app.route('/vista_previa')
def vista_previa():
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            datos = json.load(f)
        return render_template("acta_preview.html", acta=datos)
    except Exception as e:
        return render_template("error.html", mensaje=f"Error al cargar vista previa: {str(e)}"), 500
@app.route('/vista_previa/data')
def vista_previa_data():
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            datos = json.load(f)
        return jsonify(datos)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/guardar_cambios', methods=['POST'])
def guardar_cambios():
    try:
        datos_actualizados = request.get_json()
        with open(DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(datos_actualizados, f, ensure_ascii=False, indent=4)
        return jsonify({"status": "success", "message": "Cambios guardados correctamente"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

def extract_structured_data(text):
    prompt = f"""Extrae la siguiente información del texto del acta y devuelve SOLO un JSON válido con esta estructura exacta:
{{
    "cliente": "string (nombre del cliente/empresa)",
    "fecha": "string (formato DD-MM-AAAA)",
    "hora": "string",
    "duracion": "string",
    "autor": "string",
    "nombre": "string (nombre del proyecto)",
    "asistentes": [
        {{
            "nombre": "string",
            "organizacion": "string",
            "estado": "string (Presente/Ausente)"
        }}
    ],
    "orden_dia": ["string"],
    "temas": [
        {{
            "titulo": "string",
            "puntos": ["string"],
            "decisiones": ["string"]
        }}
    ],
    "riesgos": [
        {{
            "titulo": "string",
            "problema": "string",
            "asociado": "string",
            "mitigaciones": ["string"]
        }}
    ],
    "comentarios": ["string"],
    "tareas": [
        {{
            "tarea": "string",
            "responsable": "string",
            "fecha": "string",
            "estado": "string"
        }}
    ],
    "pasos": ["string"]
}}

Texto del acta:
{text}
"""
    try:
        response = ask_openai(prompt)
        return json.loads(response)
    except json.JSONDecodeError as e:
        print(f"Error al decodificar JSON: {str(e)}")
        return {}
    except Exception as e:
        print(f"Error al procesar la respuesta de OpenAI: {str(e)}")
        return {}
    
    

def ask_openai(prompt):
    """Envía una solicitud a OpenAI y devuelve la respuesta limpia"""
    try:
        response = cliente.chat.completions.create(
            model="gpt-4",  
            messages=[
                {
                    "role": "system", 
                    "content": "Eres un asistente que responde EXCLUSIVAMENTE con un JSON válido que contiene los campos solicitados. No incluyas ningún texto adicional fuera del JSON."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.3 
        )
        
        # Extraer y limpiar la respuesta
        response_content = response.choices[0].message.content
        
        # Eliminar marcas de código si existen
        if response_content.startswith("```json"):
            response_content = response_content[7:-3].strip()
        elif response_content.startswith("```"):
            response_content = response_content[3:-3].strip()
            
        return response_content
    except Exception as e:
        print(f"Error en la solicitud a OpenAI: {str(e)}")
        return "{}"  # Devuelve un JSON vacío como fallback

@app.route('/download/<filename>')
def download_file(filename):
    """Endpoint para descargar archivos generados"""
    try:
        return send_from_directory(
            directory=OUTPUT_DIR,
            path=filename,
            as_attachment=True
        )
    except FileNotFoundError:
        return jsonify({
            "status": "error",
            "message": f"El archivo {filename} no fue encontrado"
        }), 404
    
    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8888, debug=True)