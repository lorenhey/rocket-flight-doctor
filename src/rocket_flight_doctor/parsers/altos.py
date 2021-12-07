import pandas as pd
from pathlib import Path
from .base import TelemetryParser

class AltOSParser(TelemetryParser):
    def can_parse(self, file_path: Path) -> bool:
        if file_path.suffix.lower() != '.csv':
            return False
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            first_line = f.readline()
            if "version,serial,flight,call,time" in first_line.lower() or "state_name" in first_line.lower():
                return True
        return False

    def parse(self, file_path: Path, **kwargs) -> pd.DataFrame:
        df = pd.read_csv(file_path)
        
        # Clean columns
        df.columns = [col.strip().lower() for col in df.columns]
        
        # Map to TelemetrySchema
        mapping = {
            "time": "time_s",
            "pressure": "pressure_pa",
            "temperature": "temperature_k", # Check units! AltOS usually exports deg C
            "acceleration": "accel_z_m_s2", # AltOS acceleration is usually along the main axis
            "battery_voltage": "battery_v",
            "latitude": "latitude_deg",
            "longitude": "longitude_deg",
            "altitude": "altitude_gps_m", # In AltOS, 'altitude' is often GPS MSL, while 'height' is Baro AGL
            "height": "altitude_baro_m" 
        }
        
        # If 'temperature' is in C, convert to K
        if 'temperature' in df.columns:
            # We assume it's C if the mean is < 100
            if df['temperature'].mean() < 100:
                df['temperature'] = df['temperature'] + 273.15
        
        df = df.rename(columns=mapping)
        
        # Ensure we have time
        if 'time_s' not in df.columns:
            raise ValueError("AltOS CSV missing 'time' column.")
            
        return df
