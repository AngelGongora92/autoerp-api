import os
import httpx
import logging
import traceback

# Configuración de logging para ver qué pasa en la consola
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar variables de entorno (las que pusiste en el .env)
META_TOKEN = os.environ.get("META_TOKEN")
META_PHONE_ID = os.environ.get("META_PHONE_ID")
META_TEST_PHONE_NUMBER = os.environ.get("META_TEST_PHONE_NUMBER")

async def send_whatsapp_confirmation(phone_number: str, customer_name: str, appointment_date: str, vehicle_info: str):
    """
    Envía un mensaje de WhatsApp usando la API de Meta.
    Se ejecuta en segundo plano (Background Task).
    """
    if not META_TOKEN or not META_PHONE_ID:
        logger.warning("Faltan credenciales de Meta. No se envió el WhatsApp.")
        return

    # URL de la API de Graph (usando v22.0 como en tu curl)
    url = f"https://graph.facebook.com/v22.0/{META_PHONE_ID}/messages"
    
    headers = {
        "Authorization": f"Bearer {META_TOKEN}",
        "Content-Type": "application/json"
    }

    # --- ESTRATEGIA DEMO: Plantilla 'hello_world' ---
    # Meta requiere usar plantillas pre-aprobadas para iniciar conversación.
    
    # NOTA: En modo Sandbox, SOLO puedes enviar al número verificado (tu celular).
    # En producción, usarías 'phone_number' (el del cliente).
    recipient_phone = META_TEST_PHONE_NUMBER or phone_number

    if not recipient_phone:
        logger.warning("No hay número de teléfono de destino configurado para pruebas.")
        return

    payload = {
        "messaging_product": "whatsapp",
        "to": recipient_phone, 
        "type": "template",
        "template": {
            "name": "nueva_cita_confirmacion",
            "language": { "code": "es_MX" },
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        { "type": "text", "text": customer_name },  # {{1}} Nombre
                        { "type": "text", "text": appointment_date }, # {{2}} Fecha
                        { "type": "text", "text": vehicle_info }    # {{3}} Vehículo
                    ]
                }
            ]
        }
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            
            if response.status_code in [200, 201]:
                logger.info(f"WhatsApp enviado exitosamente a {recipient_phone}")
            else:
                logger.error(f"Error Meta API: {response.status_code} - {response.text}")
        except Exception as e:
            logger.error(f"Excepción al enviar WhatsApp: {e}")
            logger.error(traceback.format_exc())