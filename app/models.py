
from enum import Enum
from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictInt,
    StringConstraints,
    model_validator,
)


Latitude = Annotated[float, Field(ge=-90, le=90)]
Longitude = Annotated[float, Field(ge=-180, le=180)]

NonEmptyString = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=100,
    ),
]


class MatchingMode(str, Enum):
    V2V = "V2V"
    V2L = "V2L"
    V2H = "V2H"
    V2G = "V2G"
    CHARGING_POINT = "CHARGING_POINT"


class ConnectorType(str, Enum):
    CCS1 = "CCS1"
    CCS2 = "CCS2"
    CHADEMO = "CHADEMO"
    TYPE2 = "TYPE2"
    TESLA_NACS = "TESLA_NACS"
    GB_T = "GB_T"


class V2VProtocol(str, Enum):
    CCS = "CCS"
    CHAdeMO = "CHAdeMO"
    PROPRIETARY = "PROPRIETARY"


class StrictModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        strict=False,
        populate_by_name=True,
        use_enum_values=False,
    )


class Location(StrictModel):
    latitude: Latitude
    longitude: Longitude


class VehicleInfo(StrictModel):
    connector_type: ConnectorType = Field(alias="connectorType")

    v2v_protocol: V2VProtocol | None = Field(
        default=None,
        alias="v2vProtocol",
        description="Transfer protocol required for V2V matching.",
    )


class MatchRequest(StrictModel):
    mode: MatchingMode

    battery_percent: StrictInt = Field(
        alias="batteryPercent",
        ge=0,
        le=100,
    )

    location: Location
    vehicle: VehicleInfo

    required_energy_kwh: float | None = Field(
        default=None,
        alias="requiredEnergyKwh",
        gt=0,
        le=200,
        description="Energy the driver needs, in kWh.",
    )

    @model_validator(mode="after")
    def validate_mode_requirements(self):
        if self.mode == MatchingMode.V2V:
            if self.vehicle.v2v_protocol is None:
                raise ValueError(
                    "vehicle.v2vProtocol is required when mode is V2V"
                )

            if self.required_energy_kwh is None:
                raise ValueError(
                    "requiredEnergyKwh is required when mode is V2V"
                )

        return self


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    service: str


class MatchResponse(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    mode: MatchingMode
    battery_percent: int = Field(alias="batteryPercent")
    status: str
    message: str
    matches: list[dict[str, object]]
