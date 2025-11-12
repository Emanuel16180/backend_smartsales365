# apps/reports/parser.py

import os
import re
import json
import logging
from datetime import datetime
from django.conf import settings
import google.generativeai as genai

# Configura el logger
logger = logging.getLogger(__name__)

# Configura la API de Gemini
try:
    GOOGLE_API_KEY = os.getenv('GEMINI_API_KEY')
    if not GOOGLE_API_KEY:
        GOOGLE_API_KEY = getattr(settings, "GEMINI_API_KEY", None)
        
    if GOOGLE_API_KEY:
        genai.configure(api_key=GOOGLE_API_KEY)
    else:
        logger.error("No se encontró la GEMINI_API_KEY en el entorno.")
        
except Exception as e:
    logger.error(f"Error al configurar la API de Gemini: {e}")

# --- PROMPT MAESTRO (Sin cambios) ---
PROMPT_MAESTRO = """
Eres un asistente experto en análisis de datos para un E-Commerce. Tu trabajo es
convertir un prompt de lenguaje natural en un objeto JSON ESTRUCTURADO que
servirá para filtrar una base de datos de ventas.

El JSON de salida DEBE seguir este esquema. Solo puedes usar las claves
definidas a continuación. Si un valor no es mencionado en el prompt, OMITE la clave.

ESQUEMA JSON PERMITIDO:
{
  "report_type": "pdf" | "csv" | "excel",
  "client_search": "texto de búsqueda de cliente",
  "product_search": "texto de búsqueda de producto",
  "status": "COMPLETED" | "PENDING" | "FAILED",
  "fecha_inicio": "YYYY-MM-DD",
  "fecha_fin": "YYYY-MM-DD",
  "month": "1-12",
  "year": "YYYY"
}

REGLAS ESTRICTAS:
1.  **Formato de Salida:** Responde SIEMPRE Y ÚNICAMENTE con el objeto JSON. NADA MÁS.
2.  **Omisión:** Si el usuario no menciona un filtro, NO incluyas esa clave en el JSON.
3.  **Fechas:** Convierte todas las fechas al formato YYYY-MM-DD.
4.  **Meses:** Convierte meses (ej. "septiembre") al número de mes ("9"). Si no se menciona un año para el mes, asume el año actual.
5.  **Ambigüedad de Fechas:** Si el usuario dice "del 10 al 15 de noviembre", asume que ambas fechas son de noviembre.
6.  **Palabras Clave:**
    * "cliente", "comprador", "usuario" -> `client_search`
    * "producto", "artículo", "item" -> `product_search`
    * "reporte", "archivo" -> `report_type` (pdf, csv, excel)
7.  **Valores por defecto:** Si no se pide un formato, usa "pdf" como `report_type`.

Ejemplos:
Prompt: "Quiero un reporte en pdf del cliente Ana Gomez"
Respuesta:
{
  "report_type": "pdf",
  "client_search": "Ana Gomez"
}

Prompt: "reporte de ventas del mes de septiembre, en excel"
Respuesta:
{
  "report_type": "excel",
  "month": 9,
  "year": 2025
}

Prompt: "dame las ventas de lavadoras del 01/10/2024 al 01/01/2025"
Respuesta:
{
  "report_type": "pdf",
  "product_search": "lavadoras",
  "fecha_inicio": "2024-10-01",
  "fecha_fin": "2025-01-01"
}

Prompt: "ventas completadas del producto Samsung"
Respuesta:
{
  "report_type": "pdf",
  "status": "COMPLETED",
  "product_search": "Samsung"
}
"""

def parse_prompt_to_filters(prompt_text: str) -> dict:
    """
    Toma un prompt de lenguaje natural y usa un LLM (Gemini)
    para convertirlo en un diccionario de parámetros de filtro.
    """
    if not GOOGLE_API_KEY:
        raise ValueError("GEMINI_API_KEY no está configurada.")
    
    try:
        # --- (INICIO DE LA CORRECCIÓN) ---
        
        # 1. Usamos el modelo estándar con su RUTA COMPLETA
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # --- (FIN DE LA CORRECCIÓN) ---
        
        prompt_con_contexto = PROMPT_MAESTRO.replace(
            "asume el año actual",
            f"asume el año actual ({datetime.now().year})"
        )
        
        full_prompt = f"{prompt_con_contexto}\n\nPrompt: \"{prompt_text}\"\nRespuesta:\n"
        
        response = model.generate_content(full_prompt)
        
        json_text = re.search(r'```(json)?(.*)```', response.text, re.DOTALL)
        if json_text:
            cleaned_response = json_text.group(2).strip()
        else:
            cleaned_response = response.text.strip()
            
        logger.warning(f"Respuesta JSON del LLM: {cleaned_response}")
        
        params = json.loads(cleaned_response)
        
        return params

    except Exception as e:
        logger.error(f"Error en la API de Gemini o parseando JSON: {e}")
        return {"error": str(e)}