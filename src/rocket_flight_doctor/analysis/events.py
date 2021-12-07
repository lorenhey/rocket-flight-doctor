import numpy as np
import pandas as pd
from typing import Optional, Tuple, Dict
from ..models.flight import FlightEvent, EventType, DataProvenance

def detect_liftoff(df: pd.DataFrame, accel_col: str = 'accel_z_m_s2', alt_col: str = 'altitude_baro_m', time_col: str = 'time_s') -> Optional[FlightEvent]:
    """
    Detect liftoff event. Look for sustained acceleration > 2g or altitude > 5m.
    """
    if accel_col in df.columns and df[accel_col].notna().any():
        # Look for first time acceleration exceeds 2g (approx 20 m/s^2) for at least 3 samples
        accel_threshold = 20.0
        mask = df[accel_col] > accel_threshold
        
        # Simple rolling sum to find sustained acceleration
        sustained = mask.rolling(window=3).sum() >= 3
        if sustained.any():
            idx = sustained.idxmax()
            # The actual liftoff is likely slightly before the sustained threshold was reached
            # Backtrack to when it crossed 1.2g (approx 12 m/s^2)
            backtrack_idx = df.loc[:idx][df.loc[:idx, accel_col] < 12.0].index.max()
            if pd.isna(backtrack_idx):
                backtrack_idx = df.loc[:idx].index[0]
                
            time_val = float(df.loc[backtrack_idx, time_col])
            return FlightEvent(
                event_type=EventType.LIFTOFF,
                timestamp_s=time_val,
                provenance=DataProvenance.INFERRED,
                description="Inferred from sustained vertical acceleration.",
                source="Acceleration"
            )
            
    if alt_col in df.columns and df[alt_col].notna().any():
        # Fallback to altitude: first time it goes above 5m and stays there
        mask = df[alt_col] > 5.0
        sustained = mask.rolling(window=5).sum() >= 5
        if sustained.any():
            idx = sustained.idxmax()
            backtrack_idx = df.loc[:idx][df.loc[:idx, alt_col] < 1.0].index.max()
            if pd.isna(backtrack_idx):
                backtrack_idx = df.loc[:idx].index[0]
                
            time_val = float(df.loc[backtrack_idx, time_col])
            return FlightEvent(
                event_type=EventType.LIFTOFF,
                timestamp_s=time_val,
                provenance=DataProvenance.INFERRED,
                description="Inferred from barometric altitude crossing 5m.",
                source="Barometer"
            )
            
    return None

def detect_apogee(df: pd.DataFrame, alt_col: str = 'altitude_baro_m', time_col: str = 'time_s') -> Optional[FlightEvent]:
    """
    Detect apogee (maximum altitude).
    """
    if alt_col not in df.columns or not df[alt_col].notna().any():
        return None
        
    idx = df[alt_col].idxmax()
    time_val = float(df.loc[idx, time_col])
    
    return FlightEvent(
        event_type=EventType.APOGEE,
        timestamp_s=time_val,
        provenance=DataProvenance.INFERRED,
        description=f"Maximum measured {alt_col}.",
        source=alt_col
    )

def detect_burnout(df: pd.DataFrame, liftoff_time: float, accel_col: str = 'accel_z_m_s2', time_col: str = 'time_s') -> Optional[FlightEvent]:
    """
    Detect burnout (sharp drop in acceleration after liftoff).
    """
    if accel_col not in df.columns or not df[accel_col].notna().any():
        return None
        
    # Only look at data after liftoff + 0.2s to avoid launch transient
    post_launch_df = df[df[time_col] > liftoff_time + 0.2]
    
    if post_launch_df.empty:
        return None
        
    # Find when acceleration drops below 0 (or some small negative value due to drag)
    mask = post_launch_df[accel_col] < 0
    if mask.any():
        idx = mask.idxmax()
        time_val = float(post_launch_df.loc[idx, time_col])
        return FlightEvent(
            event_type=EventType.BURNOUT,
            timestamp_s=time_val,
            provenance=DataProvenance.INFERRED,
            description="Acceleration dropped below 0 m/s^2.",
            source="Acceleration"
        )
        
    return None
