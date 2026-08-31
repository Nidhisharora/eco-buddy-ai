import pytest
from src.services.ccs_subterranean_simulator import (
    IndustrialHub, InjectionSite, PipelineNetwork,
    GeologicalCell, DarcysLawSimulator, SeismicRiskModel, MineralizationEngine
)

def test_pipeline_network_mst_and_flow():
    hubs = [IndustrialHub("H1", 0.0, 0.0, 500.0), IndustrialHub("H2", 10.0, 10.0, 300.0)]
    sites = [InjectionSite("S1", 5.0, 5.0, 1000.0)]
    
    network = PipelineNetwork(hubs, sites)
    mst = network.optimize_network_mst()
    # 3 nodes total -> 2 edges in MST
    assert len(mst) == 2
    
    flow = network.calculate_max_flow()
    # Total hub output is 800, site capacity is 1000, so flow should be 800
    assert flow == 800.0
    assert sites[0].current_injection_rate == 800.0

def test_darcys_law_permeation_accuracy():
    sim = DarcysLawSimulator((3, 3, 3))
    sim.initialize_aquifer(2.0e7)
    
    # Inject CO2 at the center
    center = (1, 1, 1)
    sim.inject_co2(center, rate=100.0, time_step=1.0)
    assert sim.grid[center].co2_saturation > 0.0
    
    # Step simulation to propagate flow
    initial_sat = sim.grid[center].co2_saturation
    sim.simulate_flow_step(time_step=1.0)
    
    # CO2 should move to neighbors, so center saturation decreases
    assert sim.grid[center].co2_saturation < initial_sat
    # Neighbor should have some CO2
    assert sim.grid[(2, 1, 1)].co2_saturation > 0.0

def test_seismic_risk_model():
    sim = DarcysLawSimulator((3, 3, 3))
    sim.initialize_aquifer(2.0e7)  # Base pressure 20 MPa
    
    # Force a massive pressure spike at top layer
    sim.grid[(1, 1, 0)].pressure = 5.0e7  # 50 MPa
    
    risk_model = SeismicRiskModel(caprock_tensile_strength=1.5e7)
    risks = risk_model.evaluate_risk(sim)
    
    assert len(risks) > 0
    assert risks[0]["location"] == (1, 1, 0)
    assert risks[0]["risk_level"] == "CRITICAL"
    
def test_chemical_mineralization():
    sim = DarcysLawSimulator((2, 2, 2))
    sim.initialize_aquifer(2.0e7)
    
    loc = (0, 0, 0)
    sim.grid[loc].co2_saturation = 0.5
    sim.grid[loc].porosity = 0.2
    
    engine = MineralizationEngine(dissolution_rate=0.1, reaction_rate=0.1)
    minerals = engine.process_time_step(sim, years=10.0)
    
    assert minerals > 0.0
    assert sim.grid[loc].co2_saturation < 0.5
    assert sim.grid[loc].porosity < 0.2
