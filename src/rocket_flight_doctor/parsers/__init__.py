from pathlib import Path
from .openrocket import OpenRocketParser
from .altos import AltOSParser
from .generic import GenericCSVParser
from .base import TelemetryParser

def get_parser_for_file(file_path: Path) -> TelemetryParser:
    """
    Returns the first parser that claims it can parse the file.
    Order matters: put specific parsers before generic ones.
    """
    parsers = [
        OpenRocketParser(),
        AltOSParser(),
        GenericCSVParser()
    ]
    
    for parser in parsers:
        if parser.can_parse(file_path):
            return parser
            
    raise ValueError(f"No suitable parser found for {file_path}")
