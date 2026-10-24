"""External irradiation and thermal emission; no radiosity unknowns.

Earth view factors are integrated across the terrestrial angular disk. The
albedo factors assume Lambertian reflection from a uniformly albedo Earth,
with a directional solar source in the plane of the +X/+Y axes. This is an
idealized *instantaneous* illumination geometry, not a full orbital model.
"""
import numpy as np
from parameters import FACE_ORDER, SIGMA

EARTH_RADIUS_KM = 6371.0
NORMALS = {
    '+X': np.array([1., 0., 0.]), '-X': np.array([-1., 0., 0.]),
    '+Y': np.array([0., 1., 0.]), '-Y': np.array([0., -1., 0.]),
    '+Z': np.array([0., 0., 1.]), '-Z': np.array([0., 0., -1.]),
}


def sun_direction(angle_deg):
    """0° is +X toward Sun, +90° is +Y toward Sun (also nadir)."""
    a = np.deg2rad(float(angle_deg))
    return np.array([np.cos(a), np.sin(a), 0.])


def incidence_factors(sun_unit, sunlight=True):
    return {f: float(max(0., NORMALS[f]@sun_unit)) if sunlight else 0.
            for f in FACE_ORDER}


def earth_geometry_factors(altitude_km, sun_unit, polar_samples=80, azimuth_samples=240):
    """Return view F and effective albedo factor b for each face.

    F_i = (1/pi) ∫_earth max(0,n_i·ray) dΩ.
    b_i = (1/pi) ∫_earth max(0,n_i·ray)*max(0,n_Earth·sun) dΩ.

    For Lambertian Earth albedo a_E, spacecraft albedo irradiance is S*a_E*b_i.
    Earth-center direction is spacecraft +Y (nadir), satellite at -D*Y.
    Sky directions are integrated via midpoint quadrature over the disk.
    """
    if polar_samples < 8 or azimuth_samples < 16:
        raise ValueError('Insufficient integration resolution.')
    d = EARTH_RADIUS_KM+float(altitude_km)
    beta = np.arcsin(EARTH_RADIUS_KM/d)
    theta = (np.arange(polar_samples)+0.5)*beta/polar_samples
    phi = (np.arange(azimuth_samples)+0.5)*2*np.pi/azimuth_samples
    tt,pp = np.meshgrid(theta,phi,indexing='ij')
    st,ct=np.sin(tt),np.cos(tt)
    rays=np.stack([st*np.cos(pp), ct, st*np.sin(pp)],axis=-1)
    # Ray-sphere near intersection: satellite at -D*Y, Earth radius R.
    distance=d*ct-np.sqrt(np.maximum(0.,EARTH_RADIUS_KM**2-(d*st)**2))
    points=distance[...,None]*rays
    points[...,1]-=d
    normal_earth=points/EARTH_RADIUS_KM
    earth_sun_cos=np.maximum(0.,normal_earth@sun_unit)
    weights=(st*(beta/polar_samples)*(2*np.pi/azimuth_samples))/np.pi
    F={}; b={}
    for face in FACE_ORDER:
        pos=np.maximum(0.,rays@NORMALS[face]); w=pos*weights
        F[face]=float(np.sum(w))
        b[face]=float(np.sum(w*earth_sun_cos))
    return F,b


def absorbed_powers(solar_flux, earth_ir, albedo, alpha, epsilon, area,
                    incidence, albedo_factor, earth_view, extracted_electricity=0.):
    """Individual positive external inputs and outgoing PV electric power (W)."""
    return {
        'solar_W': solar_flux*alpha*area*incidence,
        'albedo_W': solar_flux*albedo*albedo_factor*alpha*area,
        'earth_ir_W': earth_ir*earth_view*epsilon*area,
        'electrical_W': extracted_electricity,
    }


def emitted_power(emissivity, area, temperature_K):
    return emissivity*SIGMA*area*temperature_K**4
