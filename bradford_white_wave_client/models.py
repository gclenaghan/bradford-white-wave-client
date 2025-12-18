from datetime import datetime
from typing import Optional, Union
from pydantic import BaseModel, Field

class DeviceStatus(BaseModel):
    """Model for device status response."""
    # Common fields
    mac_address: str = Field(..., alias="macAddress")
    friendly_name: str = Field(..., alias="friendlyName")
    serial_number: str = Field(..., alias="serialNumber")
    
    # Status fields (nullable since they might be missing in 'list' view)
    setpoint_fahrenheit: Optional[int] = Field(None, alias="setpointFahrenheit")
    mode: Optional[Union[str, int]] = None
    heat_mode_value: Optional[int] = Field(None, alias="heatModeValue")
    request_id: Optional[str] = Field(None, alias="requestId")
    
    # List fields
    appliance_type: Optional[str] = Field(None, alias="applianceType")
    access_level: Optional[int] = Field(None, alias="accessLevel")

class EnergyUsage(BaseModel):
    """Model for a single energy usage data point."""
    timestamp: datetime
    total_energy: float = Field(..., alias="total_energy")
    heat_pump_energy: float = Field(..., alias="heat_pump_energy")
    element_energy: float = Field(..., alias="element_energy")
    reported_minutes: Optional[int] = Field(None, alias="reported_minutes")

class WriteResponse(BaseModel):
    """Model for write operation responses."""
    status: str
    
    # Setpoint fields
    requested_temperature: Optional[float] = None
    actual_temperature: Optional[int] = None
    
    # Mode fields
    requested_mode: Optional[int] = None
    actual_mode: Optional[int] = None
    
    # Nested response
    device_response: Optional[dict] = None
