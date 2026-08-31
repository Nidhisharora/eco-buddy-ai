import pytest
from src.services.bio_ecosystem_simulator import (
    Genome, Organism, BiomeCell, CellularAutomataEngine,
    DisasterPropagator, BioInterventionEngine, EcosystemVisualizer
)

def test_genetic_drift_and_mutation():
    g = Genome("G1", heat_tolerance=50.0, drought_resistance=50.0, reproduction_rate=0.5, mutation_rate=0.1)
    
    # Mutate
    g_mut = g.mutate()
    assert g_mut.id == "G1_mut"
    # Might be same if random is exact 0, but generally different or within bounds
    assert 0.0 <= g_mut.heat_tolerance <= 100.0
    assert 0.0 <= g_mut.drought_resistance <= 100.0

def test_cellular_automata_survival():
    g = Genome("G1", heat_tolerance=20.0, drought_resistance=80.0, reproduction_rate=0.9, mutation_rate=0.1)
    org = Organism("TestSpecies", g)
    
    # Temp 30 > 20 (heat tolerance), Humidity 10 < 20 (threshold 100-80=20)
    # Total stress = 10*2 + 10*2 = 40. Health becomes 60. Survives.
    survives = org.evaluate_survival(30.0, 10.0)
    assert survives is True
    assert org.health < 100.0
    
    # Extreme conditions -> death
    survives2 = org.evaluate_survival(100.0, 0.0)
    assert survives2 is False

def test_disaster_propagation_fire():
    ca = CellularAutomataEngine(size=3)
    ca.initialize_grid(30.0, 50.0)
    
    disaster = DisasterPropagator(ca)
    disaster.trigger_forest_fire(1, 1)
    assert ca.grid[(1, 1)].is_burning is True
    
    # Propagate with wind pushing right (dx=1, dy=0)
    disaster.simulate_fire_propagation(1.0, 0.0)
    
    # Original cell loses fuel
    assert ca.grid[(1, 1)].fire_fuel < 100.0
    # Center cell temp spikes
    assert ca.grid[(1, 1)].temperature > 30.0

def test_bio_intervention():
    ca = CellularAutomataEngine(size=3)
    ca.initialize_grid(30.0, 20.0) # Low humidity
    
    bio = BioInterventionEngine(ca)
    # Deploy drought resistant flora
    bio.deploy_drought_resistant_flora()
    
    assert ca.grid[(0, 0)].flora_biomass > 100.0 # Started at 100
    
    # Introduce species
    g = Genome("G1", 50.0, 50.0, 0.5, 0.1)
    bio.introduce_engineered_species("Fox", g, 5, 1, 1)
    assert len(ca.grid[(1, 1)].fauna) == 5

def test_pathogen_spread():
    ca = CellularAutomataEngine(size=3)
    ca.initialize_grid(30.0, 80.0) # High humidity
    
    ca.grid[(1, 1)].pathogen_level = 50.0
    disaster = DisasterPropagator(ca)
    
    disaster.simulate_pathogen_spread()
    
    # Pathogen spreads to neighbor (0,0)
    assert ca.grid[(0, 0)].pathogen_level > 0.0
    # Flora in epicenter drops
    assert ca.grid[(1, 1)].flora_biomass < 100.0
