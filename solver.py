"""Robust solution of the 11 nonlinear equations using nested 1D root solves.

This eliminates the 10 external temperatures for each trial interior temperature,
then solves the remaining interior energy balance. The same 11 governing
balances are verified at the final solution. The transformation does NOT
reduce the physical model or its number of thermal nodes.
"""
from dataclasses import dataclass
import numpy as np
from scipy.optimize import brentq
from thermal_balance import build_regions, external_terms, results_table, residuals
from radiation import emitted_power


@dataclass
class Solution:
    scenario: object
    temperatures_K: np.ndarray
    regions: list
    rows: list
    summary: dict
    max_residual_W: float

    @property
    def interior_C(self):
        return float(self.temperatures_K[-1]-273.15)


def solve(p,scenario):
    p.validate()
    regions=build_regions(p,scenario)
    def surface_temp(interior,region):
        terms=external_terms(p,region)
        source=(terms['solar_W']+terms['albedo_W']+terms['earth_ir_W']
                -terms['electrical_W'])
        def g(temp):
            return source+(interior-temp)/region.resistance_K_W - emitted_power(
                region.epsilon,region.area_m2,temp)
        return brentq(g,1e-6,1600.,xtol=1e-9)
    def temps_for_interior(interior):
        return np.array([surface_temp(interior,r) for r in regions],dtype=float)
    def interior_residual(interior):
        t=temps_for_interior(interior)
        out=np.sum([(interior-t[i])/r.resistance_K_W for i,r in enumerate(regions)])
        return p.internal_dissipation_W-out
    interior=brentq(interior_residual,1e-3,1400.,xtol=1e-9)
    surface=temps_for_interior(interior)
    t=np.r_[surface,interior]
    err=float(np.max(np.abs(residuals(t,p,regions))))
    if err>1e-6:
        raise RuntimeError(f'Nonconverged energy balance: {err:.3e} W')
    rows=results_table(t,p,regions)
    summary={k:sum(row[k] for row in rows) for k in
             ('solar_W','albedo_W','earth_ir_W','electrical_W','radiation_out_W')}
    summary['internal_heat_W']=p.internal_dissipation_W
    summary['global_residual_W']=(summary['solar_W']+summary['albedo_W']+
        summary['earth_ir_W']+p.internal_dissipation_W-
        summary['electrical_W']-summary['radiation_out_W'])
    return Solution(scenario,t,regions,rows,summary,err)
