import sys
import os
from docxtpl import DocxTemplate
import json
import re

def main(json_path):
    try:
        # Cargar los datos
        with open(json_path, "r", encoding="utf-8") as f:
            datos = json.load(f)

        # Obtener ruta absoluta de la plantilla
        template_dir = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(template_dir, "plantilla_acta.docx")
        
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"No se encontró la plantilla en {template_path}")

        # Crear nombre de archivo seguro
        safe_cliente = re.sub(r'[^\w\s-]', '', datos.get('cliente', 'acta')).strip().replace(' ', '_')[:30]
        safe_fecha = re.sub(r'[^\w\s-]', '', datos.get('fecha', '')).strip().replace(' ', '_')[:10]
        output_filename = f"acta_{safe_cliente}_{safe_fecha}.docx"
        
        # Crear directorio de salida si no existe
        output_dir = os.path.join(template_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, output_filename)

        # Generar documento
        doc = DocxTemplate(template_path)
        doc.render(datos)
        doc.save(output_path)
        
        # Devolver la ruta completa del archivo generado
        return output_path
        
    except Exception as e:
        print(f"Error al generar acta: {str(e)}", file=sys.stderr)
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python generar_acta.py <ruta_json>", file=sys.stderr)
        sys.exit(1)
        
    json_path = sys.argv[1]
    if not os.path.exists(json_path):
        print(f"Error: Archivo JSON no encontrado en {json_path}", file=sys.stderr)
        sys.exit(1)
        
    output_path = main(json_path)
    if output_path:
        # Imprimir solo la ruta para que app.py la capture
        print(output_path)
        sys.exit(0)
    else:
        sys.exit(1)