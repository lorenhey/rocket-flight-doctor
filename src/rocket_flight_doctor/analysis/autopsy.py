import pandas as pd
import numpy as np
from typing import List, Optional
from ..models.flight import FlightFinding, FindingSeverity, EvidenceStrength, FlightEvent, EventType

def check_apogee_discrepancy(actual_df: pd.DataFrame, sim_df: Optional[pd.DataFrame], actual_apogee: FlightEvent) -> List[FlightFinding]:
    findings = []
    if sim_df is None or sim_df.empty:
        return findings
        
    if 'altitude_m' not in sim_df.columns:
        return findings
        
    sim_apogee_m = float(sim_df['altitude_m'].max())
    
    # We need the actual apogee altitude. Let's find it.
    # The event timestamp gives us the row.
    actual_apogee_m = float(actual_df.loc[actual_df['time_s'] == actual_apogee.timestamp_s, 'altitude_baro_m'].iloc[0])
    
    diff_m = actual_apogee_m - sim_apogee_m
    diff_pct = (diff_m / sim_apogee_m) * 100 if sim_apogee_m > 0 else 0
    
    if abs(diff_pct) > 5.0:
        severity = FindingSeverity.MINOR if abs(diff_pct) < 15.0 else FindingSeverity.MODERATE
        direction = "lower" if diff_m < 0 else "higher"
        
        description = (
            f"Measured apogee ({actual_apogee_m:.1f} m) is {abs(diff_pct):.1f}% {direction} "
            f"than the simulated apogee ({sim_apogee_m:.1f} m)."
        )
        
        findings.append(FlightFinding(
            category="TRAJECTORY",
            severity=severity,
            evidence_strength=EvidenceStrength.STRONG,
            title=f"Apogee {direction} than simulation",
            description=description,
            compatible_with=["Simulation configuration mismatch", "Different effective drag", "Different liftoff mass"]
        ))
        
    return findings

def analyze_coast_drag(actual_df: pd.DataFrame, sim_df: pd.DataFrame, burnout: FlightEvent, apogee: FlightEvent) -> List[FlightFinding]:
    """
    Compare deceleration during coast phase to see if drag is higher or lower than modeled.
    """
    findings = []
    if sim_df is None or sim_df.empty or 'velocity_z_m_s' not in sim_df.columns or 'velocity_z_m_s' not in actual_df.columns:
        return findings

    # Get coast phase data
    coast_actual = actual_df[(actual_df['time_s'] > burnout.timestamp_s) & (actual_df['time_s'] < apogee.timestamp_s)]
    coast_sim = sim_df[(sim_df['time_s'] > burnout.timestamp_s) & (sim_df['time_s'] < apogee.timestamp_s)]
    
    if coast_actual.empty or coast_sim.empty:
        return findings
        
    # Compare deceleration (slope of velocity)
    actual_slope = np.polyfit(coast_actual['time_s'], coast_actual['velocity_z_m_s'], 1)[0]
    sim_slope = np.polyfit(coast_sim['time_s'], coast_sim['velocity_z_m_s'], 1)[0]
    
    # Both should be negative
    if actual_slope < sim_slope * 1.1: # 10% more deceleration
        findings.append(FlightFinding(
            category="AERODYNAMICS",
            severity=FindingSeverity.MODERATE,
            evidence_strength=EvidenceStrength.MODERATE,
            title="Coast-phase deceleration higher than simulation",
            description="Observed velocity diverges from simulation after burnout. Deceleration is systematically higher.",
            compatible_with=["Higher aerodynamic drag than modeled", "Atmospheric-density mismatch", "Surface finish mismatch"],
            start_time_s=burnout.timestamp_s,
            end_time_s=apogee.timestamp_s
        ))
            
    return findings

def check_boost_discrepancy(actual_df: pd.DataFrame, sim_df: pd.DataFrame, liftoff: FlightEvent, burnout: FlightEvent) -> List[FlightFinding]:
    findings = []
    if sim_df is None or sim_df.empty or 'velocity_z_m_s' not in sim_df.columns or 'velocity_z_m_s' not in actual_df.columns:
        return findings
        
    boost_actual = actual_df[(actual_df['time_s'] > liftoff.timestamp_s) & (actual_df['time_s'] <= burnout.timestamp_s)]
    boost_sim = sim_df[(sim_df['time_s'] > liftoff.timestamp_s) & (sim_df['time_s'] <= burnout.timestamp_s)]
    
    if boost_actual.empty or boost_sim.empty:
        return findings
        
    act_max_v = boost_actual['velocity_z_m_s'].max()
    sim_max_v = boost_sim['velocity_z_m_s'].max()
    
    diff_pct = ((act_max_v - sim_max_v) / sim_max_v) * 100 if sim_max_v > 0 else 0
    
    if abs(diff_pct) > 5.0:
        direction = "lower" if diff_pct < 0 else "higher"
        findings.append(FlightFinding(
            category="PROPULSION",
            severity=FindingSeverity.MODERATE if abs(diff_pct) > 10 else FindingSeverity.MINOR,
            evidence_strength=EvidenceStrength.STRONG,
            title=f"Boost-phase velocity {direction} than simulation",
            description=f"Derived maximum velocity during boost ({act_max_v:.1f} m/s) is {abs(diff_pct):.1f}% {direction} than simulated ({sim_max_v:.1f} m/s).",
            compatible_with=["Heavier liftoff mass than simulated", "Motor underperformance", "Non-vertical launch", "Sensor smoothing artifact"],
            start_time_s=liftoff.timestamp_s,
            end_time_s=burnout.timestamp_s
        ))
        
    return findings
