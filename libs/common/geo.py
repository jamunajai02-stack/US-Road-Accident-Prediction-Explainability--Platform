"""Geospatial utilities including H3 cell indexing, Haversine distances, and bearing calculations."""

import math
from typing import List, Tuple

try:
    import h3
except ImportError:
    h3 = None


class GeoUtils:
    """Geodesic calculation and H3 spatial grid helpers with pure-Python fallback."""

    @classmethod
    def lat_lng_to_h3(cls, latitude: float, longitude: float, resolution: int = 8) -> str:
        """Convert latitude and longitude to H3 hexadecimal string index."""
        if h3 is not None:
            if hasattr(h3, "latlng_to_cell"):
                return h3.latlng_to_cell(latitude, longitude, resolution)
            elif hasattr(h3, "geo_to_h3"):
                return h3.geo_to_h3(latitude, longitude, resolution)
        
        # Pure Python fallback: deterministic spatial hex bin string
        # Resolution 8 ~460m (0.005 deg lat/lon)
        step = 0.005 * (2 ** (8 - resolution))
        lat_bin = int(math.floor((latitude + 90.0) / step))
        lon_bin = int(math.floor((longitude + 180.0) / step))
        # Format as 15-char hexadecimal representation
        return f"88{resolution:01x}{lat_bin:06x}{lon_bin:06x}"

    @classmethod
    def h3_to_lat_lng(cls, h3_cell: str) -> Tuple[float, float]:
        """Convert H3 cell index back to centroid (latitude, longitude)."""
        if h3 is not None:
            if hasattr(h3, "cell_to_latlng"):
                return h3.cell_to_latlng(h3_cell)
            elif hasattr(h3, "h3_to_geo"):
                return h3.h3_to_geo(h3_cell)

        # Pure Python fallback decoding
        if h3_cell.startswith("88") and len(h3_cell) >= 15:
            try:
                res = int(h3_cell[2:3], 16)
                lat_bin = int(h3_cell[3:9], 16)
                lon_bin = int(h3_cell[9:15], 16)
                step = 0.005 * (2 ** (8 - res))
                lat = (lat_bin * step) - 90.0 + (step / 2.0)
                lon = (lon_bin * step) - 180.0 + (step / 2.0)
                return (round(lat, 6), round(lon, 6))
            except Exception:
                pass
        return (0.0, 0.0)

    @classmethod
    def haversine_distance_meters(
        cls, lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        """Calculate great-circle distance between two points in meters."""
        r = 6371000.0  # Earth radius in meters
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = (
            math.sin(delta_phi / 2.0) ** 2
            + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
        )
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return r * c

    @classmethod
    def calculate_bearing(
        cls, lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        """Calculate compass bearing (0-360 degrees) from point 1 to point 2."""
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        diff_long = math.radians(lon2 - lon1)

        x = math.sin(diff_long) * math.cos(lat2_rad)
        y = math.cos(lat1_rad) * math.sin(lat2_rad) - (
            math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(diff_long)
        )

        initial_bearing = math.atan2(x, y)
        compass_bearing = (math.degrees(initial_bearing) + 360.0) % 360.0
        return round(compass_bearing, 2)

    @classmethod
    def calculate_sinuosity(
        cls, coordinates: List[Tuple[float, float]]
    ) -> Tuple[float, float]:
        """Calculate arc length, straight line chord length, and sinuosity ratio.
        
        Args:
            coordinates: Ordered list of (latitude, longitude) tuples along the road segment
            
        Returns:
            Tuple of (total_arc_length_meters, sinuosity_ratio)
        """
        if len(coordinates) < 2:
            return (0.0, 1.0)

        total_arc_length = 0.0
        for i in range(len(coordinates) - 1):
            p1 = coordinates[i]
            p2 = coordinates[i + 1]
            total_arc_length += cls.haversine_distance_meters(p1[0], p1[1], p2[0], p2[1])

        start_pt = coordinates[0]
        end_pt = coordinates[-1]
        chord_length = cls.haversine_distance_meters(start_pt[0], start_pt[1], end_pt[0], end_pt[1])

        if chord_length <= 0.1:
            sinuosity = 1.0
        else:
            sinuosity = max(1.0, round(total_arc_length / chord_length, 3))

        return (round(total_arc_length, 2), sinuosity)

    @classmethod
    def calculate_turning_angle_variance(
        cls, coordinates: List[Tuple[float, float]]
    ) -> float:
        """Calculate variance of turning angles along a road geometry segment (curvature proxy)."""
        if len(coordinates) < 3:
            return 0.0

        bearings = []
        for i in range(len(coordinates) - 1):
            p1 = coordinates[i]
            p2 = coordinates[i + 1]
            bearings.append(cls.calculate_bearing(p1[0], p1[1], p2[0], p2[1]))

        turning_angles = []
        for i in range(len(bearings) - 1):
            b1 = bearings[i]
            b2 = bearings[i + 1]
            diff = abs((b2 - b1 + 180.0) % 360.0 - 180.0)
            turning_angles.append(diff)

        if not turning_angles:
            return 0.0

        mean_turn = sum(turning_angles) / len(turning_angles)
        variance = sum((t - mean_turn) ** 2 for t in turning_angles) / len(turning_angles)
        return round(variance, 3)
