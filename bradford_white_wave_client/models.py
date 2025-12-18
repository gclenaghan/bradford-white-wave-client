from datetime import datetime
from typing import Optional, Union
from pydantic import BaseModel, Field

class DeviceStatus(BaseModel):
    """Model for device status response."""
    mac_address: str = Field(..., alias="macAddress")
    friendly_name: str = Field(..., alias="friendlyName")
    serial_number: str = Field(..., alias="serialNumber")
    setpoint_fahrenheit: int = Field(..., alias="setpointFahrenheit")
    mode: Union[str, int] # Can be string ("Heat Pump") or Int depending on context, prompt said string in JSON
    heat_mode_value: int = Field(..., alias="heatModeValue")
    request_id: str = Field(..., alias="requestId")

class EnergyUsage(BaseModel):
    """Model for a single energy usage data point."""
    timestamp: datetime
    total_energy: float
    heat_pump_energy: float
    element_energy: float

class WriteResponse(BaseModel):
    """Model for write operation responses."""
    status: str
    requested_temperature: Optional[float] = None
    actual_temperature: Optional[int] = None
