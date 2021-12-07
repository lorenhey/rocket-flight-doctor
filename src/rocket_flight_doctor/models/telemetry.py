import pandera as pa
from pandera.typing import Series, DateTime

class TelemetrySchema(pa.DataFrameModel):
    """
    Standard unified schema for flight telemetry data.
    All data is strictly in SI units.
    """
    # The master time baseline (seconds since liftoff by default)
    time_s: Series[float] = pa.Field(nullable=False)
    
    # Absolute time if known
    timestamp: Optional[Series[DateTime]] = pa.Field(nullable=True)
    
    # Barometric
    pressure_pa: Optional[Series[float]] = pa.Field(nullable=True)
    temperature_k: Optional[Series[float]] = pa.Field(nullable=True)
    
    # Derived from Barometric
    altitude_baro_m: Optional[Series[float]] = pa.Field(nullable=True)
    
    # Accelerometer (body frame)
    accel_x_m_s2: Optional[Series[float]] = pa.Field(nullable=True)
    accel_y_m_s2: Optional[Series[float]] = pa.Field(nullable=True)
    accel_z_m_s2: Optional[Series[float]] = pa.Field(nullable=True)
    
    # IMU / Gyro
    gyro_x_rad_s: Optional[Series[float]] = pa.Field(nullable=True)
    gyro_y_rad_s: Optional[Series[float]] = pa.Field(nullable=True)
    gyro_z_rad_s: Optional[Series[float]] = pa.Field(nullable=True)
    
    # GPS
    latitude_deg: Optional[Series[float]] = pa.Field(nullable=True)
    longitude_deg: Optional[Series[float]] = pa.Field(nullable=True)
    altitude_gps_m: Optional[Series[float]] = pa.Field(nullable=True)
    gps_satellites: Optional[Series[int]] = pa.Field(nullable=True)
    
    # Derived kinematics
    velocity_z_m_s: Optional[Series[float]] = pa.Field(nullable=True)
    
    # System
    battery_v: Optional[Series[float]] = pa.Field(nullable=True)
    continuity_drogue: Optional[Series[bool]] = pa.Field(nullable=True)
    continuity_main: Optional[Series[bool]] = pa.Field(nullable=True)
    
    # Metadata/Health flags per sample
    is_saturated: Optional[Series[bool]] = pa.Field(nullable=True)
    
    class Config:
        strict = False  # Allow extra columns
        coerce = True   # Attempt to cast data types

class SimulationSchema(pa.DataFrameModel):
    """
    Standard schema for simulated trajectories (e.g. OpenRocket).
    """
    time_s: Series[float] = pa.Field(nullable=False)
    altitude_m: Series[float] = pa.Field(nullable=True)
    velocity_z_m_s: Series[float] = pa.Field(nullable=True)
    acceleration_z_m_s2: Series[float] = pa.Field(nullable=True)
    mass_kg: Optional[Series[float]] = pa.Field(nullable=True)
    mach: Optional[Series[float]] = pa.Field(nullable=True)
    drag_n: Optional[Series[float]] = pa.Field(nullable=True)
    
    class Config:
        strict = False
        coerce = True
