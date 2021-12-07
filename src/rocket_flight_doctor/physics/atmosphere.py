import numpy as np

# US Standard Atmosphere 1976 constants (Troposphere)
R_STAR = 8.31432 # J/(mol·K)
G0 = 9.80665 # m/s^2
M_AIR = 0.0289644 # kg/mol
L_B = -0.0065 # K/m
T0 = 288.15 # K
P0 = 101325.0 # Pa

def pressure_to_altitude(pressure_pa: np.ndarray, p_ref: float = P0, t_ref: float = T0) -> np.ndarray:
    """
    Convert pressure to altitude using the US Standard Atmosphere formula.
    By default, if p_ref is sea level pressure, returns MSL altitude.
    If p_ref is the launch site pressure, returns AGL altitude.
    
    Args:
        pressure_pa: Array of pressures in Pascals.
        p_ref: Reference pressure in Pascals (e.g. pressure at launch pad for AGL).
        t_ref: Reference temperature in Kelvin.
        
    Returns:
        Array of altitudes in meters relative to the reference.
    """
    # Prevent division by zero or negative powers if sensor glitches to 0 or negative
    pressure_pa = np.maximum(pressure_pa, 1e-5)
    
    exponent = -(R_STAR * L_B) / (G0 * M_AIR)
    # altitude = (t_ref / L_B) * ((pressure_pa / p_ref) ** exponent - 1)
    
    # Actually the standard derivation is:
    # P = P_ref * (1 + (L_b * h) / T_ref) ** (-g0 * M / (R * L_b))
    # h = (T_ref / L_b) * ((P / P_ref) ** (-R * L_b / (g0 * M)) - 1)
    
    altitude = (t_ref / L_B) * ((pressure_pa / p_ref) ** exponent - 1.0)
    return altitude

def altitude_to_pressure(altitude_m: np.ndarray, p_ref: float = P0, t_ref: float = T0) -> np.ndarray:
    """
    Convert altitude to expected pressure.
    """
    exponent = -(G0 * M_AIR) / (R_STAR * L_B)
    pressure = p_ref * (1.0 + (L_B * altitude_m) / t_ref) ** exponent
    return pressure

def calculate_mach_number(velocity_m_s: np.ndarray, temperature_k: float = T0) -> np.ndarray:
    """
    Calculate Mach number given velocity and ambient temperature.
    Gamma for dry air ~ 1.4
    """
    gamma = 1.4
    speed_of_sound = np.sqrt(gamma * (R_STAR / M_AIR) * temperature_k)
    return np.abs(velocity_m_s) / speed_of_sound
