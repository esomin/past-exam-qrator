"""
Solve field parser module for extracting institution and year information
"""

import re
from typing import Optional
from dataclasses import dataclass


@dataclass
class SolveInfo:
    """Data class to hold parsed solve field information"""
    institution: str
    year: str
    raw_solve: str
    
    @classmethod
    def parse(cls, solve_string: str) -> 'SolveInfo':
        """
        Parse solve string to extract institution and year information.
        
        Expected format: "institution / year"
        Examples:
        - "지방직 7급 / 2022" -> institution="지방직 7급", year="2022"
        - "서울시 7급 / 2021" -> institution="서울시 7급", year="2021"
        - "국가직 7급 / 2020" -> institution="국가직 7급", year="2020"
        
        Args:
            solve_string: The solve field string to parse
            
        Returns:
            SolveInfo object with parsed institution and year
        """
        if not solve_string or not isinstance(solve_string, str):
            return cls(
                institution="Unknown",
                year="Unknown", 
                raw_solve=solve_string or ""
            )
        
        # Clean the input string
        solve_string = solve_string.strip()
        
        # Split by "/" delimiter
        parts = solve_string.split("/")
        
        if len(parts) >= 2:
            # Extract institution (first part) and year (second part)
            institution = parts[0].strip()
            year_part = parts[1].strip()
            
            # Extract year using regex to handle various formats
            year_match = re.search(r'(19|20)\d{2}', year_part)
            year = year_match.group() if year_match else year_part
            
            return cls(
                institution=institution if institution else "Unknown",
                year=year if year else "Unknown",
                raw_solve=solve_string
            )
        else:
            # Handle cases where there's no "/" delimiter
            # Try to extract year from the entire string
            year_match = re.search(r'(19|20)\d{2}', solve_string)
            year = year_match.group() if year_match else "Unknown"
            
            # Use the entire string as institution if no year found, otherwise remove year
            if year != "Unknown":
                institution = re.sub(r'(19|20)\d{2}[년]?', '', solve_string).strip()
                institution = re.sub(r'[/\-\s]+$', '', institution).strip()  # Remove trailing delimiters
            else:
                institution = solve_string
            
            return cls(
                institution=institution if institution else "Unknown",
                year=year,
                raw_solve=solve_string
            )


def parse_solve_field(solve_string: str) -> SolveInfo:
    """
    Convenience function to parse solve field.
    
    Args:
        solve_string: The solve field string to parse
        
    Returns:
        SolveInfo object with parsed institution and year
    """
    return SolveInfo.parse(solve_string)