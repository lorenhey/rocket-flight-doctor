import pandas as pd
import numpy as np

def generate_synthetic_flight() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Generates a synthetic telemetry dataframe and a simulation dataframe.
    This creates a scenario where the actual flight has a lower apogee than simulated,
    due to higher effective drag during the coast phase.
    """
    # Time base
    t = np.linspace(-5, 60, 650) # 10 Hz sampling
    
    # SIMULATION
    # Simplified physics for simulation
    sim_mass = 1.0 # kg
    sim_thrust = np.zeros_like(t)
    sim_thrust[(t >= 0) & (t <= 1.5)] = 50.0 # 50N for 1.5s (average)
    
    sim_g = 9.81
    sim_cd = 0.5
    sim_area = 0.002 # m^2
    rho = 1.225
    
    sim_v = np.zeros_like(t)
    sim_a = np.zeros_like(t)
    sim_h = np.zeros_like(t)
    
    for i in range(1, len(t)):
        dt = t[i] - t[i-1]
        
        # Calculate drag
        speed = sim_v[i-1]
        drag = 0.5 * rho * speed**2 * sim_cd * sim_area * np.sign(speed)
        
        # Calculate net force
        fg = sim_mass * sim_g
        f_net = sim_thrust[i-1] - fg - drag
        
        # Ground constraint
        if sim_h[i-1] <= 0 and f_net < 0:
            f_net = 0
            sim_v[i-1] = 0
            
        sim_a[i] = f_net / sim_mass
        sim_v[i] = sim_v[i-1] + sim_a[i] * dt
        sim_h[i] = max(0, sim_h[i-1] + sim_v[i-1] * dt)
        
        # Deployment (parachute)
        if sim_v[i] < 0 and sim_h[i] < sim_h[i-1] and sim_cd < 1.0:
            sim_cd = 1.5 # Drogue
            sim_area = 0.1
        if sim_h[i] < 150 and sim_v[i] < 0:
            sim_cd = 1.5 # Main
            sim_area = 0.5
            
    sim_df = pd.DataFrame({
        'time_s': t,
        'altitude_m': sim_h,
        'velocity_z_m_s': sim_v,
        'acceleration_z_m_s2': sim_a,
        'mass_kg': sim_mass
    })
    
    # ACTUAL FLIGHT
    # Actual has 5% more mass and 20% more drag during coast
    act_mass = 1.0 * 1.05
    act_cd = 0.5 * 1.2
    act_area = 0.002
    
    act_v = np.zeros_like(t)
    act_a = np.zeros_like(t)
    act_h = np.zeros_like(t)
    
    # True physics
    for i in range(1, len(t)):
        dt = t[i] - t[i-1]
        speed = act_v[i-1]
        
        # Drag modifier
        current_cd = act_cd if (speed > 0 and t[i] > 1.5) else sim_cd
        if speed < 0:
            current_cd = sim_cd # Keep recovery same as sim for now
            
        drag = 0.5 * rho * speed**2 * current_cd * act_area * np.sign(speed)
        
        fg = act_mass * sim_g
        f_net = sim_thrust[i-1] - fg - drag
        
        # Ground constraint
        if act_h[i-1] <= 0 and f_net < 0:
            f_net = 0
            act_v[i-1] = 0
            
        act_a[i] = f_net / act_mass
        act_v[i] = act_v[i-1] + act_a[i] * dt
        act_h[i] = max(0, act_h[i-1] + act_v[i-1] * dt)
            
        # Deployments
        if act_v[i] < 0 and act_h[i] < act_h[i-1] and act_area < 0.1:
            act_area = 0.1 # Drogue
        if act_h[i] < 150 and act_v[i] < 0:
            act_area = 0.5 # Main
            
    # Add noise to sensors
    np.random.seed(42)
    noise_baro = np.random.normal(0, 1.5, len(t))
    noise_accel = np.random.normal(0, 2.0, len(t))
    
    # Accelerometer reading (includes 1g at rest)
    # When resting, accelerometer reads +9.81 on Z (pointing up)
    measured_a = act_a + sim_g + noise_accel
    
    # Introduce saturation during boost
    saturation_limit = 35.0 # ~3.5g
    measured_a = np.clip(measured_a, -saturation_limit, saturation_limit)
    
    measured_h = act_h + noise_baro
    
    # GPS with dropout
    gps_h = act_h + np.random.normal(0, 3.0, len(t))
    # Dropout during coast (t=5 to t=10)
    gps_h[(t > 5) & (t < 10)] = np.nan
    
    act_df = pd.DataFrame({
        'time_s': t,
        'altitude_baro_m': measured_h,
        'accel_z_m_s2': measured_a,
        'altitude_gps_m': gps_h
    })
    
    return act_df, sim_df
