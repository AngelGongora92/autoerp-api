from pydantic import BaseModel, ConfigDict
from datetime import date, time
from typing import Optional

class EmployeeScheduleBlockBase(BaseModel):
    day_of_week: int
    start_time: time
    end_time: time

class EmployeeScheduleBlockCreate(EmployeeScheduleBlockBase):
    employee_id: int

class EmployeeScheduleBlockResponse(EmployeeScheduleBlockBase):
    model_config = ConfigDict(from_attributes=True)
    block_id: int
    employee_id: int

class ScheduleOverrideBase(BaseModel):
    override_date: date
    is_available: bool
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    reason: Optional[str] = None

class ScheduleOverrideCreate(ScheduleOverrideBase):
    employee_id: int

class ScheduleOverrideResponse(ScheduleOverrideBase):
    model_config = ConfigDict(from_attributes=True)
    override_id: int
    employee_id: int