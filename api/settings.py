from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from api.database import get_db, CompanySettings, User
from api.auth_deps import get_current_user
from api.schemas.settings import (
    CompanySettingsResponse,
    CompanySettingsUpdate,
    AppointmentConfigSchema
)

router = APIRouter(prefix="", tags=["Settings"])

def get_or_create_settings(db: Session) -> CompanySettings:
    settings = db.query(CompanySettings).filter(CompanySettings.id == 1).first()
    if not settings:
        settings = CompanySettings(id=1, company_name="Mi Taller")
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings

@router.get("/", response_model=CompanySettingsResponse)
def get_company_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene la configuración general de la empresa.
    """
    return get_or_create_settings(db)

@router.put("/", response_model=CompanySettingsResponse)
def update_company_settings(
    settings_data: CompanySettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Actualiza la configuración general de la empresa.
    """
    settings = get_or_create_settings(db)
    update_data = settings_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(settings, key, value)
    
    db.commit()
    db.refresh(settings)
    return settings

@router.get("/appointment-config", response_model=AppointmentConfigSchema)
def get_appointment_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene los parámetros de configuración de citas (horarios, duración y días permitidos).
    """
    settings = get_or_create_settings(db)
    return settings

@router.put("/appointment-config", response_model=AppointmentConfigSchema)
def update_appointment_config(
    config_data: AppointmentConfigSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Actualiza la configuración de agendamiento de citas de la empresa.
    """
    settings = get_or_create_settings(db)
    update_data = config_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(settings, key, value)
    
    db.commit()
    db.refresh(settings)
    return settings