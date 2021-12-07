import enum
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, ConfigDict

class FlightPhase(str, enum.Enum):
    PRE_LAUNCH = "pre_launch"
    IGNITION = "ignition"
    RAIL = "rail"
    BOOST = "boost"
    COAST = "coast"
    APOGEE = "apogee"
    DROGUE_DESCENT = "drogue_descent"
    MAIN_DESCENT = "main_descent"
    LANDED = "landed"
    UNKNOWN = "unknown"

class SensorHealth(str, enum.Enum):
    GOOD = "GOOD"
    QUESTIONABLE = "QUESTIONABLE"
    SATURATED = "SATURATED"
    DROPOUT = "DROPOUT"
    MISALIGNED = "MISALIGNED"
    UNKNOWN = "UNKNOWN"

class EventType(str, enum.Enum):
    LIFTOFF = "liftoff"
    BURNOUT = "burnout"
    APOGEE = "apogee"
    DEPLOYMENT_DROGUE = "deployment_drogue"
    DEPLOYMENT_MAIN = "deployment_main"
    LANDING = "landing"
    USER_MARKER = "user_marker"
    OTHER = "other"

class DataProvenance(str, enum.Enum):
    MEASURED = "MEASURED"
    DERIVED = "DERIVED"
    INFERRED = "INFERRED"
    HYPOTHESIS = "HYPOTHESIS"
    UNKNOWN = "UNKNOWN"

class FlightEvent(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    event_type: EventType
    timestamp_s: float
    uncertainty_s: Optional[float] = None
    provenance: DataProvenance
    description: str = ""
    source: str = ""

class FindingSeverity(str, enum.Enum):
    INFO = "INFO"
    MINOR = "MINOR"
    MODERATE = "MODERATE"
    MAJOR = "MAJOR"

class EvidenceStrength(str, enum.Enum):
    WEAK = "WEAK"
    MODERATE = "MODERATE"
    STRONG = "STRONG"

class FlightFinding(BaseModel):
    category: str
    severity: FindingSeverity
    evidence_strength: EvidenceStrength
    title: str
    description: str
    compatible_with: List[str] = Field(default_factory=list)
    start_time_s: Optional[float] = None
    end_time_s: Optional[float] = None

class VehicleSnapshot(BaseModel):
    dry_mass_kg: Optional[float] = None
    liftoff_mass_kg: Optional[float] = None
    diameter_m: Optional[float] = None
    length_m: Optional[float] = None
    motor_designation: Optional[str] = None
    simulation_hash: Optional[str] = None

class Flight(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    name: str
    vehicle: VehicleSnapshot = Field(default_factory=VehicleSnapshot)
    events: List[FlightEvent] = Field(default_factory=list)
    findings: List[FlightFinding] = Field(default_factory=list)
