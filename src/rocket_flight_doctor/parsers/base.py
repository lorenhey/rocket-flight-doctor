import abc
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional

class TelemetryParser(abc.ABC):
    """
    Base class for all telemetry parsers.
    A parser takes a file and returns a standardized pandas DataFrame 
    that conforms to the TelemetrySchema or SimulationSchema.
    """
    
    @abc.abstractmethod
    def can_parse(self, file_path: Path) -> bool:
        """
        Check if this parser can handle the given file.
        This should be a fast check (e.g. looking at headers).
        """
        pass
        
    @abc.abstractmethod
    def parse(self, file_path: Path, **kwargs) -> pd.DataFrame:
        """
        Parse the file into a standardized DataFrame.
        """
        pass
