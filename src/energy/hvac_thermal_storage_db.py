"""
PCM materials thermal database and tariff profiles for HVAC optimization.
"""

PCM_MATERIAL_CATALOG = {
    "organic_paraffin_p21": {
        "name": "Bio-based Paraffin P21",
        "melting_temp_c": 21.0,
        "latent_heat_kj_kg": 200.0,
        "density_kg_m3": 800.0,
        "lifecycle_cost_usd_kwh": 45.0
    },
    "salt_hydrate_s22": {
        "name": "Inorganic Salt Hydrate S22",
        "melting_temp_c": 22.5,
        "latent_heat_kj_kg": 185.0,
        "density_kg_m3": 1500.0,
        "lifecycle_cost_usd_kwh": 30.0
    }
}

DEFAULT_24H_TARIFF_PROFILE = [
    {"hour": h, "price_usd_per_kwh": 0.10 if h < 6 or h >= 22 else (0.35 if 14 <= h <= 19 else 0.18),
     "carbon_intensity_g_per_kwh": 180.0 if h < 6 or h >= 22 else (420.0 if 14 <= h <= 19 else 280.0)}
    for h in range(24)
]
