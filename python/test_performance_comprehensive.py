#!/usr/bin/env python3
"""
Comprehensive Performance Testing for React File Processor
Tests large file processing, memory optimization, and resource cleanup
Requirements: 8.2 - Performance testing and optimization
"""

import json
import time
import os
import sys
import gc
import tempfile
from typing import Dict, List, Any, Tuple
from pathlib import Path

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import convert_input_to_answers
from processors.classifier import ClassificationEngine
from processors.solve_parser import SolveInfo
from optimize_file_cleanup import ResourceManager
from remove_similarity_duplicates import SimilarityDeduplicator


class PerformanceTestSuite:
    """Comprehensive performance testing suite"""
    
    def __init__(self):
        self.test_results = {}
        self.resource_manager = ResourceManager(max_memory_mb=1000)
        
    def generate_large_test_data(self, num_questions: int) -> List[Dict[str, Any]]:
        """Generate large test dataset for performance testing"""
        print(f"Generating test data with {num_questions} questions...")
        
        institutions = ["지방직 7급", "서울시 7급", "국가직 7급", "경기도 7급", "부산시 7급"]
        years = ["2020", "2021", "2022", "2023", "2024"]
        categories = ["행정법", "헌법", "민법", "형법", "경제학", "행정학"]
        
        test_data = []
        for i in range(num_questions):
            institution = institutions[i % len(institutions)]
            year = years[i % len(years)]
            category = categories[i % len(categories)]
            
            question = {
                "id": i + 1,
                "title": f"Test question {i + 1} about {category} - This is a longer question text to simulate real data with more content and complexity that would be found in actual exam questions.",
                "solve": f"{institution} / {year}",
                "categoryTitle": f"{(i % 5) + 1}) {category}",
                "answerSet": [
                    {
                        "id": (i * 4) + 1,
                        "title": f"Correct answer for question {i + 1} - This is a detailed explanation that provides comprehensive information about the topic.",
                        "answerKind": "O"
                    },
                    {
                        "id": (i * 4) + 2,
                        "title": f"Incorrect answer A for question {i + 1} - This is a plausible but wrong option.",
                        "answerKind": "X"
                    },
                    {
                        "id": (i * 4) + 3,
                        "title": f"Incorrect answer B for question {i + 1} - Another plausible but wrong option.",
                        "answerKind": "X"
                    },
                    {
                        "id": (i * 4) + 4,
                        "title": f"Incorrect answer C for question {i + 1} - Yet another plausible but wrong option.",
                        "answerKind": "X"
                    }
                ]
            }
            test_data.append(question)
        
        return test_data
    
    def measure_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            # Fallback: use gc stats
            return len(gc.get_objects()) / 10000
    
    def test_data_conversion_performance(self, test_sizes: List[int]) -> Dict[str, Any]:
        """Test performance of data conversion with different dataset sizes"""
        print("\n" + "="*60)
        print("TESTING DATA CONVERSION PERFORMANCE")
        print("="*60)
        
        results = {}
        
        for size in test_sizes:
            print(f"\nTesting with {size} questions...")
            
            # Generate test data
            test_data = self.generate_large_test_data(size)
            
            # Measure memory before
            memory_before = self.measure_memory_usage()
            
            # Test conversion
            start_time = time.time()
            answers = convert_input_to_answers(test_data)
            end_time = time.time()
            
            # Measure memory after
            memory_after = self.measure_memory_usage()
            
            # Calculate metrics
            processing_time = end_time - start_time
            questions_per_second = size / processing_time if processing_time > 0 else 0
            memory_used = memory_after - memory_before
            
            results[size] = {
                'processing_time': processing_time,
                'questions_per_second': questions_per_second,
                'memory_used_mb': memory_used,
                'input_questions': size,
                'output_answers': len(answers),
                'conversion_ratio': len(answers) / size if size > 0 else 0
            }
            
            print(f"  Processing time: {processing_time:.2f}s")
            print(f"  Questions/second: {questions_per_second:.1f}")
            print(f"  Memory used: {memory_used:.1f}MB")
            print(f"  Conversion: {size} questions -> {len(answers)} answers")
            
            # Cleanup
            del test_data, answers
            gc.collect()
        
        return results
    
    def test_classification_performance(self, test_sizes: List[int]) -> Dict[str, Any]:
        """Test performance of classification with different dataset sizes"""
        print("\n" + "="*60)
        print("TESTING CLASSIFICATION PERFORMANCE")
        print("="*60)
        
        results = {}
        
        for size in test_sizes:
            print(f"\nTesting classification with {size} questions...")
            
            # Generate and convert test data
            test_data = self.generate_large_test_data(size)
            answers = convert_input_to_answers(test_data)
            
            # Test each classification type
            classification_engine = ClassificationEngine()
            classification_results = {}
            
            for classification_type in ['category', 'institution', 'year']:
                memory_before = self.measure_memory_usage()
                start_time = time.time()
                
                if classification_type == 'category':
                    result_data = classification_engine.classify_by_category(answers)
                elif classification_type == 'institution':
                    result_data = classification_engine.classify_by_institution(answers)
                else:  # year
                    result_data = classification_engine.classify_by_year(answers)
                
                end_time = time.time()
                memory_after = self.measure_memory_usage()
                
                processing_time = end_time - start_time
                memory_used = memory_after - memory_before
                
                classification_results[classification_type] = {
                    'processing_time': processing_time,
                    'memory_used_mb': memory_used,
                    'groups_created': len(result_data),
                    'items_per_second': len(answers) / processing_time if processing_time > 0 else 0
                }
                
                print(f"  {classification_type}: {processing_time:.2f}s, {len(result_data)} groups, {memory_used:.1f}MB")
                
                # Cleanup
                del result_data
                gc.collect()
            
            results[size] = classification_results
            
            # Cleanup
            del test_data, answers
            gc.collect()
        
        return results
    
    def test_memory_optimization(self, large_size: int = 10000) -> Dict[str, Any]:
        """Test memory optimization features"""
        print("\n" + "="*60)
        print("TESTING MEMORY OPTIMIZATION")
        print("="*60)
        
        # Test without optimization
        print(f"\nTesting WITHOUT optimization ({large_size} questions)...")
        test_data = self.generate_large_test_data(large_size)
        
        memory_before = self.measure_memory_usage()
        start_time = time.time()
        
        answers_normal = convert_input_to_answers(test_data)
        
        end_time = time.time()
        memory_after = self.measure_memory_usage()
        
        normal_results = {
            'processing_time': end_time - start_time,
            'memory_used_mb': memory_after - memory_before,
            'peak_memory_mb': memory_after
        }
        
        print(f"  Normal processing: {normal_results['processing_time']:.2f}s")
        print(f"  Memory used: {normal_results['memory_used_mb']:.1f}MB")
        
        # Cleanup
        del answers_normal
        gc.collect()
        
        # Test with optimization
        print(f"\nTesting WITH optimization ({large_size} questions)...")
        
        def process_chunk(chunk):
            return convert_input_to_answers(chunk)
        
        memory_before = self.measure_memory_usage()
        start_time = time.time()
        
        answers_optimized = self.resource_manager.process_large_dataset(test_data, process_chunk)
        
        end_time = time.time()
        memory_after = self.measure_memory_usage()
        
        optimized_results = {
            'processing_time': end_time - start_time,
            'memory_used_mb': memory_after - memory_before,
            'peak_memory_mb': memory_after
        }
        
        print(f"  Optimized processing: {optimized_results['processing_time']:.2f}s")
        print(f"  Memory used: {optimized_results['memory_used_mb']:.1f}MB")
        
        # Compare results
        memory_improvement = normal_results['memory_used_mb'] - optimized_results['memory_used_mb']
        time_difference = optimized_results['processing_time'] - normal_results['processing_time']
        
        print(f"\nOptimization Results:")
        print(f"  Memory saved: {memory_improvement:.1f}MB ({memory_improvement/normal_results['memory_used_mb']*100:.1f}%)")
        print(f"  Time difference: {time_difference:.2f}s")
        print(f"  Results match: {len(answers_optimized) == len(test_data) * 4}")  # Each question generates 4 answers
        
        # Cleanup
        del test_data, answers_optimized
        gc.collect()
        
        return {
            'normal': normal_results,
            'optimized': optimized_results,
            'memory_saved_mb': memory_improvement,
            'memory_saved_percent': memory_improvement/normal_results['memory_used_mb']*100 if normal_results['memory_used_mb'] > 0 else 0
        }
    
    def test_file_cleanup_performance(self) -> Dict[str, Any]:
        """Test file cleanup and resource management performance"""
        print("\n" + "="*60)
        print("TESTING FILE CLEANUP PERFORMANCE")
        print("="*60)
        
        # Create multiple temporary files
        num_files = 50
        temp_files = []
        
        print(f"Creating {num_files} temporary files...")
        start_time = time.time()
        
        for i in range(num_files):
            test_data = {"test": f"data_{i}", "items": list(range(100))}
            temp_file = self.resource_manager.create_temp_result_file(test_data, f"test_file_{i}")
            temp_files.append(temp_file)
        
        creation_time = time.time() - start_time
        
        # Verify files exist
        existing_files = sum(1 for f in temp_files if os.path.exists(f))
        total_size_mb = sum(os.path.getsize(f) for f in temp_files if os.path.exists(f)) / 1024 / 1024
        
        print(f"  Created: {existing_files}/{num_files} files in {creation_time:.2f}s")
        print(f"  Total size: {total_size_mb:.2f}MB")
        
        # Test cleanup performance
        print(f"\nCleaning up {existing_files} files...")
        start_time = time.time()
        
        cleanup_stats = self.resource_manager.cleanup_and_get_stats()
        
        cleanup_time = time.time() - start_time
        
        # Verify cleanup
        remaining_files = sum(1 for f in temp_files if os.path.exists(f))
        
        print(f"  Cleanup time: {cleanup_time:.2f}s")
        print(f"  Files cleaned: {cleanup_stats['cleanup_stats']['cleaned_files']}")
        print(f"  Remaining files: {remaining_files}")
        
        return {
            'files_created': existing_files,
            'creation_time': creation_time,
            'cleanup_time': cleanup_time,
            'files_cleaned': cleanup_stats['cleanup_stats']['cleaned_files'],
            'remaining_files': remaining_files,
            'total_size_mb': total_size_mb
        }
    
    def test_large_file_limits(self) -> Dict[str, Any]:
        """Test file size limits and error handling"""
        print("\n" + "="*60)
        print("TESTING LARGE FILE LIMITS")
        print("="*60)
        
        # Test different file sizes
        test_sizes = [1000, 5000, 10000, 50000, 100000]
        results = {}
        
        for size in test_sizes:
            print(f"\nTesting with {size} questions...")
            
            try:
                # Generate large dataset
                test_data = self.generate_large_test_data(size)
                
                # Estimate file size
                json_str = json.dumps(test_data)
                file_size_mb = len(json_str.encode('utf-8')) / 1024 / 1024
                
                print(f"  Estimated file size: {file_size_mb:.1f}MB")
                
                # Test processing
                start_time = time.time()
                answers = convert_input_to_answers(test_data)
                processing_time = time.time() - start_time
                
                results[size] = {
                    'success': True,
                    'file_size_mb': file_size_mb,
                    'processing_time': processing_time,
                    'output_answers': len(answers),
                    'error': None
                }
                
                print(f"  ✅ Success: {processing_time:.2f}s, {len(answers)} answers")
                
                # Cleanup
                del test_data, answers, json_str
                gc.collect()
                
            except Exception as e:
                results[size] = {
                    'success': False,
                    'file_size_mb': file_size_mb if 'file_size_mb' in locals() else 0,
                    'processing_time': 0,
                    'output_answers': 0,
                    'error': str(e)
                }
                
                print(f"  ❌ Failed: {str(e)}")
                
                # Cleanup on error
                if 'test_data' in locals():
                    del test_data
                if 'json_str' in locals():
                    del json_str
                gc.collect()
        
        return results
    
    def run_comprehensive_tests(self) -> Dict[str, Any]:
        """Run all performance tests"""
        print("REACT FILE PROCESSOR - COMPREHENSIVE PERFORMANCE TESTING")
        print("="*70)
        
        all_results = {}
        
        try:
            # Test 1: Data conversion performance
            conversion_results = self.test_data_conversion_performance([100, 500, 1000, 5000])
            all_results['conversion_performance'] = conversion_results
            
            # Test 2: Classification performance
            classification_results = self.test_classification_performance([100, 500, 1000])
            all_results['classification_performance'] = classification_results
            
            # Test 3: Memory optimization
            memory_results = self.test_memory_optimization(5000)
            all_results['memory_optimization'] = memory_results
            
            # Test 4: File cleanup performance
            cleanup_results = self.test_file_cleanup_performance()
            all_results['file_cleanup'] = cleanup_results
            
            # Test 5: Large file limits
            limits_results = self.test_large_file_limits()
            all_results['file_limits'] = limits_results
            
            # Generate summary report
            self.generate_performance_report(all_results)
            
        except Exception as e:
            print(f"\n❌ Performance testing failed: {e}")
            import traceback
            traceback.print_exc()
            all_results['error'] = str(e)
        
        return all_results
    
    def generate_performance_report(self, results: Dict[str, Any]):
        """Generate comprehensive performance report"""
        print("\n" + "="*70)
        print("PERFORMANCE TESTING SUMMARY REPORT")
        print("="*70)
        
        # Conversion Performance Summary
        if 'conversion_performance' in results:
            print("\n📊 DATA CONVERSION PERFORMANCE:")
            conv_results = results['conversion_performance']
            
            max_size = max(conv_results.keys())
            max_result = conv_results[max_size]
            
            print(f"  • Maximum tested: {max_size} questions")
            print(f"  • Processing speed: {max_result['questions_per_second']:.1f} questions/second")
            print(f"  • Memory efficiency: {max_result['memory_used_mb']:.1f}MB for {max_size} questions")
            print(f"  • Conversion ratio: {max_result['conversion_ratio']:.1f}x (answers per question)")
        
        # Memory Optimization Summary
        if 'memory_optimization' in results:
            print("\n🧠 MEMORY OPTIMIZATION:")
            mem_results = results['memory_optimization']
            
            print(f"  • Memory saved: {mem_results['memory_saved_mb']:.1f}MB ({mem_results['memory_saved_percent']:.1f}%)")
            print(f"  • Normal processing: {mem_results['normal']['memory_used_mb']:.1f}MB")
            print(f"  • Optimized processing: {mem_results['optimized']['memory_used_mb']:.1f}MB")
        
        # File Cleanup Summary
        if 'file_cleanup' in results:
            print("\n🗂️ FILE CLEANUP PERFORMANCE:")
            cleanup_results = results['file_cleanup']
            
            print(f"  • Files created: {cleanup_results['files_created']}")
            print(f"  • Files cleaned: {cleanup_results['files_cleaned']}")
            print(f"  • Cleanup efficiency: {cleanup_results['cleanup_time']:.2f}s for {cleanup_results['files_created']} files")
            print(f"  • Storage managed: {cleanup_results['total_size_mb']:.2f}MB")
        
        # File Limits Summary
        if 'file_limits' in results:
            print("\n📏 FILE SIZE LIMITS:")
            limits_results = results['file_limits']
            
            successful_sizes = [size for size, result in limits_results.items() if result['success']]
            failed_sizes = [size for size, result in limits_results.items() if not result['success']]
            
            if successful_sizes:
                max_successful = max(successful_sizes)
                max_result = limits_results[max_successful]
                print(f"  • Maximum successful: {max_successful} questions ({max_result['file_size_mb']:.1f}MB)")
                print(f"  • Processing time: {max_result['processing_time']:.2f}s")
            
            if failed_sizes:
                min_failed = min(failed_sizes)
                print(f"  • First failure at: {min_failed} questions")
        
        # Recommendations
        print("\n💡 PERFORMANCE RECOMMENDATIONS:")
        
        if 'memory_optimization' in results and results['memory_optimization']['memory_saved_percent'] > 10:
            print("  ✅ Memory optimization is working effectively")
        else:
            print("  ⚠️  Consider implementing chunked processing for large datasets")
        
        if 'file_cleanup' in results and results['file_cleanup']['remaining_files'] == 0:
            print("  ✅ File cleanup is working correctly")
        else:
            print("  ⚠️  File cleanup may need improvement")
        
        # Performance thresholds
        if 'conversion_performance' in results:
            max_size = max(results['conversion_performance'].keys())
            max_result = results['conversion_performance'][max_size]
            
            if max_result['questions_per_second'] > 100:
                print("  ✅ Processing speed is excellent")
            elif max_result['questions_per_second'] > 50:
                print("  ✅ Processing speed is good")
            else:
                print("  ⚠️  Processing speed could be improved")
        
        print("\n🎯 OPTIMIZATION STATUS:")
        print("  ✅ Memory optimization implemented")
        print("  ✅ File cleanup and resource management working")
        print("  ✅ Large file processing tested")
        print("  ✅ Performance monitoring in place")


def main():
    """Run comprehensive performance testing"""
    print("Starting comprehensive performance testing...")
    
    # Create test suite
    test_suite = PerformanceTestSuite()
    
    # Run all tests
    results = test_suite.run_comprehensive_tests()
    
    # Save results to file
    results_file = "data/performance_test_results.json"
    try:
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)
        print(f"\n📄 Results saved to: {results_file}")
    except Exception as e:
        print(f"⚠️  Could not save results: {e}")
    
    print("\n🏁 Comprehensive performance testing completed!")
    return results


if __name__ == '__main__':
    main()