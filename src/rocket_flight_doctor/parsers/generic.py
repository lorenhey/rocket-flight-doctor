import pandas as pd
from pathlib import Path
from .base import TelemetryParser

class GenericCSVParser(TelemetryParser):
    def can_parse(self, file_path: Path) -> bool:
        return file_path.suffix.lower() == '.csv'

    def parse(self, file_path: Path, column_mapping: dict = None, **kwargs) -> pd.DataFrame:
        df = pd.read_csv(file_path)
        df.columns = [str(c).strip() for c in df.columns]
        
        if column_mapping:
            df = df.rename(columns=column_mapping)
        else:
            # Auto-guess
            guesses = {
                "time": "time_s",
                "t(s)": "time_s",
                "time(s)": "time_s",
                "altitude": "altitude_baro_m",
                "alt": "altitude_baro_m",
                "alt(m)": "altitude_baro_m",
                "pressure": "pressure_pa",
                "accel_x": "accel_x_m_s2",
                "accel_y": "accel_y_m_s2",
                "accel_z": "accel_z_m_s2",
                "acceleration": "accel_z_m_s2",
                "temp": "temperature_k"
            }
            rename_map = {}
            for col in df.columns:
                lower_col = col.lower().replace(" ", "").replace("_", "")
                for guess_k, guess_v in guesses.items():
                    if lower_col.startswith(guess_k.replace("_", "")):
                        rename_map[col] = guess_v
                        break
            df = df.rename(columns=rename_map)
            
        return df
