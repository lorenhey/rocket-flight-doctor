import pandas as pd
from pathlib import Path
from .base import TelemetryParser
import numpy as np

class OpenRocketParser(TelemetryParser):
    def can_parse(self, file_path: Path) -> bool:
        if file_path.suffix.lower() != '.csv':
            return False
        
        # Read the first few lines to see if it looks like OpenRocket
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for _ in range(20):
                line = f.readline()
                if not line:
                    break
                if "OpenRocket" in line or "Time (s),Altitude (m)" in line or "# Time (s)" in line:
                    return True
        return False

    def parse(self, file_path: Path, **kwargs) -> pd.DataFrame:
        # OpenRocket CSVs often have comments starting with #.
        # But sometimes the header itself starts with #. 
        # We need to find the header row.
        header_row_index = 0
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            for i, line in enumerate(lines):
                if "Time (s)" in line and "Altitude" in line:
                    header_row_index = i
                    break
        
        # Read the CSV skipping the lines before the header
        df = pd.read_csv(file_path, skiprows=header_row_index)
        
        # Clean up column names (remove leading '#' and strip whitespace)
        df.columns = [col.lstrip('#').strip() for col in df.columns]
        
        # Map OpenRocket columns to our SimulationSchema
        mapping = {
            "Time (s)": "time_s",
            "Altitude (m)": "altitude_m",
            "Vertical velocity (m/s)": "velocity_z_m_s",
            "Vertical acceleration (m/s²)": "acceleration_z_m_s2",
            "Mach number (?)": "mach",
            "Drag force (N)": "drag_n",
            "Mass (g)": "mass_g", 
            # Or is it kg? Let's handle both.
            "Mass (kg)": "mass_kg"
        }
        
        # Apply mapping
        rename_map = {}
        for orig_col in df.columns:
            for k, v in mapping.items():
                # Allow some flexibility in names
                if k.lower() in orig_col.lower():
                    rename_map[orig_col] = v
                    break
                    
        df = df.rename(columns=rename_map)
        
        # Convert mass from g to kg if needed
        if 'mass_g' in df.columns and 'mass_kg' not in df.columns:
            df['mass_kg'] = df['mass_g'] / 1000.0
            
        # Ensure required columns exist
        if 'time_s' not in df.columns or 'altitude_m' not in df.columns:
            raise ValueError("Could not find required columns in OpenRocket CSV")
            
        return df
