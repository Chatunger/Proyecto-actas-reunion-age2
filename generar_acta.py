import sys
import os
from docxtpl import DocxTemplate, InlineImage
from docx.shared import Mm
import json
import re

def get_client_logo(cliente_name):
    """Busca el logo del cliente en la carpeta de logos"""
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    logos_dir = os.path.join(base_dir, "static", "img", "logos_clientes")
    default_logo = os.path.join(logos_dir, "no_cliente.jpg")
    
    if not os.path.exists(logos_dir):
        return default_logo
    
    # Limpiar el nombre del cliente para buscar coincidencias
    clean_name = re.sub(r'[^\w\s-]', '', cliente_name).lower().strip().replace(' ', '_')
    
    # Buscar archivos que coincidan
    for file in os.listdir(logos_dir):
        file_lower = file.lower()
        if (file_lower.startswith(clean_name) or clean_name.startswith(file_lower.split('.')[0])) and \
           file_lower.endswith(('.jpg', '.jpeg', '.png')):
            return os.path.join(logos_dir, file)
    
    return default_logo

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

        # Obtener logo del cliente
        logo_path = get_client_logo(datos.get('cliente', ''))
        
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
        context = datos.copy()
        
        # Añadir el logo 
        if os.path.exists(logo_path):
            context['logo'] = InlineImage(doc, logo_path, width=Mm(40))
        else:
            # Si no existe el logo, usar uno por defecto
            default_logo = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                     "static", "img", "logos_clientes", "no_cliente.jpg")
            context['logo'] = InlineImage(doc, default_logo, width=Mm(40))
        
        doc.render(context)
        doc.save(output_path)
        
        
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
        
        print(output_path)
        sys.exit(0)
    else:
        sys.exit(1)