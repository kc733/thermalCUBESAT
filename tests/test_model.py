"""Physical consistency and responsiveness checks for the reduced-order model."""
from dataclasses import replace
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import pytest
from parameters import Parameters, FACE_ORDER
from radiation import earth_geometry_factors, sun_direction
from scenarios import create_scenario
from solver import solve
from thermal_balance import residuals


def test_areas_and_validity():
    p=Parameters().validate()
    al,pv,end,active=p.areas()
    assert np.isclose(al+pv,.0227)
    assert np.isclose(pv,4*.04015*.08015)
    assert np.isclose(active,4*.003018)
    assert np.isclose(end,.01)


def test_earth_geometry_symmetry_and_nadir():
    F,b=earth_geometry_factors(500,sun_direction(0))
    assert np.isclose(F['+Y'],(6371/6871)**2,atol=3e-4)
    assert F['-Y']<1e-12
    assert np.isclose(F['+X'],F['-X'],rtol=1e-9)
    assert np.isclose(F['+Z'],F['-Z'],rtol=1e-9)
    assert F['+X']>0.1
    assert b['+X']>b['-X']
    assert all(0<=b[f]<=F[f]<=1 for f in FACE_ORDER)


def test_sunlight_solution_and_energy_balance():
    p=Parameters()
    sol=solve(p,create_scenario(p,True,0))
    assert len(sol.temperatures_K)==11
    assert np.all(sol.temperatures_K>0)
    assert sol.max_residual_W<1e-6
    assert abs(sol.summary['global_residual_W'])<1e-6
    assert sol.summary['electrical_W']>0
    assert sol.summary['solar_W']>0
    assert sol.summary['albedo_W']>0
    assert np.allclose(residuals(sol.temperatures_K,p,sol.regions),0,atol=1e-6)


def test_eclipse_excludes_solar_albedo_electricity():
    p=Parameters()
    sol=solve(p,create_scenario(p,False,0))
    assert sol.summary['solar_W']==0
    assert sol.summary['albedo_W']==0
    assert sol.summary['electrical_W']==0
    assert sol.summary['earth_ir_W']>0
    assert sol.summary['internal_heat_W']==1.5
    assert abs(sol.summary['global_residual_W'])<1e-6


def test_parameter_changes_update_results():
    p=Parameters()
    base=solve(p,create_scenario(p,True))
    altered=replace(p,alpha_al=.7)
    sol2=solve(altered,create_scenario(altered,True))
    assert abs(sol2.interior_C-base.interior_C)>0.1
    higher=replace(p, internal_dissipation_W=3.0)
    sol3=solve(higher,create_scenario(higher,False))
    assert sol3.interior_C>solve(p,create_scenario(p,False)).interior_C


def test_sun_angle_updates_direct_incidence():
    p=Parameters()
    a=create_scenario(p,True,0.)
    b=create_scenario(p,True,90.)
    assert a.incidence['+X']==1
    assert a.incidence['+Y']<1e-12
    assert abs(b.incidence['+Y']-1)<1e-12
    assert b.incidence['+X']<1e-12


def test_invalid_parameters():
    with pytest.raises(ValueError):
        replace(Parameters(),pv_resistance_K_W=0).validate()
    with pytest.raises(ValueError):
        replace(Parameters(),cell_length_m=0.2).validate()


def test_more_pv_electricity_cools_exposed_panel():
    p=Parameters()
    m=solve(p,create_scenario(p,True,0.))
    q=replace(p,pv_operating_efficiency=0.0)
    n=solve(q,create_scenario(q,True,0.))
    t1=next(r['temperature_C'] for r in m.rows if r['node']=='PV +X')
    t2=next(r['temperature_C'] for r in n.rows if r['node']=='PV +X')
    assert t1<t2
