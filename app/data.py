
from dataclasses import dataclass


@dataclass(frozen=True)
class SimulatedDonorEV:
    vehicle_id: str
    latitude: float
    longitude: float
    available: bool
    willing_to_share: bool
    battery_percent: int
    battery_capacity_kwh: float
    minimum_reserve_percent: int
    max_shareable_energy_kwh: float
    connector_types: tuple[str, ...]
    v2v_supported: bool
    v2v_protocols: tuple[str, ...]
    v2l_supported: bool
    v2l_power_kw: float
    v2l_can_charge_recipient_ev: bool
    v2h_supported: bool
    v2g_supported: bool


@dataclass(frozen=True)
class SimulatedChargingPoint:
    station_id: str
    name: str
    latitude: float
    longitude: float
    connector_types: tuple[str, ...]
    power_kw: float
    available: bool
    operational: bool


SIMULATED_DONOR_EVS = (
    SimulatedDonorEV(
        vehicle_id="EV-DONOR-001",
        latitude=19.0780,
        longitude=72.8790,
        available=True,
        willing_to_share=True,
        battery_percent=75,
        battery_capacity_kwh=60.0,
        minimum_reserve_percent=30,
        max_shareable_energy_kwh=15.0,
        connector_types=("CCS2",),
        v2v_supported=True,
        v2v_protocols=("CCS",),
        v2l_supported=True,
        v2l_power_kw=3.3,
        v2l_can_charge_recipient_ev=False,
        v2h_supported=False,
        v2g_supported=False,
    ),
    SimulatedDonorEV(
        vehicle_id="EV-DONOR-002",
        latitude=19.0800,
        longitude=72.8800,
        available=True,
        willing_to_share=True,
        battery_percent=65,
        battery_capacity_kwh=50.0,
        minimum_reserve_percent=25,
        max_shareable_energy_kwh=10.0,
        connector_types=("CCS2",),
        v2v_supported=True,
        v2v_protocols=("CHAdeMO",),
        v2l_supported=False,
        v2l_power_kw=0.0,
        v2l_can_charge_recipient_ev=False,
        v2h_supported=False,
        v2g_supported=False,
    ),
    SimulatedDonorEV(
        vehicle_id="EV-DONOR-003",
        latitude=19.0900,
        longitude=72.8900,
        available=False,
        willing_to_share=True,
        battery_percent=90,
        battery_capacity_kwh=70.0,
        minimum_reserve_percent=25,
        max_shareable_energy_kwh=20.0,
        connector_types=("CCS2",),
        v2v_supported=True,
        v2v_protocols=("CCS",),
        v2l_supported=True,
        v2l_power_kw=3.6,
        v2l_can_charge_recipient_ev=False,
        v2h_supported=True,
        v2g_supported=False,
    ),
    SimulatedDonorEV(
        vehicle_id="EV-DONOR-004",
        latitude=19.1050,
        longitude=72.9000,
        available=True,
        willing_to_share=True,
        battery_percent=80,
        battery_capacity_kwh=75.0,
        minimum_reserve_percent=20,
        max_shareable_energy_kwh=18.0,
        connector_types=("CCS2",),
        v2v_supported=True,
        v2v_protocols=("CCS",),
        v2l_supported=True,
        v2l_power_kw=7.0,
        v2l_can_charge_recipient_ev=True,
        v2h_supported=True,
        v2g_supported=True,
    ),
)


SIMULATED_CHARGING_POINTS = (
    SimulatedChargingPoint(
        station_id="CHARGER-001",
        name="Demo Fast Charger A",
        latitude=19.0785,
        longitude=72.8785,
        connector_types=("CCS2",),
        power_kw=60.0,
        available=True,
        operational=True,
    ),
    SimulatedChargingPoint(
        station_id="CHARGER-002",
        name="Demo AC Charger B",
        latitude=19.0820,
        longitude=72.8850,
        connector_types=("TYPE2",),
        power_kw=7.4,
        available=True,
        operational=True,
    ),
    SimulatedChargingPoint(
        station_id="CHARGER-003",
        name="Demo Fast Charger C",
        latitude=19.0850,
        longitude=72.8870,
        connector_types=("CCS2", "CHADEMO"),
        power_kw=50.0,
        available=False,
        operational=True,
    ),
    SimulatedChargingPoint(
        station_id="CHARGER-004",
        name="Demo Charger D",
        latitude=19.1000,
        longitude=72.9000,
        connector_types=("CCS2",),
        power_kw=120.0,
        available=True,
        operational=False,
    ),
)


def get_donor_evs() -> list[SimulatedDonorEV]:
    return list(SIMULATED_DONOR_EVS)


def get_charging_points() -> list[SimulatedChargingPoint]:
    return list(SIMULATED_CHARGING_POINTS)
