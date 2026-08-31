import pytest
from src.services.atmospheric_geo_engineering import (
    LorenzSystem, FluidDynamicsEngine, AtmosphericCell,
    ThermodynamicModel, AgriculturalImpactModel
)

def test_lorenz_chaotic_system():
    lorenz = LorenzSystem()
    lorenz.step(0.01)
    
    assert len(lorenz.history) == 1
    assert lorenz.x != 1.0 or lorenz.y != 1.0 or lorenz.z != 1.0
    
    extreme = lorenz.generate_weather_extreme()
    assert "type" in extreme
    assert "severity" in extreme

def test_fluid_dynamics_dispersion():
    fluid = FluidDynamicsEngine(grid_size=10)
    fluid.initialize_grid()
    
    fluid.inject_aerosols(0, 0, 1000.0)
    
    # Snap logic means it snaps to nearest grid lat/lon (0, 0 is exact)
    assert fluid.grid[(0, 0)].aerosol_density == 1000.0
    
    fluid.simulate_dispersion_step(1.0)
    
    # After dispersion, some aerosol should move
    assert fluid.grid[(0, 0)].aerosol_density < 1000.0
    assert fluid.grid[(0, 0)].albedo_modifier > 0.0

def test_thermodynamic_energy_conservation():
    fluid = FluidDynamicsEngine(grid_size=10)
    fluid.initialize_grid()
    thermo = ThermodynamicModel(fluid)
    
    # Inject massive aerosols to trigger albedo change
    fluid.inject_aerosols(0, 0, 10000.0)
    fluid.simulate_dispersion_step(1.0)
    
    # Baseline temp should drop over time
    initial_temp = fluid.grid[(0, 0)].temperature
    thermo.apply_thermodynamics(10.0)
    
    assert fluid.grid[(0, 0)].temperature < initial_temp

def test_agricultural_fallout():
    fluid = FluidDynamicsEngine(grid_size=10)
    fluid.initialize_grid()
    thermo = ThermodynamicModel(fluid)
    lorenz = LorenzSystem()
    
    agri = AgriculturalImpactModel(base_global_yield=100.0)
    
    # Force extreme weather and high albedo
    lorenz.x = 20.0
    fluid.inject_aerosols(0, 0, 100000.0)
    fluid.simulate_dispersion_step(1.0)
    
    agri.process_impact(thermo, lorenz)
    
    # Yield should drop
    assert agri.current_yield < 100.0
