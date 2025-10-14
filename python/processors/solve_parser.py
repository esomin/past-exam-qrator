"""
Solve field parser for extracting institution and year information
"""

from dataclasses import dataclass
from typing import Optional

@dataclass
class SolveInfo:
    institution: str
    year: str
    raw_solve: str
    
    @classmethod
    def parse(cls, solve_string: str) -> 'SolveInfo':
        """
        Parse solve string to extract institution and year
        Expected format: "institution / year"
        Example: "지방직 7급 / 2022"
        """
        if not solve_string or not isinstance(solve_string, str):
            return cls(institution="Unknown", year="Unknown", raw_solve=solve_string or "")
        
        parts = solve_string.split('/')
        if len(parts) >= 2:
            institution = parts[0].strip()
            year = parts[1].strip()
        else:
            institution = solve_string.strip()
            year = "Unknown"
        
        return cls(institution=institution, year=year, raw_solve=solve_string)