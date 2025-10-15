#!/usr/bin/env python3
"""
Comprehensive backend unit tests for React File Processor
Tests solve parser, classification engine, and API endpoints using input1.json test data
"""

import unittest
import json
import base64
import tempfile
import os
from unittest.mock import patch, MagicMock
from typing import Dict, List, Any

# Import modules to test
from processors.solve_parser import SolveInfo, parse_solve_field
from processors.classifier import ClassificationEngine, ClassificationResult
from main import convert_input_to_answers, classify_by_institution, classify_by_year
from remove_similarity_duplicates import SimilarityDeduplicator
from app import app, validate_json_data, process_file_data, ProcessingError


class TestSolveParserWithRealData(unittest.TestCase):
    """Test solve parser functionality using real data from input1.json"""
    
    @classmethod
    def setUpClass(cls):
        """Load real test data from input1.json"""
        try:
            with open('data/input1.json', 'r', encoding='utf-8') as f:
                cls.real_data = json.load(f)
        except FileNotFoundError:
            # Create minimal test data if input1.json not available
            cls.real_data = [
                {
                    "id": 51596,
                    "title": "Test question 1",
                    "solve": "지방직 7급 / 2022",
                    "categoryTitle": "1) Test Category",
                    "answerSet": [{"id": 1, "title": "Test answer", "answerKind": "O"}]
                },
                {
                    "id": 52052,
                    "title": "Test question 2", 
                    "solve": "서울시 7급 / 2022",
                    "categoryTitle": "2) Test Category 2",
                    "answerSet": [{"id": 2, "title": "Test answer 2", "answerKind": "X"}]
                }
            ]
    
    def test_solve_parsing_with_real_data_samples(self):
        """Test solve parsing with actual data samples from input1.json"""
        # Extract unique solve strings from real data
        solve_strings = set()
        for item in self.real_data[:50]:  # Test first 50 items
            if 'solve' in item and item['solve']:
                solve_strings.add(item['solve'])
        
        self.assertGreater(len(solve_strings), 0, "Should have solve strings in test data")
        
        # Test parsing each unique solve string
        for solve_string in solve_strings:
            with self.subTest(solve=solve_string):
                result = SolveInfo.parse(solve_string)
                
                # Verify result structure
                self.assertIsInstance(result.institution, str)
                self.assertIsInstance(result.year, str)
                self.assertEqual(result.raw_solve, solve_string)
                
                # Verify parsing logic for known formats
                if "/" in solve_string:
                    parts = solve_string.split("/")
                    if len(parts) >= 2:
                        expected_institution = parts[0].strip()
                        self.assertEqual(result.institution, expected_institution)
    
    def test_solve_parsing_edge_cases_from_real_data(self):
        """Test edge cases found in real data"""
        # Test various solve field formats that might exist
        test_cases = [
            ("지방직 7급 / 2022", "지방직 7급", "2022"),
            ("서울시 7급 / 2021", "서울시 7급", "2021"),
            ("국가직 7급 / 2020", "국가직 7급", "2020"),
            ("지방직 9급 / 2023", "지방직 9급", "2023"),
            ("", "Unknown", "Unknown"),
            (None, "Unknown", "Unknown"),
            ("지방직 7급", "지방직 7급", "Unknown"),
            ("2022", "Unknown", "2022"),
        ]
        
        for solve_string, expected_institution, expected_year in test_cases:
            with self.subTest(solve=solve_string):
                result = SolveInfo.parse(solve_string)
                self.assertEqual(result.institution, expected_institution)
                self.assertEqual(result.year, expected_year)
    
    def test_year_extraction_patterns(self):
        """Test year extraction with various patterns found in data"""
        year_test_cases = [
            ("지방직 7급 / 2022년", "2022"),
            ("서울시 7급 / 시행 2021", "2021"),
            ("국가직 7급 / 2020.12", "2020"),
            ("지방직 7급 / 2019-2020", "2019"),  # Should extract first year
            ("지방직 7급 / 22년", "22년"),  # Invalid format, keep original
        ]
        
        for solve_string, expected_year in year_test_cases:
            with self.subTest(solve=solve_string):
                result = SolveInfo.parse(solve_string)
                self.assertEqual(result.year, expected_year)


class TestClassificationEngineWithRealData(unittest.TestCase):
    """Test classification engine with various data scenarios from real test file"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test data from input1.json"""
        try:
            with open('data/input1.json', 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
                # Convert to answers format for testing
                cls.test_answers = convert_input_to_answers(raw_data[:20])  # Use first 20 questions
        except FileNotFoundError:
            # Create test data if file not available
            cls.test_answers = [
                {
                    "id": 1,
                    "category1": "지방행정",
                    "category2": "지방자치권",
                    "institution": "지방직 7급",
                    "year": "2022",
                    "solve": "지방직 7급 / 2022",
                    "question": "Test question 1",
                    "answer": "Test answer 1",
                    "isTrue": True
                },
                {
                    "id": 2,
                    "category1": "지방행정",
                    "category2": "지방자치 변천",
                    "institution": "서울시 7급",
                    "year": "2021",
                    "solve": "서울시 7급 / 2021",
                    "question": "Test question 2",
                    "answer": "Test answer 2",
                    "isTrue": False
                }
            ]
    
    def setUp(self):
        """Set up classification engine for each test"""
        self.engine = ClassificationEngine()
    
    def test_institution_classification_with_real_data(self):
        """Test institution-based classification with real data"""
        result = self.engine.classify_by_institution(self.test_answers)
        
        # Verify structure
        self.assertIsInstance(result, dict)
        self.assertGreater(len(result), 0, "Should have at least one institution")
        
        # Verify all items are classified
        total_items = sum(len(items) for items in result.values())
        self.assertEqual(total_items, len(self.test_answers))
        
        # Verify institution keys are valid
        for institution, items in result.items():
            self.assertIsInstance(institution, str)
            self.assertIsInstance(items, list)
            self.assertGreater(len(items), 0)
            
            # Verify all items in group have same institution
            for item in items:
                self.assertEqual(item.get('institution'), institution)
    
    def test_year_classification_with_real_data(self):
        """Test year-based classification with real data"""
        result = self.engine.classify_by_year(self.test_answers)
        
        # Verify structure
        self.assertIsInstance(result, dict)
        self.assertGreater(len(result), 0, "Should have at least one year")
        
        # Verify all items are classified
        total_items = sum(len(items) for items in result.values())
        self.assertEqual(total_items, len(self.test_answers))
        
        # Verify year keys are valid
        for year, items in result.items():
            self.assertIsInstance(year, str)
            self.assertIsInstance(items, list)
            self.assertGreater(len(items), 0)
            
            # Verify all items in group have same year
            for item in items:
                self.assertEqual(item.get('year'), year)
    
    def test_multiple_classifications_simultaneously(self):
        """Test processing multiple classification types at once"""
        options = ['institution', 'year']
        results = self.engine.process_multiple_classifications(
            data=self.test_answers,
            options=options
        )
        
        # Verify correct number of results
        self.assertEqual(len(results), len(options))
        
        # Verify result types
        result_types = [r.type for r in results]
        self.assertIn('institution', result_types)
        self.assertIn('year', result_types)
        
        # Verify each result has correct structure
        for result in results:
            self.assertIsInstance(result, ClassificationResult)
            self.assertIn(result.type, options)
            self.assertIsInstance(result.data, dict)
            self.assertIsInstance(result.filename, str)
            self.assertTrue(result.filename.endswith('.json'))
    
    def test_category_classification_without_similarity(self):
        """Test category classification without similarity processing"""
        result = self.engine.classify_by_category(self.test_answers)
        
        # Verify nested structure
        self.assertIsInstance(result, dict)
        
        # Verify all items are classified
        total_items = 0
        for cat1_dict in result.values():
            for cat2_list in cat1_dict.values():
                total_items += len(cat2_list)
        
        self.assertEqual(total_items, len(self.test_answers))
        
        # Verify structure integrity
        for cat1, cat2_dict in result.items():
            self.assertIsInstance(cat1, str)
            self.assertIsInstance(cat2_dict, dict)
            for cat2, items in cat2_dict.items():
                self.assertIsInstance(cat2, str)
                self.assertIsInstance(items, list)
                # Verify all items have correct categories
                for item in items:
                    self.assertEqual(item.get('category1'), cat1)
                    self.assertEqual(item.get('category2'), cat2)
    
    def test_engine_result_management(self):
        """Test classification engine result storage and retrieval"""
        # Process classifications
        results = self.engine.process_multiple_classifications(
            data=self.test_answers,
            options=['institution']
        )
        
        self.assertEqual(len(results), 1)
        result = results[0]
        
        # Test result retrieval
        retrieved = self.engine.get_result(result.id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.id, result.id)
        self.assertEqual(retrieved.type, result.type)
        
        # Test result removal
        removed = self.engine.remove_result(result.id)
        self.assertTrue(removed)
        
        # Verify removal
        retrieved_after_removal = self.engine.get_result(result.id)
        self.assertIsNone(retrieved_after_removal)
        
        # Test removing non-existent result
        removed_again = self.engine.remove_result(result.id)
        self.assertFalse(removed_again)
    
    def test_engine_statistics(self):
        """Test classification engine statistics"""
        # Initially empty
        stats = self.engine.get_stats()
        self.assertEqual(stats['total_results'], 0)
        
        # Add some results
        results = self.engine.process_multiple_classifications(
            data=self.test_answers,
            options=['institution', 'year']
        )
        
        # Check updated stats
        stats = self.engine.get_stats()
        self.assertEqual(stats['total_results'], 2)
        self.assertEqual(stats['by_type']['institution'], 1)
        self.assertEqual(stats['by_type']['year'], 1)
        self.assertIsNotNone(stats['oldest_result'])
        self.assertIsNotNone(stats['newest_result'])


class TestAPIEndpointsWithRealData(unittest.TestCase):
    """Test API endpoints with input1.json sample data"""
    
    @classmethod
    def setUpClass(cls):
        """Set up Flask test client and test data"""
        cls.app = app
        cls.app.config['TESTING'] = True
        cls.client = cls.app.test_client()
        
        # Create test data
        try:
            with open('data/input1.json', 'r', encoding='utf-8') as f:
                test_data = json.load(f)[:5]  # Use first 5 questions for API tests
        except FileNotFoundError:
            test_data = [
                {
                    "id": 51596,
                    "title": "Test question",
                    "solve": "지방직 7급 / 2022",
                    "categoryTitle": "1) Test Category",
                    "answerSet": [{"id": 1, "title": "Test answer", "answerKind": "O"}]
                }
            ]
        
        cls.test_file_data = base64.b64encode(
            json.dumps(test_data, ensure_ascii=False).encode('utf-8')
        ).decode('utf-8')
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = self.client.get('/api/health')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertIn('status', data)
        self.assertEqual(data['status'], 'healthy')
        self.assertIn('timestamp', data)
        self.assertIn('classification_stats', data)
    
    def test_process_endpoint_with_valid_data(self):
        """Test file processing endpoint with valid data"""
        payload = {
            "file_data": self.test_file_data,
            "filename": "test_input.json",
            "options": ["institution", "year"]
        }
        
        response = self.client.post('/api/process', 
                                  json=payload,
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertIn('results', data)
        self.assertIn('processed_items', data)
        self.assertIn('original_questions', data)
        
        # Verify results structure
        results = data['results']
        self.assertEqual(len(results), 2)  # institution and year
        
        for result in results:
            self.assertIn('type', result)
            self.assertIn('filename', result)
            self.assertIn('download_id', result)
            self.assertIn(result['type'], ['institution', 'year'])
    
    def test_process_endpoint_with_category_option(self):
        """Test processing with category classification"""
        payload = {
            "file_data": self.test_file_data,
            "filename": "test_input.json",
            "options": ["category"]
        }
        
        response = self.client.post('/api/process', 
                                  json=payload,
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(len(data['results']), 1)
        self.assertEqual(data['results'][0]['type'], 'category')
    
    def test_process_endpoint_validation_errors(self):
        """Test API validation with various error cases"""
        # Test missing file_data
        response = self.client.post('/api/process', 
                                  json={"filename": "test.json", "options": ["category"]})
        self.assertEqual(response.status_code, 400)
        
        # Test missing options
        response = self.client.post('/api/process', 
                                  json={"file_data": self.test_file_data, "filename": "test.json"})
        self.assertEqual(response.status_code, 400)
        
        # Test invalid options
        response = self.client.post('/api/process', 
                                  json={
                                      "file_data": self.test_file_data,
                                      "filename": "test.json",
                                      "options": ["invalid_option"]
                                  })
        self.assertEqual(response.status_code, 400)
        
        # Test empty options
        response = self.client.post('/api/process', 
                                  json={
                                      "file_data": self.test_file_data,
                                      "filename": "test.json",
                                      "options": []
                                  })
        self.assertEqual(response.status_code, 400)
    
    def test_process_endpoint_with_invalid_json(self):
        """Test processing with invalid JSON data"""
        invalid_json_data = base64.b64encode(b"invalid json content").decode('utf-8')
        
        payload = {
            "file_data": invalid_json_data,
            "filename": "invalid.json",
            "options": ["category"]
        }
        
        response = self.client.post('/api/process', 
                                  json=payload,
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        
        data = response.get_json()
        self.assertFalse(data['success'])
        self.assertIn('error', data)
        self.assertEqual(data['error']['code'], 'PROCESSING_ERROR')
    
    def test_download_endpoint_workflow(self):
        """Test complete workflow: process -> download"""
        # First, process a file
        payload = {
            "file_data": self.test_file_data,
            "filename": "test_input.json",
            "options": ["institution"]
        }
        
        process_response = self.client.post('/api/process', 
                                          json=payload,
                                          content_type='application/json')
        
        self.assertEqual(process_response.status_code, 200)
        
        process_data = process_response.get_json()
        download_id = process_data['results'][0]['download_id']
        
        # Then, download the result
        download_response = self.client.get(f'/api/download/{download_id}')
        
        self.assertEqual(download_response.status_code, 200)
        self.assertEqual(download_response.content_type, 'application/json')
        
        # Verify downloaded content is valid JSON
        downloaded_data = download_response.get_json()
        self.assertIsInstance(downloaded_data, dict)
        self.assertGreater(len(downloaded_data), 0)
    
    def test_download_endpoint_with_invalid_id(self):
        """Test download endpoint with non-existent ID"""
        response = self.client.get('/api/download/invalid-id-12345')
        
        self.assertEqual(response.status_code, 404)
        
        data = response.get_json()
        self.assertFalse(data['success'])
        self.assertEqual(data['error']['code'], 'FILE_NOT_FOUND')
    
    def test_data_validation_functions(self):
        """Test data validation helper functions"""
        # Test valid data
        valid_data = [
            {"id": 1, "title": "Test question", "solve": "test / 2022"}
        ]
        result = validate_json_data(valid_data)
        self.assertEqual(result, valid_data)
        
        # Test invalid data types
        with self.assertRaises(ProcessingError):
            validate_json_data("not a list")
        
        with self.assertRaises(ProcessingError):
            validate_json_data([])
        
        with self.assertRaises(ProcessingError):
            validate_json_data([{"missing_id": True}])
        
        with self.assertRaises(ProcessingError):
            validate_json_data([{"id": 1}])  # Missing title


class TestMainProcessingFunctions(unittest.TestCase):
    """Test main processing functions with real data scenarios"""
    
    @classmethod
    def setUpClass(cls):
        """Load test data"""
        try:
            with open('data/input1.json', 'r', encoding='utf-8') as f:
                cls.test_data = json.load(f)[:10]  # Use first 10 questions
        except FileNotFoundError:
            cls.test_data = [
                {
                    "id": 51596,
                    "title": "Test question",
                    "solve": "지방직 7급 / 2022",
                    "categoryTitle": "1) Test Category",
                    "answerSet": [{"id": 1, "title": "Test answer", "answerKind": "O"}]
                }
            ]
    
    def test_convert_input_to_answers(self):
        """Test conversion from input format to answers format"""
        answers = convert_input_to_answers(self.test_data)
        
        # Verify structure
        self.assertIsInstance(answers, list)
        self.assertGreater(len(answers), 0)
        
        # Verify each answer has required fields
        for answer in answers:
            required_fields = ['id', 'category1', 'category2', 'institution', 
                             'year', 'solve', 'question', 'answer', 'isTrue']
            for field in required_fields:
                self.assertIn(field, answer, f"Missing field: {field}")
        
        # Verify institution and year extraction
        for answer in answers:
            self.assertIsInstance(answer['institution'], str)
            self.assertIsInstance(answer['year'], str)
            # Should not be empty unless solve field was empty/invalid
            if answer['solve']:
                self.assertNotEqual(answer['institution'], '')
                self.assertNotEqual(answer['year'], '')
    
    def test_classify_by_institution_function(self):
        """Test standalone institution classification function"""
        answers = convert_input_to_answers(self.test_data)
        result = classify_by_institution(answers)
        
        # Verify structure
        self.assertIsInstance(result, dict)
        
        # Verify all items are classified
        total_items = sum(len(items) for items in result.values())
        self.assertEqual(total_items, len(answers))
        
        # Verify grouping correctness
        for institution, items in result.items():
            for item in items:
                self.assertEqual(item['institution'], institution)
    
    def test_classify_by_year_function(self):
        """Test standalone year classification function"""
        answers = convert_input_to_answers(self.test_data)
        result = classify_by_year(answers)
        
        # Verify structure
        self.assertIsInstance(result, dict)
        
        # Verify all items are classified
        total_items = sum(len(items) for items in result.values())
        self.assertEqual(total_items, len(answers))
        
        # Verify grouping correctness
        for year, items in result.items():
            for item in items:
                self.assertEqual(item['year'], year)


if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestSolveParserWithRealData,
        TestClassificationEngineWithRealData,
        TestAPIEndpointsWithRealData,
        TestMainProcessingFunctions
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    print(f"{'='*50}")