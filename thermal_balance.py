"""Ten exterior balances plus one internal balance (11 temperatures total)."""
from dataclasses import dataclass
import numpy as np
from parameters import LATERAL_FACES, END_FACES
from conduction import (aluminum_wall_resistance, photovoltaic_resistance,
                        conducted_power)
from radiation import absorbed_powers, emitted_power


@dataclass(frozen=True)
class Region:
    face: str
    material: str
    area_m2: float
    alpha: float
    epsilon: float
    resistance_K_W: float
    electric_W: float
    incidence: float
    albedo_factor: float
    earth_view: float

    @property
    def label(self):
        return f'{self.material} {self.face}'


def build_regions(p,scenario):
    A_al,A_pv,A_end,A_active=p.areas()
    regions=[]
    for face in LATERAL_FACES:
        regions.append(Region(face,'Al',A_al,p.alpha_al,p.epsilon_al,
                              aluminum_wall_resistance(p.aluminum_thickness_m,
                                  p.aluminum_k_W_mK,A_al,p.aluminum_extra_interface_K_W),
                              0.,scenario.incidence[face],scenario.albedo_factors[face],
                              scenario.earth_view[face]))
        electric=(p.pv_operating_efficiency*p.solar_flux_W_m2*A_active*
                  scenario.incidence[face])
        regions.append(Region(face,'PV',A_pv,p.alpha_pv,p.epsilon_pv,
                              photovoltaic_resistance(p.pv_resistance_K_W,
                                                        p.pv_extra_interface_K_W),
                              electric,scenario.incidence[face],
                              scenario.albedo_factors[face],scenario.earth_view[face]))
    for face in END_FACES:
        regions.append(Region(face,'Al',A_end,p.alpha_al,p.epsilon_al,
                              aluminum_wall_resistance(p.aluminum_thickness_m,
                                  p.aluminum_k_W_mK,A_end,p.aluminum_extra_interface_K_W),
                              0.,scenario.incidence[face],scenario.albedo_factors[face],
                              scenario.earth_view[face]))
    assert len(regions)==10
    return regions


def external_terms(p, region):
    return absorbed_powers(p.solar_flux_W_m2,p.earth_ir_W_m2,p.earth_albedo,
                           region.alpha,region.epsilon,region.area_m2,
                           region.incidence,region.albedo_factor,region.earth_view,
                           region.electric_W)


def surface_row(p,region,surface_temp_K,interior_temp_K):
    powers=external_terms(p,region)
    cond=conducted_power(interior_temp_K,surface_temp_K,region.resistance_K_W)
    rad=emitted_power(region.epsilon,region.area_m2,surface_temp_K)
    residual=sum(powers[k] for k in ('solar_W','albedo_W','earth_ir_W'))-powers['electrical_W']+cond-rad
    return {'node':region.label,'face':region.face,'material':region.material,
            'temperature_K':float(surface_temp_K),'temperature_C':float(surface_temp_K-273.15),
            'conduction_W':float(cond),'radiation_out_W':float(rad),
            'residual_W':float(residual), 'earth_view':region.earth_view,
            'albedo_factor':region.albedo_factor,'incidence':region.incidence,
            'resistance_K_W':region.resistance_K_W,**powers}


def residuals(temperatures_K,p,regions):
    T=np.asarray(temperatures_K,dtype=float)
    if len(T)!=11:
        raise ValueError('Expected 11 temperatures: 10 surfaces and one interior.')
    rows=[surface_row(p,r,T[i],T[-1]) for i,r in enumerate(regions)]
    interior=p.internal_dissipation_W-sum(r['conduction_W'] for r in rows)
    return np.array([r['residual_W'] for r in rows]+[interior],dtype=float)


def results_table(temperatures_K,p,regions):
    return [surface_row(p,r,temperatures_K[i],temperatures_K[-1])
            for i,r in enumerate(regions)]
