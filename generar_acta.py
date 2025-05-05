import sys
import os
from docxtpl import DocxTemplate, InlineImage
from docx.shared import Mm
import json
import re

def get_client_logo(cliente_name):
    """Busca el logo del cliente en la carpeta de logos (sin crear imágenes por defecto)"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    logos_dir = os.path.join(base_dir, "static", "img", "logos_clientes")
    default_logo = os.path.join(logos_dir, "no_cliente.jpg")

    # Verificar si existe el directorio de logos
    if not os.path.exists(logos_dir):
        return None

    # Limpiar nombre para búsqueda
    clean_name = re.sub(r'[^\w\s-]', '', cliente_name).lower().strip().replace(' ', '_')

    # Buscar coincidencia de logo
    for file in os.listdir(logos_dir):
        file_lower = file.lower()
        if (file_lower.startswith(clean_name) or clean_name.startswith(file_lower.split('.')[0])) and \
           file_lower.endswith(('.jpg', '.jpeg', '.png')):
            return os.path.join(logos_dir, file)

    # Usar logo por defecto solo si existe
    return default_logo if os.path.exists(default_logo) else None

def asegurar_estructura_contexto(context):
    """Garantiza que todos los campos tengan la estructura correcta"""
    campos_str = ["cliente", "fecha", "hora", "duracion", "autor", "nombre"]
    campos_lista = ["asistentes", "orden_dia", "temas", "riesgos", "comentarios", "tareas", "pasos"]

    # Campos string
    for campo in campos_str:
        if campo not in context or not isinstance(context[campo], str):
            context[campo] = ""

    # Campos lista
    for campo in campos_lista:
        if campo not in context or not isinstance(context[campo], list):
            context[campo] = []

    # Asistentes
    for asistente in context["asistentes"]:
        asistente.setdefault("nombre", "")
        asistente.setdefault("organizacion", "")
        asistente.setdefault("estado", "")

    # Tareas
    for tarea in context["tareas"]:
        tarea.setdefault("tarea", "")
        tarea.setdefault("responsable", "")
        tarea.setdefault("fecha", "")
        tarea.setdefault("estado", "")

    # Temas
    for tema in context["temas"]:
        tema.setdefault("titulo", "")
        tema.setdefault("puntos", [])
        tema.setdefault("decisiones", [])

    # Riesgos
    for riesgo in context["riesgos"]:
        riesgo.setdefault("titulo", "")
        riesgo.setdefault("problema", "")
        riesgo.setdefault("asociado", "")
        riesgo.setdefault("mitigaciones", [])

    return context

def main(json_path):
    try:
        # Cargar datos JSON
        with open(json_path, "r", encoding="utf-8") as f:
            datos = json.load(f)

        # Ruta de la plantilla
        template_dir = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(template_dir, "plantilla_acta.docx")

        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Plantilla no encontrada en {template_path}")

        # Generar nombre de archivo seguro
        safe_cliente = re.sub(r'[^\w\s-]', '', datos.get('cliente', 'acta')).strip().replace(' ', '_')[:30]
        safe_fecha = re.sub(r'[^\w\s-]', '', datos.get('fecha', '')).strip().replace(' ', '_')[:10]
        output_filename = f"acta_{safe_cliente}_{safe_fecha}.docx"

        # Directorio de salida
        output_dir = os.path.join(template_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, output_filename)

        # Preparar contexto
        doc = DocxTemplate(template_path)
        context = asegurar_estructura_contexto(datos.copy())

        # Manejo seguro del logo
        logo_path = get_client_logo(context.get('cliente', ''))
        context['logo'] = None  # Valor por defecto

        if logo_path and os.path.exists(logo_path):
            try:
                context['logo'] = InlineImage(doc, logo_path, width=Mm(40))
            except Exception as img_error:
                print(f"Advertencia: Error al cargar logo - {img_error}")

        # Renderizar y guardar
        doc.render(context)
        doc.save(output_path)

        print(output_path)  # Necesario para capturar la ruta en app.py
        return output_path

    except json.JSONDecodeError as e:
        print(f"Error: Archivo JSON inválido - {str(e)}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Error crítico: {str(e)}", file=sys.stderr)
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
    sys.exit(0 if output_path else 1)