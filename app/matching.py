
from app.data import get_charging_points, get_donor_evs
from app.distance import (
    MAX_SEARCH_RADIUS_KM,
    haversine_distance,
    is_within_search_radius,
)
from app.models import MatchRequest, MatchingMode


# Demo assumptions, not hardware-verified values.
ENERGY_TRANSFER_EFFICIENCY = 0.90
MAX_RATED_CHARGER_POWER_KW = 150.0


def _driver_location(request: MatchRequest) -> tuple[float, float]:
    return (
        request.location.latitude,
        request.location.longitude,
    )


def _shared_connectors(
    driver_connectors: tuple[str, ...] | list[str],
    candidate_connectors: tuple[str, ...] | list[str],
) -> list[str]:
    return sorted(set(driver_connectors) & set(candidate_connectors))


def _calculate_deliverable_energy_kwh(donor) -> float:
    """Estimate recipient energy after reserve and demo transfer losses."""

    energy_above_reserve = (
        (donor.battery_percent - donor.minimum_reserve_percent)
        / 100.0
        * donor.battery_capacity_kwh
    )

    transferable_energy = min(
        max(0.0, energy_above_reserve),
        donor.max_shareable_energy_kwh,
    )

    return round(
        transferable_energy * ENERGY_TRANSFER_EFFICIENCY,
        3,
    )


def _v2v_score(distance_km: float, deliverable_kwh: float,
               required_kwh: float) -> float:
    """
    Score from 0 to 100:
    70% proximity + 30% energy sufficiency.

    Energy score is capped at 100% when available energy reaches
    twice the requested amount.
    """
    proximity_score = max(
        0.0,
        1.0 - distance_km / MAX_SEARCH_RADIUS_KM,
    )

    energy_score = min(
        1.0,
        deliverable_kwh / (2.0 * required_kwh),
    )

    return round(
        100.0 * (
            0.70 * proximity_score
            + 0.30 * energy_score
        ),
        2,
    )


def _charger_score(distance_km: float, power_kw: float) -> float:
    """
    Score from 0 to 100:
    70% proximity + 30% rated charging power.

    Power is normalized against a 150 kW demo reference.
    """
    proximity_score = max(
        0.0,
        1.0 - distance_km / MAX_SEARCH_RADIUS_KM,
    )

    power_score = min(
        1.0,
        power_kw / MAX_RATED_CHARGER_POWER_KW,
    )

    return round(
        100.0 * (
            0.70 * proximity_score
            + 0.30 * power_score
        ),
        2,
    )


def _match_v2v(request: MatchRequest) -> dict:
    driver_lat, driver_lon = _driver_location(request)
    required_kwh = request.required_energy_kwh

    # Pydantic validates this before matching, but keep the
    # invariant explicit for static analysis and future callers.
    if required_kwh is None:
        raise ValueError("V2V matching requires requiredEnergyKwh")

    results = []

    for donor in get_donor_evs():
        if not donor.available or not donor.willing_to_share:
            continue

        if not donor.v2v_supported:
            continue

        connectors = _shared_connectors(
            (request.vehicle.connector_type.value,),
            donor.connector_types,
        )
        if not connectors:
            continue

        protocol = request.vehicle.v2v_protocol.value
        if protocol not in donor.v2v_protocols:
            continue

        # Calculate energy only after donor eligibility checks.
        deliverable_kwh = _calculate_deliverable_energy_kwh(donor)

        # Hard eligibility constraint: insufficient energy is excluded.
        if deliverable_kwh < required_kwh:
            continue

        distance_km = haversine_distance(
            driver_lat,
            driver_lon,
            donor.latitude,
            donor.longitude,
        )

        # Hard eligibility constraint: never rank candidates beyond 5 km.
        if not is_within_search_radius(distance_km):
            continue

        score = _v2v_score(
            distance_km,
            deliverable_kwh,
            required_kwh,
        )

        results.append(
            {
                "matchId": donor.vehicle_id,
                "type": "V2V",
                "distanceKm": round(distance_km, 3),
                "score": score,
                "available": True,
                "compatibleConnectors": connectors,
                "v2vProtocol": protocol,
                "requiredEnergyKwh": required_kwh,
                "deliverableEnergyKwh": deliverable_kwh,
                "donorBatteryPercent": donor.battery_percent,
                "donorReservePercent": donor.minimum_reserve_percent,
                "reasons": [
                    "Donor is available and willing to share.",
                    "Connector and transfer protocol are compatible.",
                    "Estimated delivered energy meets the requested amount.",
                    "Donor reserve constraint is satisfied.",
                    f"Within the {MAX_SEARCH_RADIUS_KM:.1f} km search radius.",
                    "Ranked by 70% proximity and 30% energy sufficiency.",
                ],
            }
        )

    # Highest score first; deterministic tie-breakers follow.
    results.sort(
        key=lambda item: (
            -item["score"],
            item["distanceKm"],
            -item["deliverableEnergyKwh"],
            item["matchId"],
        )
    )

    return {
        "status": "matched" if results else "no_match",
        "message": (
            "Eligible V2V donors found."
            if results
            else (
                "No compatible, available V2V donor within 5 km "
                "can safely deliver the requested energy."
            )
        ),
        "matches": results,
    }


def _match_charging_points(request: MatchRequest) -> dict:
    driver_lat, driver_lon = _driver_location(request)
    results = []

    for charger in get_charging_points():
        if not charger.available or not charger.operational:
            continue

        connectors = _shared_connectors(
            (request.vehicle.connector_type.value,),
            charger.connector_types,
        )
        if not connectors:
            continue

        distance_km = haversine_distance(
            driver_lat,
            driver_lon,
            charger.latitude,
            charger.longitude,
        )

        if not is_within_search_radius(distance_km):
            continue

        score = _charger_score(distance_km, charger.power_kw)

        reasons = [
            "Charging point is available and operational.",
            "Connector is compatible with the driver's EV.",
            f"Within the {MAX_SEARCH_RADIUS_KM:.1f} km search radius.",
            "Ranked by 70% proximity and 30% rated charging power.",
        ]

        if request.required_energy_kwh is not None:
            reasons.append(
                "Requested energy recorded; charging duration is not "
                "estimated because vehicle charging curves are unavailable."
            )

        results.append(
            {
                "matchId": charger.station_id,
                "type": "CHARGING_POINT",
                "name": charger.name,
                "distanceKm": round(distance_km, 3),
                "score": score,
                "available": True,
                "operational": True,
                "compatibleConnectors": connectors,
                "powerKw": charger.power_kw,
                "requiredEnergyKwh": request.required_energy_kwh,
                "reasons": reasons,
            }
        )

    results.sort(
        key=lambda item: (
            -item["score"],
            item["distanceKm"],
            -item["powerKw"],
            item["matchId"],
        )
    )

    return {
        "status": "matched" if results else "no_match",
        "message": (
            "Eligible charging points found."
            if results
            else "No compatible, operational charging point found within 5 km."
        ),
        "matches": results,
    }


def find_matches(request: MatchRequest) -> dict:
    """Run the matching algorithm for a validated request."""

    if request.mode == MatchingMode.V2V:
        return _match_v2v(request)

    if request.mode == MatchingMode.CHARGING_POINT:
        return _match_charging_points(request)

    return {
        "status": "unsupported_mode",
        "message": (
            f"Matching mode {request.mode.value} is recognized, "
            "but its matching algorithm has not been implemented yet."
        ),
        "matches": [],
    }
