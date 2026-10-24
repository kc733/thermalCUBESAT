"""Physical parameters and geometry for the 2U CubeSat thermal model.

Values are PRELIMINARY and must not be used for qualification.
"""
from dataclasses import dataclass

SIGMA = 5.670374419e-8  # W/(m² K⁴)
FACE_ORDER = ('+X', '-X', '+Y', '-Y', '+Z', '-Z')
LATERAL_FACES = FACE_ORDER[:4]
END_FACES = FACE_ORDER[4:]


@dataclass(frozen=True)
class Parameters:
    # Geometry (m)
    width_m: float = 0.100
    length_m: float = 0.227
    cell_width_m: float = 0.04015
    cell_length_m: float = 0.08015
    cells_per_lateral_face: int = 4
    active_cell_area_m2: float = 30.18e-4

    # LEO environment (reference estimates)
    altitude_km: float = 500.0
    solar_flux_W_m2: float = 1361.0
    earth_ir_W_m2: float = 237.0
    earth_albedo: float = 0.30

    # Surface properties (illustrative; not certified)
    alpha_al: float = 0.35
    epsilon_al: float = 0.10
    alpha_pv: float = 0.90
    epsilon_pv: float = 0.85

    # Conduction and simplified panel-to-interior coupling
    aluminum_k_W_mK: float = 167.0
    aluminum_thickness_m: float = 0.002
    pv_resistance_K_W: float = 2.0  # assumed effective panel-through-thickness value
    aluminum_extra_interface_K_W: float = 0.0  # optional sensitivity, default zero
    pv_extra_interface_K_W: float = 0.0  # optional sensitivity, default zero

    # Power: actual electrical extraction from PV, and internal heat load
    pv_operating_efficiency: float = 0.29
    internal_dissipation_W: float = 1.5  # orbit-averaged nominal consumption, assumed constant

    def areas(self):
        """Exposed Al (lateral), PV envelope, end face, active PV (m²)."""
        face = self.width_m * self.length_m
        pv = self.cells_per_lateral_face * self.cell_width_m * self.cell_length_m
        al = face - pv
        end = self.width_m**2
        active = self.cells_per_lateral_face * self.active_cell_area_m2
        return al, pv, end, active

    def validate(self):
        values = (self.width_m, self.length_m, self.cell_width_m,
                  self.cell_length_m, self.aluminum_k_W_mK,
                  self.aluminum_thickness_m, self.pv_resistance_K_W)
        if any(v <= 0 for v in values):
            raise ValueError('Geometry, conductivity, thickness and PV resistance must be positive.')
        if self.cells_per_lateral_face < 1:
            raise ValueError('At least one cell per lateral face is required.')
        al, pv, end, active = self.areas()
        if min(al, pv, end, active) <= 0 or active > pv:
            raise ValueError('PV geometry is inconsistent with face and active areas.')
        for name in ('alpha_al', 'alpha_pv', 'epsilon_al', 'epsilon_pv',
                     'pv_operating_efficiency', 'earth_albedo'):
            value = getattr(self, name)
            if not 0 <= value <= 1:
                raise ValueError(f'{name} must lie in [0, 1].')
        if self.epsilon_al == 0 or self.epsilon_pv == 0:
            raise ValueError('Nonzero infrared emissivities are required.')
        if not 100 <= self.altitude_km <= 2000:
            raise ValueError('Altitude must be between 100 and 2000 km for this example model.')
        if min(self.solar_flux_W_m2, self.earth_ir_W_m2,
               self.internal_dissipation_W,
               self.aluminum_extra_interface_K_W,
               self.pv_extra_interface_K_W) < 0:
            raise ValueError('Incident fluxes, power and resistances must not be negative.')
        if self.pv_operating_efficiency*active > self.alpha_pv*pv + 1e-12:
            raise ValueError('PV electrical extraction cannot exceed absorbed direct sunlight.')
        return self
