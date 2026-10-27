
from math import atan2, cos, radians, sin, sqrt

EARTH_RADIUS_KM = 6371.0
MAX_SEARCH_RADIUS_KM = 5.0


def haversine_distance(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:
    """Return straight-line distance between two coordinates in km."""

    for name, latitude in (("lat1", lat1), ("lat2", lat2)):
        if not -90 <= latitude <= 90:
            raise ValueError(f"{name} must be between -90 and 90")

    for name, longitude in (("lon1", lon1), ("lon2", lon2)):
        if not -180 <= longitude <= 180:
            raise ValueError(f"{name} must be between -180 and 180")

    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)
    delta_lat = radians(lat2 - lat1)
    delta_lon = radians(lon2 - lon1)

    a = (
        sin(delta_lat / 2) ** 2
        + cos(lat1_rad)
        * cos(lat2_rad)
        * sin(delta_lon / 2) ** 2
    )

    a = min(1.0, max(0.0, a))
    central_angle = 2 * atan2(sqrt(a), sqrt(1.0 - a))

    return EARTH_RADIUS_KM * central_angle


def is_within_search_radius(distance_km: float) -> bool:
    """Return True only when a candidate is within 5 km."""
    return 0 <= distance_km <= MAX_SEARCH_RADIUS_KM
