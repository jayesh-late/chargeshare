
import pytest
from fastapi.testclient import TestClient

from app.data import get_charging_points, get_donor_evs
from app.distance import haversine_distance
from app.main import app
from app.matching import find_matches
from app.models import MatchRequest


client = TestClient(app)


def make_request(
    mode="V2V",
    battery_percent=5,
    required_energy_kwh=10,
    latitude=19.076,
    longitude=72.8777,
    connector_type="CCS2",
    protocol="CCS",
):
    vehicle = {"connectorType": connector_type}
    if protocol is not None:
        vehicle["v2vProtocol"] = protocol

    payload = {
        "mode": mode,
        "batteryPercent": battery_percent,
        "location": {
            "latitude": latitude,
            "longitude": longitude,
        },
        "vehicle": vehicle,
    }

    if required_energy_kwh is not None:
        payload["requiredEnergyKwh"] = required_energy_kwh

    return MatchRequest.model_validate(payload)


def test_v2v_returns_eligible_donors():
    result = find_matches(make_request())

    assert result["status"] == "matched"
    assert result["matches"]

    for match in result["matches"]:
        assert match["distanceKm"] <= 5
        assert match["deliverableEnergyKwh"] >= 10


def test_v2v_excludes_donors_outside_five_km():
    request = make_request(latitude=19.076, longitude=72.8777)
    result = find_matches(request)

    for match in result["matches"]:
        assert match["distanceKm"] <= 5


def test_v2v_excludes_insufficient_energy():
    result = find_matches(
        make_request(required_energy_kwh=17)
    )

    assert result["status"] == "no_match"
    assert result["matches"] == []


def test_donor_energy_respects_reserve():
    for donor in get_donor_evs():
        energy_above_reserve = max(
            0.0,
            (
                donor.battery_percent
                - donor.minimum_reserve_percent
            )
            / 100
            * donor.battery_capacity_kwh,
        )

        assert energy_above_reserve >= 0


def test_v2v_excludes_incompatible_protocol():
    result = find_matches(
        make_request(protocol="CCS")
    )

    assert all(
        match["v2vProtocol"] == "CCS"
        for match in result["matches"]
    )

    assert all(
        "EV-DONOR-002" != match["matchId"]
        for match in result["matches"]
    )


def test_v2v_excludes_unavailable_donor():
    result = find_matches(make_request())

    ids = {match["matchId"] for match in result["matches"]}

    assert "EV-DONOR-003" not in ids


def test_v2v_rejects_incompatible_connector():
    result = find_matches(
        make_request(connector_type="TYPE2")
    )

    assert result["status"] == "no_match"
    assert result["matches"] == []


def test_v2v_ranking_is_deterministic():
    request = make_request()

    first = find_matches(request)
    second = find_matches(request)

    assert first["matches"] == second["matches"]

    scores = [m["score"] for m in first["matches"]]
    assert scores == sorted(scores, reverse=True)


def test_charging_points_are_available_operational_and_compatible():
    result = find_matches(
        make_request(
            mode="CHARGING_POINT",
            required_energy_kwh=None,
            protocol=None,
        )
    )

    assert result["status"] == "matched"

    for match in result["matches"]:
        assert match["distanceKm"] <= 5
        assert match["available"] is True
        assert match["operational"] is True
        assert "CCS2" in match["compatibleConnectors"]


def test_charging_excludes_unavailable_and_non_operational_points():
    result = find_matches(
        make_request(
            mode="CHARGING_POINT",
            required_energy_kwh=None,
            protocol=None,
        )
    )

    ids = {m["matchId"] for m in result["matches"]}

    assert "CHARGER-003" not in ids
    assert "CHARGER-004" not in ids


def test_charging_rejects_incompatible_connector():
    result = find_matches(
        make_request(
            mode="CHARGING_POINT",
            required_energy_kwh=None,
            connector_type="TYPE2",
            protocol=None,
        )
    )

    assert all(
        "TYPE2" in match["compatibleConnectors"]
        for match in result["matches"]
    )


def test_charging_ranking_is_deterministic():
    request = make_request(
        mode="CHARGING_POINT",
        required_energy_kwh=None,
        protocol=None,
    )

    first = find_matches(request)
    second = find_matches(request)

    assert first["matches"] == second["matches"]

    scores = [m["score"] for m in first["matches"]]
    assert scores == sorted(scores, reverse=True)


def test_api_accepts_valid_v2v_request():
    response = client.post(
        "/match",
        json={
            "mode": "V2V",
            "batteryPercent": 5,
            "requiredEnergyKwh": 10,
            "location": {
                "latitude": 19.076,
                "longitude": 72.8777,
            },
            "vehicle": {
                "connectorType": "CCS2",
                "v2vProtocol": "CCS",
            },
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "matched"


def test_api_rejects_v2v_without_required_energy():
    response = client.post(
        "/match",
        json={
            "mode": "V2V",
            "batteryPercent": 5,
            "location": {
                "latitude": 19.076,
                "longitude": 72.8777,
            },
            "vehicle": {
                "connectorType": "CCS2",
                "v2vProtocol": "CCS",
            },
        },
    )

    assert response.status_code == 422


def test_api_rejects_invalid_battery_percentage():
    payload = {
        "mode": "V2V",
        "batteryPercent": 150,
        "requiredEnergyKwh": 10,
        "location": {
            "latitude": 19.076,
            "longitude": 72.8777,
        },
        "vehicle": {
            "connectorType": "CCS2",
            "v2vProtocol": "CCS",
        },
    }

    response = client.post("/match", json=payload)

    assert response.status_code == 422


def test_api_rejects_invalid_coordinates():
    response = client.post(
        "/match",
        json={
            "mode": "V2V",
            "batteryPercent": 5,
            "requiredEnergyKwh": 10,
            "location": {
                "latitude": 100,
                "longitude": 72.8777,
            },
            "vehicle": {
                "connectorType": "CCS2",
                "v2vProtocol": "CCS",
            },
        },
    )

    assert response.status_code == 422


def test_unsupported_mode_does_not_claim_success():
    result = find_matches(
        make_request(
            mode="V2L",
            required_energy_kwh=None,
            protocol=None,
        )
    )

    assert result["status"] == "unsupported_mode"
    assert result["matches"] == []


def test_haversine_same_location_is_zero():
    distance = haversine_distance(
        19.076,
        72.8777,
        19.076,
        72.8777,
    )

    assert distance == pytest.approx(0.0)


def test_haversine_rejects_invalid_coordinates():
    with pytest.raises(ValueError):
        haversine_distance(100, 0, 0, 0)
