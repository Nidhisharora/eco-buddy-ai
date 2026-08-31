import pytest
from src.services.global_climate_economics import (
    Commodity, SupplyChainGraph, ConsumerAgent, MarketSimulator,
    SovereignState, GlobalPolicyEngine, MonteCarloSimulator
)

def test_supply_chain_ripple_dynamics():
    graph = SupplyChainGraph()
    graph.add_commodity(Commodity("STEEL", "Steel", base_price=100.0, carbon_intensity=1.0, elasticity_of_demand=-0.5))
    graph.add_commodity(Commodity("CAR", "Car", base_price=1000.0, carbon_intensity=0.0, elasticity_of_demand=-1.0))
    graph.add_dependency("CAR", "STEEL", 5.0)
    
    # 0 Tax
    assert graph.calculate_true_price("STEEL", 0.0) == 100.0
    assert graph.calculate_true_price("CAR", 0.0) == 1500.0 # 1000 + (100 * 5)
    
    # Tax of 50 per ton
    assert graph.calculate_true_price("STEEL", 50.0) == 150.0
    assert graph.calculate_true_price("CAR", 50.0) == 1750.0 # 1000 + (150 * 5)
    
    assert graph.calculate_total_carbon_intensity("CAR") == 5.0

def test_market_price_elasticity():
    graph = SupplyChainGraph()
    graph.add_commodity(Commodity("C1", "C1", base_price=10.0, carbon_intensity=1.0, elasticity_of_demand=-1.0))
    
    market = MarketSimulator(graph)
    market.add_agent(ConsumerAgent("A1", income=100.0, preferences={"C1": 10.0})) # Prefers 10 units
    
    demand_0_tax = market.simulate_demand(0.0)
    assert demand_0_tax["C1"] == 10.0
    
    # Tax 10 -> Price doubles from 10 to 20. 
    # Price pct change = 1.0 (100%)
    # Elasticity -1.0 means demand changes by 1.0 * -1.0 = -1.0 (-100%)
    # Quantity factor = 0.0
    demand_10_tax = market.simulate_demand(10.0)
    assert demand_10_tax["C1"] == 0.0
    
def test_cbam_trade_impact():
    graph = SupplyChainGraph()
    graph.add_commodity(Commodity("STEEL", "Steel", base_price=100.0, carbon_intensity=2.0, elasticity_of_demand=-0.5))
    
    engine = GlobalPolicyEngine(graph, MarketSimulator(graph))
    engine.add_state(SovereignState("S1", "LowTax", base_gdp=1.0, carbon_tax_rate=10.0))
    engine.add_state(SovereignState("S2", "HighTax", base_gdp=1.0, carbon_tax_rate=50.0, implements_cbam=True))
    
    # S1 base price: 100 + (2 * 10) = 120
    # CBAM applied by S2: diff in tax = 40. carbon embodied = 2. tariff = 80.
    # Total effective price imported to S2 = 120 + 80 = 200
    price_imported = engine.simulate_trade_impact("S1", "S2", "STEEL")
    assert price_imported == 200.0

def test_monte_carlo_equilibrium():
    graph = SupplyChainGraph()
    graph.add_commodity(Commodity("C1", "C1", base_price=10.0, carbon_intensity=1.0, elasticity_of_demand=0.0))
    market = MarketSimulator(graph)
    market.add_agent(ConsumerAgent("A1", income=1000.0, preferences={"C1": 1.0}))
    
    engine = GlobalPolicyEngine(graph, market)
    engine.add_state(SovereignState("S1", "S1", base_gdp=1.0, carbon_tax_rate=10.0))
    
    mc = MonteCarloSimulator(engine)
    bounds = mc.run_inflation_bounds(iterations=5)
    
    assert "min_emissions" in bounds
    assert "max_emissions" in bounds
    assert bounds["max_emissions"] >= bounds["min_emissions"]
