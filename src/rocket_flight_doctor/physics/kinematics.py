import numpy as np
from scipy.signal import savgol_filter

def derive_velocity(time_s: np.ndarray, altitude_m: np.ndarray, window_length: int = 11, polyorder: int = 2) -> np.ndarray:
    """
    Derive velocity from altitude using Savitzky-Golay filter to compute the derivative while smoothing.
    
    Args:
        time_s: Array of timestamps in seconds.
        altitude_m: Array of altitudes in meters.
        window_length: Length of the filter window. Must be odd.
        polyorder: Order of the polynomial used to fit the samples.
        
    Returns:
        Array of velocities in m/s.
    """
    if len(time_s) < window_length:
        # Not enough points, fallback to simple finite difference
        dt = np.gradient(time_s)
        dt = np.where(dt == 0, 1e-6, dt) # Prevent division by zero
        return np.gradient(altitude_m, dt)

    # Assuming roughly uniform sampling for savgol_filter. 
    # If strongly non-uniform, this needs interpolation first.
    dt_mean = np.mean(np.gradient(time_s))
    
    # savgol_filter with deriv=1 computes the first derivative of the polynomial
    # We must divide by delta according to scipy docs if delta != 1
    velocity = savgol_filter(altitude_m, window_length=window_length, polyorder=polyorder, deriv=1, delta=dt_mean)
    return velocity

def derive_acceleration(time_s: np.ndarray, velocity_m_s: np.ndarray, window_length: int = 11, polyorder: int = 2) -> np.ndarray:
    """
    Derive acceleration from velocity using Savitzky-Golay filter.
    """
    if len(time_s) < window_length:
        dt = np.gradient(time_s)
        dt = np.where(dt == 0, 1e-6, dt)
        return np.gradient(velocity_m_s, dt)
        
    dt_mean = np.mean(np.gradient(time_s))
    acceleration = savgol_filter(velocity_m_s, window_length=window_length, polyorder=polyorder, deriv=1, delta=dt_mean)
    return acceleration

def smooth_series(data: np.ndarray, window_length: int = 11, polyorder: int = 2) -> np.ndarray:
    """
    Apply Savitzky-Golay smoothing to a data series.
    """
    if len(data) < window_length:
        return data
    return savgol_filter(data, window_length=window_length, polyorder=polyorder)
