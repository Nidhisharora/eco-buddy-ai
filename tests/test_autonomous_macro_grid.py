import pytest
from src.services.autonomous_macro_grid import (
    SmartMeter, SolarInverter, BatteryManagementSystem,
    LSTMPredictor, MathUtils,
    GridNode, ACGridFlow,
    ElectricVehicle, V2GSwarmOrchestrator
)

def test_hardware_in_the_loop_mocking():
    bms = BatteryManagementSystem("B1", 100.0, 50.0, 10.0, 10.0)
    charged = bms.charge(20.0, 1.0) # 20 kWh attempted, max rate 10 kW for 1 hr = 10 kWh
    assert charged == 10.0
    assert bms.current_charge_kwh == 60.0
    
    discharged = bms.discharge(15.0, 2.0) # 15 kWh attempted, max rate 10 kW for 2 hr = 20 max possible. Actual = 15.
    assert discharged == 15.0
    assert bms.current_charge_kwh == 45.0

def test_lstm_forward_and_backprop():
    lstm = LSTMPredictor(input_size=2, hidden_size=4)
    seq = [[0.1, 0.2], [0.3, 0.4]]
    
    initial_pred = lstm.predict(seq)
    
    # Train step
    target = 1.0
    loss1 = lstm.train_step(seq, target, lr=0.1)
    
    # Second step should have lower loss
    loss2 = lstm.train_step(seq, target, lr=0.1)
    assert loss2 < loss1

def test_ac_power_flow_frequency():
    grid = ACGridFlow()
    n1 = GridNode("N1", p_gen=100.0, p_demand=50.0) # 50 Surplus
    n2 = GridNode("N2", p_gen=0.0, p_demand=100.0)  # 100 Deficit
    grid.add_node(n1)
    grid.add_node(n2)
    grid.add_line("N1", "N2", 0.01, 0.1)
    
    # Net deficit = 50. Frequency should drop below 60.0
    freq = grid.update_frequency()
    assert freq < 60.0
    
    # Mismatch calc (will be high because voltage angles are all 0 right now)
    mismatch = grid.calculate_power_mismatch()
    assert mismatch > 0.0

def test_v2g_swarm_logic():
    # Grid needs power
    bms1 = BatteryManagementSystem("B1", 100.0, 90.0, 10.0, 10.0)
    ev1 = ElectricVehicle("EV1", bms1, owner_target_charge=50.0) # 40 kWh surplus
    
    bms2 = BatteryManagementSystem("B2", 100.0, 40.0, 10.0, 10.0)
    ev2 = ElectricVehicle("EV2", bms2, owner_target_charge=50.0) # Deficit, shouldn't discharge
    
    swarm = V2GSwarmOrchestrator([ev1, ev2])
    
    # Grid needs 5 kW for 1 hour = 5 kWh
    impact = swarm.balance_grid(5.0, 1.0)
    
    assert impact == 5.0
    assert ev1.bms.current_charge_kwh == 85.0 # Supplied 5 kWh
    assert ev2.bms.current_charge_kwh == 40.0 # Unchanged
    
    # Grid has surplus power
    impact_surplus = swarm.balance_grid(-5.0, 1.0)
    assert impact_surplus == -5.0
    # EV2 will charge because it has lowest charge
    assert ev2.bms.current_charge_kwh == 45.0
