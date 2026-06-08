import os
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from sqlalchemy import select
from .database import get_db, WhatsAppConfig, WhatsAppConversation, WhatsAppMessage, Company

# Configurar logging
logger = logging.getLogger("whatsapp")
logger.setLevel(logging.INFO)

router = APIRouter()

# Clave secreta para la verificación del Webhook con Meta.
# Puede ser configurada en las variables de entorno o usar una por defecto para desarrollo.
WHATSAPP_VERIFY_TOKEN = os.environ.get("WHATSAPP_VERIFY_TOKEN", "autoerp_verify_token_2026")


@router.get("/webhook", response_class=PlainTextResponse)
async def verify_webhook(request: Request):
    """
    Endpoint requerido por Meta para validar y verificar el webhook.
    Debe responder en texto plano con el 'hub.challenge' si el token de verificación coincide.
    """
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode and token:
        if mode == "subscribe" and token == WHATSAPP_VERIFY_TOKEN:
            logger.info("Webhook verificado exitosamente por Meta.")
            return challenge
        else:
            logger.warning(f"Intento de verificación de webhook fallido. Token incorrecto: {token}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Token de verificación inválido"
            )
    
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Parámetros de verificación faltantes"
    )


@router.post("/webhook")
async def receive_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Endpoint centralizado que recibe los payloads de WhatsApp enviados por Meta (mensajes, estados, etc.).
    Al ser multitenant, identifica la compañía basándose en el 'phone_number_id' del mensaje recibido.
    """
    try:
        body_json = await request.json()
        logger.info(f"Webhook recibido: {body_json}")
    except Exception as e:
        logger.error(f"Error al decodificar JSON del webhook: {str(e)}")
        return {"status": "error", "message": "Invalid JSON"}

    # Meta envía "object": "whatsapp_business_account" en eventos de WhatsApp Business Platform
    if body_json.get("object") != "whatsapp_business_account":
        # Meta requiere retornar 200 OK ante cualquier petición a su webhook para evitar que se pause
        return {"status": "ignored", "message": "Not a WhatsApp Business Account object"}

    for entry in body_json.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            field = change.get("field")

            if field != "messages":
                continue

            metadata = value.get("metadata", {})
            phone_number_id = metadata.get("phone_number_id")

            if not phone_number_id:
                logger.warning("Falta metadata.phone_number_id en el payload de Meta.")
                continue

            # 1. Identificar la compañía a la que pertenece este número de teléfono
            config = db.scalars(
                select(WhatsAppConfig).where(WhatsAppConfig.phone_number_id == phone_number_id)
            ).first()

            if not config:
                logger.warning(f"No se encontró ninguna configuración de WhatsApp para phone_number_id: {phone_number_id}")
                # Seguimos retornando 200 OK para no alertar a Meta
                continue

            company_id = config.company_id

            # 2. Procesar Mensajes Entrantes (Inbound)
            messages = value.get("messages", [])
            contacts = value.get("contacts", [])

            for message in messages:
                customer_phone = message.get("from")
                whatsapp_message_id = message.get("id")
                msg_timestamp = message.get("timestamp")
                msg_type = message.get("type", "text")

                # Obtener el nombre de perfil de WhatsApp del contacto si está disponible
                customer_name = None
                if contacts:
                    # Buscamos el contacto que coincide con el número de teléfono
                    contact_match = next((c for c in contacts if c.get("wa_id") == customer_phone), None)
                    if contact_match:
                        customer_name = contact_match.get("profile", {}).get("name")

                # Extraer cuerpo del mensaje según tipo
                body = None
                media_url = None
                if msg_type == "text":
                    body = message.get("text", {}).get("body")
                elif msg_type == "image":
                    body = "[Imagen]"
                    # En una fase posterior, se descargará el adjunto usando el ID de multimedia de Meta
                    # y se guardará la URL de Supabase Storage.
                    media_url = message.get("image", {}).get("id")
                elif msg_type == "document":
                    body = "[Documento]"
                    media_url = message.get("document", {}).get("id")
                else:
                    body = f"[{msg_type.capitalize()}]"

                # 2.1 Crear o buscar conversación de este cliente con el taller (company_id)
                stmt = select(WhatsAppConversation).where(
                    WhatsAppConversation.company_id == company_id,
                    WhatsAppConversation.customer_phone == customer_phone
                )
                conversation = db.scalars(stmt).first()

                if not conversation:
                    conversation = WhatsAppConversation(
                        company_id=company_id,
                        customer_phone=customer_phone,
                        customer_name=customer_name or customer_phone,
                        last_message_at=datetime.utcnow()
                    )
                    db.add(conversation)
                    db.flush()  # Para obtener conversation.conversation_id
                else:
                    conversation.last_message_at = datetime.utcnow()
                    if customer_name:
                        conversation.customer_name = customer_name

                # 2.2 Evitar duplicados (Meta a veces reintenta si tardamos en responder)
                existing_msg = db.scalars(
                    select(WhatsAppMessage).where(WhatsAppMessage.whatsapp_message_id == whatsapp_message_id)
                ).first()

                if not existing_msg:
                    new_msg = WhatsAppMessage(
                        conversation_id=conversation.conversation_id,
                        whatsapp_message_id=whatsapp_message_id,
                        direction="inbound",
                        type=msg_type,
                        body=body,
                        media_url=media_url,
                        status="delivered",
                        created_at=datetime.utcnow()
                    )
                    db.add(new_msg)
                    logger.info(f"Mensaje entrante guardado. Compañía: {company_id}, De: {customer_phone}")
                    
                    # TODO: Difundir mensaje por WebSocket al panel de la compañía

            # 3. Procesar Actualizaciones de Estado de Envío (Statuses)
            statuses = value.get("statuses", [])
            for status_data in statuses:
                msg_id = status_data.get("id")
                msg_status = status_data.get("status")  # sent, delivered, read, failed

                # Buscar el mensaje por su ID de WhatsApp para actualizar su estado
                msg_to_update = db.scalars(
                    select(WhatsAppMessage).where(WhatsAppMessage.whatsapp_message_id == msg_id)
                ).first()

                if msg_to_update:
                    msg_to_update.status = msg_status
                    logger.info(f"Estado de mensaje {msg_id} actualizado a: {msg_status}")
                    
                    # TODO: Notificar cambio de estado por WebSocket

            db.commit()

    return {"status": "ok"}
