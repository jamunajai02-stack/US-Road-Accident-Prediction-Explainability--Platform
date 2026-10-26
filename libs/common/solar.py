"""Astronomical solar positioning engine and driver glare risk calculation."""

import math
from datetime import datetime, timezone
from typing import Tuple
from libs.schemas.weather import SolarMetrics


class SolarEngine:
    """Calculates solar zenith, elevation, azimuth, and direct driver glare factor."""

    @classmethod
    def calculate_solar_position(
        cls, latitude: float, longitude: float, dt: datetime
    ) -> SolarMetrics:
        """Calculate solar elevation and azimuth angles using standard NOAA solar calculations.
        
        Args:
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees
            dt: UTC datetime
            
        Returns:
            SolarMetrics schema with elevation_deg, azimuth_deg, and daylight flag
        """
        # Ensure UTC timezone
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)

        # Day of year and fractional hour
        day_of_year = dt.timetuple().tm_yday
        hour_frac = dt.hour + dt.minute / 60.0 + dt.second / 3600.0

        # Fractional year (radians)
        gamma = (2.0 * math.pi / 365.0) * (day_of_year - 1 + (hour_frac - 12.0) / 24.0)

        # Equation of time in minutes
        eq_time = 229.18 * (
            0.000075
            + 0.001868 * math.cos(gamma)
            - 0.032077 * math.sin(gamma)
            - 0.014615 * math.cos(2 * gamma)
            - 0.040849 * math.sin(2 * gamma)
        )

        # Solar declination angle (radians)
        decl = (
            0.006918
            - 0.399912 * math.cos(gamma)
            + 0.070257 * math.sin(gamma)
            - 0.006758 * math.cos(2 * gamma)
            + 0.000907 * math.sin(2 * gamma)
            - 0.002697 * math.cos(3 * gamma)
            + 0.00148 * math.sin(3 * gamma)
        )

        # True solar time in minutes
        time_offset = eq_time + 4.0 * longitude
        tst = hour_frac * 60.0 + time_offset
        true_solar_time = (tst % 1440.0)

        # Solar hour angle (degrees to radians)
        ha_deg = (true_solar_time / 4.0) - 180.0
        if ha_deg < -180.0:
            ha_deg += 360.0
        ha = math.radians(ha_deg)

        lat_rad = math.radians(latitude)

        # Solar zenith angle (radians)
        cos_zenith = math.sin(lat_rad) * math.sin(decl) + math.cos(lat_rad) * math.cos(decl) * math.cos(ha)
        cos_zenith = max(-1.0, min(1.0, cos_zenith))
        zenith_rad = math.acos(cos_zenith)
        zenith_deg = math.degrees(zenith_rad)
        elevation_deg = 90.0 - zenith_deg

        # Solar azimuth angle (degrees clockwise from North)
        if math.sin(zenith_rad) == 0.0:
            azimuth_deg = 180.0
        else:
            cos_az = (math.sin(lat_rad) * math.cos(zenith_rad) - math.sin(decl)) / (
                math.cos(lat_rad) * math.sin(zenith_rad)
            )
            cos_az = max(-1.0, min(1.0, cos_az))
            az_rad = math.acos(cos_az)
            az_deg = math.degrees(az_rad)
            if ha > 0:
                azimuth_deg = (az_deg + 180.0) % 360.0
            else:
                azimuth_deg = (540.0 - az_deg) % 360.0

        is_daylight = elevation_deg > 0.0

        # Base glare risk: high when sun is low on the horizon (5 to 25 degrees elevation)
        base_glare_risk = 0.0
        if 5.0 <= elevation_deg <= 25.0:
            # Peak glare around 12-15 degrees
            base_glare_risk = math.sin(math.radians((elevation_deg - 5.0) / 20.0 * 180.0))

        return SolarMetrics(
            elevation_deg=round(elevation_deg, 2),
            azimuth_deg=round(azimuth_deg, 2),
            is_daylight=is_daylight,
            glare_risk=round(max(0.0, min(1.0, base_glare_risk)), 3),
        )

    @classmethod
    def calculate_directional_glare_risk(
        cls, solar_elevation_deg: float, solar_azimuth_deg: float, road_bearing_deg: float
    ) -> float:
        """Calculate driver glare risk considering road orientation (sun directly in driver's line of sight).
        
        Args:
            solar_elevation_deg: Sun elevation angle (-90 to +90)
            solar_azimuth_deg: Sun azimuth angle (0 to 360)
            road_bearing_deg: Road heading direction (0 to 360)
            
        Returns:
            Calculated glare risk in [0.0, 1.0]
        """
        if solar_elevation_deg < 2.0 or solar_elevation_deg > 30.0:
            return 0.0

        # Angular difference between driver heading and sun azimuth
        heading_diff = abs((road_bearing_deg - solar_azimuth_deg + 180.0) % 360.0 - 180.0)
        
        # Sun is directly in driver's forward cone of vision (+/- 30 degrees)
        if heading_diff > 30.0:
            return 0.0

        elevation_factor = math.sin(math.radians((solar_elevation_deg - 2.0) / 28.0 * 180.0))
        alignment_factor = math.cos(math.radians(heading_diff * 3.0)) # 1.0 at 0 diff, 0.0 at 30 diff
        
        return max(0.0, min(1.0, round(elevation_factor * alignment_factor, 3)))
