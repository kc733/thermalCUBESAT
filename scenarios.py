"""Environment/attitude for the two steady-state thought experiments."""
from dataclasses import dataclass
from radiation import (sun_direction, incidence_factors, earth_geometry_factors)


@dataclass(frozen=True)
class Scenario:
    name: str
    incidence: dict
    albedo_factors: dict
    earth_view: dict
    sunlight: bool
    sun_angle_deg: float


def create_scenario(p, sunlight, sun_angle_deg=0., quadrature=(80,240)):
    sun = sun_direction(sun_angle_deg)
    F,b = earth_geometry_factors(p.altitude_km,sun,*quadrature)
    c = incidence_factors(sun,sunlight)
    if not sunlight:
        b={key:0. for key in b}
    return Scenario('Sunlight' if sunlight else 'Eclipse',c,b,F,
                    bool(sunlight),float(sun_angle_deg))
