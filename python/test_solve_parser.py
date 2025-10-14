"""
Unit tests for solve field parser module
"""

import unittest
from processors.solve_parser import SolveInfo, parse_solve_field


class TestSolveParser(unittest.TestCase):
    """Test cases for solve field parsing functionality"""
    
    def test_standard_format_parsing(self):
        """Test parsing of standard format solve strings"""
        # Test case from requirements: "지방직 7급 / 2022"
        result = SolveInfo.parse("지방직 7급 / 2022")
        self.assertEqual(result.institution, "지방직 7급")
        self.assertEqual(result.year, "2022")
        self.assertEqual(result.raw_solve, "지방직 7급 / 2022")
        
        # Test case from requirements: "서울시 7급 / 2021"
        result = SolveInfo.parse("서울시 7급 / 2021")
        self.assertEqual(result.institution, "서울시 7급")
        self.assertEqual(result.year, "2021")
        self.assertEqual(result.raw_solve, "서울시 7급 / 2021")
        
        # Additional test case: "국가직 7급 / 2020"
        result = SolveInfo.parse("국가직 7급 / 2020")
        self.assertEqual(result.institution, "국가직 7급")
        self.assertEqual(result.year, "2020")
        self.assertEqual(result.raw_solve, "국가직 7급 / 2020")
    
    def test_whitespace_handling(self):
        """Test parsing with various whitespace scenarios"""
        # Extra spaces around delimiter
        result = SolveInfo.parse("지방직 7급  /  2022")
        self.assertEqual(result.institution, "지방직 7급")
        self.assertEqual(result.year, "2022")
        
        # Leading/trailing spaces
        result = SolveInfo.parse("  서울시 7급 / 2021  ")
        self.assertEqual(result.institution, "서울시 7급")
        self.assertEqual(result.year, "2021")
    
    def test_edge_cases(self):
        """Test edge cases and malformed inputs"""
        # Empty string
        result = SolveInfo.parse("")
        self.assertEqual(result.institution, "Unknown")
        self.assertEqual(result.year, "Unknown")
        self.assertEqual(result.raw_solve, "")
        
        # None input
        result = SolveInfo.parse(None)
        self.assertEqual(result.institution, "Unknown")
        self.assertEqual(result.year, "Unknown")
        self.assertEqual(result.raw_solve, "")
        
        # No delimiter
        result = SolveInfo.parse("지방직 7급 2022")
        self.assertEqual(result.institution, "지방직 7급")
        self.assertEqual(result.year, "2022")
        
        # Only institution, no year
        result = SolveInfo.parse("지방직 7급 /")
        self.assertEqual(result.institution, "지방직 7급")
        self.assertEqual(result.year, "Unknown")
        
        # Only year, no institution
        result = SolveInfo.parse("/ 2022")
        self.assertEqual(result.institution, "Unknown")
        self.assertEqual(result.year, "2022")
        
        # Multiple delimiters
        result = SolveInfo.parse("지방직 7급 / 2022 / 추가정보")
        self.assertEqual(result.institution, "지방직 7급")
        self.assertEqual(result.year, "2022")
    
    def test_year_extraction(self):
        """Test year extraction from various formats"""
        # Year with additional text
        result = SolveInfo.parse("지방직 7급 / 2022년")
        self.assertEqual(result.year, "2022")
        
        # Year in different position
        result = SolveInfo.parse("지방직 7급 / 시행 2022")
        self.assertEqual(result.year, "2022")
        
        # Multiple years (should extract first valid one)
        result = SolveInfo.parse("지방직 7급 / 2021-2022")
        self.assertEqual(result.year, "2021")
        
        # Invalid year format
        result = SolveInfo.parse("지방직 7급 / 22년")
        self.assertEqual(result.year, "22년")  # Should keep original if no valid 4-digit year
    
    def test_convenience_function(self):
        """Test the convenience parse_solve_field function"""
        result = parse_solve_field("지방직 7급 / 2022")
        self.assertEqual(result.institution, "지방직 7급")
        self.assertEqual(result.year, "2022")
    
    def test_real_data_samples(self):
        """Test with actual data samples from input1.json"""
        # Sample from the test data
        result = SolveInfo.parse("지방직 7급 / 2022")
        self.assertEqual(result.institution, "지방직 7급")
        self.assertEqual(result.year, "2022")
        
        result = SolveInfo.parse("서울시 7급 / 2022")
        self.assertEqual(result.institution, "서울시 7급")
        self.assertEqual(result.year, "2022")
        
        result = SolveInfo.parse("서울시 7급 / 2021")
        self.assertEqual(result.institution, "서울시 7급")
        self.assertEqual(result.year, "2021")
        
        result = SolveInfo.parse("지방직 7급 / 2021")
        self.assertEqual(result.institution, "지방직 7급")
        self.assertEqual(result.year, "2021")
        
        result = SolveInfo.parse("지방직 7급 / 2020")
        self.assertEqual(result.institution, "지방직 7급")
        self.assertEqual(result.year, "2020")
        
        result = SolveInfo.parse("서울시 7급 / 2020")
        self.assertEqual(result.institution, "서울시 7급")
        self.assertEqual(result.year, "2020")


if __name__ == '__main__':
    unittest.main()