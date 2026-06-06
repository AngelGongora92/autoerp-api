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

async def send_whatsapp_confirmation(phone_number: str, customer_name: str, appointment_date: str, vehicle_info: str, appointment_id: int):
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
                },
                {
                    "type": "button",
                    "sub_type": "url",
                    "index": 0,
                    "parameters": [
                        {
                            "type": "text",
                            "text": str(appointment_id) # {{1}} ID de la cita para el parámetro de la URL
                        }
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

async def send_email_confirmation_brevo(email: str, customer_name: str, appointment_date: str, vehicle_info: str, appointment_id: int):
    """
    Envía un correo de confirmación de cita usando la API SMTP de Brevo.
    Se ejecuta en segundo plano (Background Task).
    """
    BREVO_API_KEY = os.environ.get("BREVO_API_KEY")
    BREVO_SENDER_EMAIL = os.environ.get("BREVO_SENDER_EMAIL")
    BREVO_SENDER_NAME = os.environ.get("BREVO_SENDER_NAME", "Auto ERP")

    if not BREVO_API_KEY or not BREVO_SENDER_EMAIL:
        logger.warning("Faltan credenciales de Brevo. No se envió el correo de confirmación.")
        return

    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "content-type": "application/json"
    }

    # Plantilla HTML adaptada al estilo estético del sistema
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            color: #1a1c25;
            background-color: #f8f9fa;
            margin: 0;
            padding: 0;
        }}
        .container {{
            max-width: 600px;
            margin: 40px auto;
            background: #ffffff;
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
            border: 1px solid #e2e8f0;
        }}
        .header {{
            background-color: #003ec7;
            padding: 32px;
            text-align: center;
            color: #ffffff;
        }}
        .header h1 {{
            margin: 0;
            font-size: 24px;
            font-weight: 700;
            letter-spacing: -0.5px;
        }}
        .content {{
            padding: 32px;
        }}
        .content p {{
            font-size: 16px;
            line-height: 1.6;
            margin-top: 0;
            margin-bottom: 24px;
        }}
        .details-card {{
            background-color: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 32px;
        }}
        .detail-row {{
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px dashed #e2e8f0;
        }}
        .detail-row:last-child {{
            border-bottom: none;
            padding-bottom: 0;
        }}
        .detail-row:first-child {{
            padding-top: 0;
        }}
        .detail-label {{
            font-weight: 600;
            color: #64748b;
            font-size: 14px;
        }}
        .detail-value {{
            font-weight: 700;
            color: #0f172a;
            font-size: 14px;
            text-align: right;
        }}
        .button-container {{
            text-align: center;
            margin-bottom: 16px;
        }}
        .btn {{
            display: inline-block;
            background-color: #003ec7;
            color: #ffffff !important;
            text-decoration: none;
            padding: 14px 28px;
            border-radius: 8px;
            font-weight: 600;
            font-size: 16px;
        }}
        .footer {{
            background-color: #f1f5f9;
            padding: 24px;
            text-align: center;
            font-size: 12px;
            color: #64748b;
            border-top: 1px solid #e2e8f0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{BREVO_SENDER_NAME}</h1>
        </div>
        <div class="content">
            <p>Hola <strong>{customer_name}</strong>,</p>
            <p>Tu cita de servicio ha sido registrada exitosamente en nuestro sistema. A continuación encontrarás los detalles de tu cita:</p>
            
            <div class="details-card">
                <div class="detail-row">
                    <span class="detail-label">Fecha y Hora</span>
                    <span class="detail-value">{appointment_date}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Vehículo</span>
                    <span class="detail-value">{vehicle_info}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Estado</span>
                    <span class="detail-value" style="color: #ea580c;">Sin confirmar</span>
                </div>
            </div>
            
            <div class="button-container">
                <a href="http://localhost:5173/?confirm_appointment={appointment_id}" class="btn">Ver Detalles de Cita</a>
            </div>
            <p style="font-size: 14px; color: #64748b; text-align: center; margin-top: 16px;">
                Si necesitas realizar algún cambio o tienes dudas, por favor contáctanos directamente respondiendo a este correo.
            </p>
        </div>
        <div class="footer">
            <p>Este es un correo automático enviado por <strong>Auto ERP</strong>.<br>&copy; 2026 {BREVO_SENDER_NAME}. Todos los derechos reservados.</p>
        </div>
    </div>
</body>
</html>"""

    payload = {
        "sender": {
            "name": BREVO_SENDER_NAME,
            "email": BREVO_SENDER_EMAIL
        },
        "to": [
            {
                "email": email,
                "name": customer_name
            }
        ],
        "subject": f"Confirmación de Cita - {BREVO_SENDER_NAME}",
        "htmlContent": html_content
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            if response.status_code in [200, 201, 202]:
                logger.info(f"Correo de confirmación enviado exitosamente a {email} vía Brevo")
            else:
                logger.error(f"Error Brevo API: {response.status_code} - {response.text}")
        except Exception as e:
            logger.error(f"Excepción al enviar correo vía Brevo: {e}")
            logger.error(traceback.format_exc())