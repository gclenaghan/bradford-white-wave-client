from datetime import datetime

from bradford_white_wave_client.models import (
    DeviceStatus,
    EnergyUsage,
    WriteResponse,
)


def test_device_status_parsing():
    data = {
        "macAddress": "00:00:00:00:00:00",
        "friendlyName": "My Water Heater",
        "serialNumber": "123456789",
        "setpointFahrenheit": 120,
        "mode": "Hybrid",
        "heatModeValue": 1,
        "applianceType": "HEAT_PUMP",
        "accessLevel": 1,
    }

    device = DeviceStatus(**data)
    assert device.mac_address == "00:00:00:00:00:00"
    assert device.friendly_name == "My Water Heater"
    assert device.setpoint_fahrenheit == 120
    assert device.mode == "Hybrid"
    assert device.heat_mode_value == 1


def test_device_status_minimal_parsing():
    # Only required fields
    data = {
        "macAddress": "AA:BB:CC:DD:EE:FF",
        "friendlyName": "Minimal Device",
        "serialNumber": "SN123",
    }
    device = DeviceStatus(**data)
    assert device.mac_address == "AA:BB:CC:DD:EE:FF"
    assert device.setpoint_fahrenheit is None


def test_energy_usage_parsing():
    data = {
        "timestamp": "2023-01-01T00:00:00",
        "total_energy": 10.5,
        "heat_pump_energy": 5.2,
        "element_energy": 5.3,
        "reported_minutes": 60,
    }

    usage = EnergyUsage(**data)
    assert usage.total_energy == 10.5
    assert usage.heat_pump_energy == 5.2
    assert isinstance(usage.timestamp, datetime)


def test_write_response_parsing():
    data = {
        "status": "success",
        "requested_temperature": 125.0,
        "actual_temperature": 125,
        "device_response": {"foo": "bar"},
    }

    response = WriteResponse(**data)
    assert response.status == "success"
    assert response.requested_temperature == 125.0
    assert response.actual_temperature == 125
    assert response.device_response == {"foo": "bar"}
