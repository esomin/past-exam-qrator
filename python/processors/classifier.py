"""
Classification engine for different grouping options
"""

from typing import Dict, List, Any
from collections import defaultdict
from .solve_parser import SolveInfo

class ClassificationEngine:
    """Handles different types of data classification"""
    
    def classify_by_category(self, data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group data by category2 field"""
        result = defaultdict(list)
        for item in data:
            category = item.get('category2', 'Unknown')
            result[category].append(item)
        return dict(result)
    
    def classify_by_institution(self, data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group data by institution extracted from solve field"""
        result = defaultdict(list)
        for item in data:
            solve_info = SolveInfo.parse(item.get('solve', ''))
            result[solve_info.institution].append(item)
        return dict(result)
    
    def classify_by_year(self, data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group data by year extracted from solve field"""
        result = defaultdict(list)
        for item in data:
            solve_info = SolveInfo.parse(item.get('solve', ''))
            result[solve_info.year].append(item)
        return dict(result)