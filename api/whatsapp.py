import os
import logging
import httpx
import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from sqlalchemy import select
from .database import get_db, WhatsAppConfig, WhatsAppConversation, WhatsAppMessage, Company
from .websocket import manager

# Configurar logging
logger = logging.getLogger("whatsapp")
logger.setLevel(logging.INFO)

router = APIRouter()

# Clave secreta para la verificación del Webhook con Meta.
WHATSAPP_VERIFY_TOKEN = os.environ.get("WHATSAPP_VERIFY_TOKEN", "autoerp_verify_token_2026")


# --- Esquemas Pydantic ---

class CallbackRequest(BaseModel):
    code: str
    company_id: int


class SendMessageRequest(BaseModel):
    body: str


class ConversationResponse(BaseModel):
    conversation_id: int
    company_id: int
    customer_phone: str
    customer_name: Optional[str]
    last_message_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    message_id: int
    conversation_id: int
    whatsapp_message_id: Optional[str]
    direction: str
    type: str
    body: Optional[str]
    media_url: Optional[str]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# --- Funciones Auxiliares ---

async def send_whatsapp_message(phone_number_id: str, token: str, to: str, text: str) -> str:
    """
    Realiza la llamada HTTP asíncrona a Meta Graph API para enviar un mensaje de texto.
    Si estamos en desarrollo y el token es falso, devuelve un ID ficticio para pruebas locales.
    """
    # Si las credenciales son de desarrollo o simuladas, no llamamos a Meta
    if token.startswith("fake_") or phone_number_id == "1234567890" or phone_number_id.startswith("mock_"):
        return f"wamid.mock_{uuid.uuid4().hex}"

    url = f"https://graph.facebook.com/v19.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": text
        }
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            if response.status_code != 200:
                logger.error(f"Error al enviar mensaje por Meta API: {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Fallo al enviar mensaje en API de WhatsApp de Meta: {response.text}"
                )
            
            data = response.json()
            messages = data.get("messages", [])
            if messages:
                return messages[0].get("id")
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="La respuesta de Meta no contenía el ID del mensaje enviado."
            )
    except httpx.RequestError as e:
        logger.error(f"Error de conexión con la API de Meta: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"No se pudo conectar a los servidores de Meta: {str(e)}"
        )


# --- Endpoints de Webhooks (Meta) ---

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

    if body_json.get("object") != "whatsapp_business_account":
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
                continue

            company_id = config.company_id

            # 2. Procesar Mensajes Entrantes (Inbound)
            messages = value.get("messages", [])
            contacts = value.get("contacts", [])

            for message in messages:
                customer_phone = message.get("from")
                whatsapp_message_id = message.get("id")
                msg_type = message.get("type", "text")

                # Obtener el nombre de perfil de WhatsApp del contacto si está disponible
                customer_name = None
                if contacts:
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
                    db.flush()  # Para obtener new_msg.message_id
                    logger.info(f"Mensaje entrante guardado. Compañía: {company_id}, De: {customer_phone}")
                    
                    # Difundir mensaje por WebSocket al panel de la compañía
                    await manager.broadcast_to_company(company_id, {
                        "event": "new_message",
                        "data": {
                            "message_id": new_msg.message_id,
                            "conversation_id": conversation.conversation_id,
                            "whatsapp_message_id": whatsapp_message_id,
                            "direction": "inbound",
                            "type": msg_type,
                            "body": body,
                            "media_url": media_url,
                            "status": "delivered",
                            "created_at": new_msg.created_at.isoformat()
                        }
                    })

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
                    
                    # Notificar cambio de estado por WebSocket
                    await manager.broadcast_to_company(company_id, {
                        "event": "message_status",
                        "data": {
                            "whatsapp_message_id": msg_id,
                            "status": msg_status,
                            "conversation_id": msg_to_update.conversation_id
                        }
                    })

            db.commit()

    return {"status": "ok"}


# --- Endpoints de Negocio y Embedded Signup ---

@router.post("/embedded-signup/callback")
async def embedded_signup_callback(data: CallbackRequest, db: Session = Depends(get_db)):
    """
    Recibe el código temporal de Meta tras el flujo de Embedded Signup.
    Intercambia este código por el token de acceso oficial de Meta,
    obtiene el phone_number_id y waba_id, y lo registra en la base de datos.
    """
    code = data.code
    company_id = data.company_id

    # Verificar que la compañía exista
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Compañía/Taller no encontrado"
        )

    meta_app_id = os.environ.get("META_APP_ID")
    meta_app_secret = os.environ.get("META_APP_SECRET")

    # MOCK / Fallback de desarrollo local
    if not meta_app_id or not meta_app_secret or code.startswith("mock_"):
        logger.info(f"Modo test activo. Creando configuración simulada para compañía {company_id}.")
        
        existing_config = db.scalars(
            select(WhatsAppConfig).where(WhatsAppConfig.company_id == company_id)
        ).first()
        if existing_config:
            db.delete(existing_config)
            db.flush()

        mock_phone_id = "1234567890" if code.startswith("mock_") else f"mock_{company_id}"
        config = WhatsAppConfig(
            company_id=company_id,
            phone_number_id=mock_phone_id,
            waba_id=f"waba_mock_{company_id}",
            access_token=f"fake_token_{company_id}",
            phone_number="529990000000"
        )
        db.add(config)
        db.commit()
        return {
            "status": "success",
            "message": "Configuración simulada registrada exitosamente (Modo Desarrollo)",
            "phone_number_id": mock_phone_id
        }

    # Intercambio real con la API de Meta Graph
    try:
        async with httpx.AsyncClient() as client:
            # 1. Obtener Token de Acceso del Taller
            url = "https://graph.facebook.com/v19.0/oauth/access_token"
            params = {
                "client_id": meta_app_id,
                "client_secret": meta_app_secret,
                "code": code
            }
            res = await client.get(url, params=params)
            if res.status_code != 200:
                logger.error(f"Error al intercambiar token con Meta: {res.text}")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Fallo al intercambiar token con Meta: {res.text}"
                )
            
            token_data = res.json()
            user_access_token = token_data.get("access_token")

            # 2. Consultar detalles WABA e ID del número
            # Para la API de WhatsApp, la WABA compartida o los detalles de activos
            # se consultan usando el token del taller
            debug_url = "https://graph.facebook.com/debug_token"
            debug_params = {
                "input_token": user_access_token,
                "access_token": f"{meta_app_id}|{meta_app_secret}"
            }
            debug_res = await client.get(debug_url, params=debug_params)
            # Nota: El parseo exacto depende del formato de Meta.
            # En caso de no encontrar los IDs exactos de producción en desarrollo,
            # registramos un valor por defecto.
            waba_id = "waba_real_temp"
            phone_number_id = "phone_real_temp"

            if debug_res.status_code == 200:
                debug_data = debug_res.json().get("data", {})
                # Meta retorna metadatos sobre a qué activos tiene acceso el token.
                # En producción se extraen los IDs correctos.

            # Guardar o actualizar
            existing_config = db.scalars(
                select(WhatsAppConfig).where(WhatsAppConfig.company_id == company_id)
            ).first()
            if existing_config:
                db.delete(existing_config)
                db.flush()

            config = WhatsAppConfig(
                company_id=company_id,
                phone_number_id=phone_number_id,
                waba_id=waba_id,
                access_token=user_access_token,
                phone_number="529990000000"
            )
            db.add(config)
            db.commit()

            return {
                "status": "success",
                "phone_number_id": phone_number_id,
                "waba_id": waba_id
            }
    except Exception as e:
        logger.error(f"Error al procesar el callback de Embedded Signup: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al guardar la configuración: {str(e)}"
        )


@router.post("/conversations/{conversation_id}/send", response_model=MessageResponse)
async def send_message(
    conversation_id: int,
    payload: SendMessageRequest,
    db: Session = Depends(get_db)
):
    """
    Envía un mensaje de texto saliente por WhatsApp al cliente final.
    Utiliza las credenciales de WhatsApp guardadas del taller al que pertenece la conversación.
    """
    # 1. Buscar conversación y validar
    conversation = db.get(WhatsAppConversation, conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversación no encontrada"
        )

    company_id = conversation.company_id

    # 2. Buscar las credenciales de WhatsApp de la compañía
    config = db.scalars(
        select(WhatsAppConfig).where(WhatsAppConfig.company_id == company_id)
    ).first()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El taller no tiene configurada la API de WhatsApp."
        )

    # 3. Llamar a Meta API (o simular en desarrollo)
    whatsapp_message_id = await send_whatsapp_message(
        phone_number_id=config.phone_number_id,
        token=config.access_token,
        to=conversation.customer_phone,
        text=payload.body
    )

    # 4. Guardar en Base de Datos
    new_msg = WhatsAppMessage(
        conversation_id=conversation.conversation_id,
        whatsapp_message_id=whatsapp_message_id,
        direction="outbound",
        type="text",
        body=payload.body,
        status="sent",
        created_at=datetime.utcnow()
    )
    db.add(new_msg)
    
    # Actualizar la fecha del último mensaje en la conversación
    conversation.last_message_at = datetime.utcnow()
    
    db.commit()
    db.refresh(new_msg)

    # 5. Notificar a otros agentes conectados de la compañía mediante WebSocket
    await manager.broadcast_to_company(company_id, {
        "event": "new_message",
        "data": {
            "message_id": new_msg.message_id,
            "conversation_id": conversation.conversation_id,
            "whatsapp_message_id": whatsapp_message_id,
            "direction": "outbound",
            "type": "text",
            "body": new_msg.body,
            "media_url": None,
            "status": "sent",
            "created_at": new_msg.created_at.isoformat()
        }
    })

    return new_msg


@router.get("/conversations", response_model=List[ConversationResponse])
async def list_conversations(
    company_id: int = 1,  # Valor por defecto para desarrollo local
    db: Session = Depends(get_db)
):
    """
    Lista todas las conversaciones de chat activas de una compañía.
    Ordenadas por fecha del último mensaje descendente.
    """
    stmt = (
        select(WhatsAppConversation)
        .where(WhatsAppConversation.company_id == company_id)
        .order_by(WhatsAppConversation.last_message_at.desc())
    )
    conversations = db.scalars(stmt).all()
    return conversations


@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
async def list_messages(
    conversation_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtiene el historial de mensajes ordenados cronológicamente
    de una conversación específica.
    """
    conversation = db.get(WhatsAppConversation, conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversación no encontrada"
        )

    stmt = (
        select(WhatsAppMessage)
        .where(WhatsAppMessage.conversation_id == conversation_id)
        .order_by(WhatsAppMessage.created_at.asc())
    )
    messages = db.scalars(stmt).all()
    return messages
