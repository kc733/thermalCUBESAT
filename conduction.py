"""Equivalent 1D conduction paths, positive interior -> exterior."""

def aluminum_wall_resistance(thickness_m, conductivity_W_mK, exposed_area_m2,
                             extra_interface_K_W=0.):
    return thickness_m/(conductivity_W_mK*exposed_area_m2) + extra_interface_K_W


def photovoltaic_resistance(effective_through_thickness_K_W,
                             extra_interface_K_W=0.):
    # An illustrative effective resistance; no lateral spreading/mount path.
    # The added interface resistance is ONLY for optional sensitivity analysis.
    return effective_through_thickness_K_W+extra_interface_K_W


def conducted_power(temp_interior_K,temp_surface_K,resistance_K_W):
    return (temp_interior_K-temp_surface_K)/resistance_K_W
