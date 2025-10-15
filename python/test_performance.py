#!/usr/bin/env python3
"""
Performance Testing Script for React File Processor
Tests with large JSON files to ensure performance and memory optimization
Requirements: 5.3, 5.4
"""

import json
import time
import psutil
import os
import tempfile
import gc
from typing import Dict, List, Any
import tracemalloc

# Import modules to test
from main import convert_input_to_answers, classify_by_category, classify_by_institution, classify_by_year
from processors.classifier import ClassificationEngine
from remove_similarity_duplicates import SimilarityDeduplicator


class PerformanceMonitor:
    """Monitor memory and CPU usage during tests"""
    
    def __init__(self):
        self.process = psutil.Process()
        self.start_memory = 0
        self.peak_memory = 0
        self.start_time = 0
        
    def start_monitoring(self):
        """Start performance monitoring"""
        tracemalloc.start()
        self.start_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        self.peak_memory = self.start_memory
        self.start_time = time.time()
        gc.collect()  # Clean up before test
        
    def update_peak_memory(self):
        """Update peak memory usage"""
        current_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        if current_memory > self.peak_memory:
            self.peak_memory = current_memory
            
    def get_stats(self):
        """Get performance statistics"""
        end_time = time.time()
        end_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        return {
            'duration': end_time - self.start_time,
            'start_memory_mb': self.start_memory,
            'end_memory_mb': end_memory,
            'peak_memory_mb': self.peak_memory,
            'memory_increase_mb': end_memory - self.start_memory,
            'traced_current_mb': current / 1024 / 1024,
            'traced_peak_mb': peak / 1024 / 1024
        }


def generate_large_test_data(num_questions: int) -> List[Dict[str, Any]]:
    """Generate large test dataset"""
    print(f"Generating {num_questions} test questions...")
    
    institutions = ["지방직 7급", "서울시 7급", "국가직 7급", "경기도 7급", "부산시 7급"]
    years = ["2020", "2021", "2022", "2023", "2024"]
    categories = [
        "1) 지방자치권", "2) 지방자치 변천", "3) 지방자치단체", 
        "4) 지방행정", "5) 지방재정", "6) 지방공무원", "7) 지방의회"
    ]
    
    data = []
    for i in range(num_questions):
        institution = institutions[i % len(institutions)]
        year = years[i % len(years)]
        category = categories[i % len(categories)]
        
        question = {
            "id": 50000 + i,
            "title": f"Test question {i + 1} - 지방자치에 관한 설명으로 옳은 것은? " + "A" * (i % 100),  # Variable length
            "solve": f"{institution} / {year}",
            "categoryTitle": category,
            "answerSet": [
                {
                    "id": i * 4 + 1,
                    "title": f"Answer {i * 4 + 1} - 정답 설명입니다. " + "B" * (i % 50),
                    "answerKind": "O"
                },
                {
                    "id": i * 4 + 2,
                    "title": f"Answer {i * 4 + 2} - 오답 설명입니다. " + "C" * (i % 30),
                    "answerKind": "X"
                },
                {
                    "id": i * 4 + 3,
                    "title": f"Answer {i * 4 + 3} - 오답 설명입니다. " + "D" * (i % 40),
                    "answerKind": "X"
                },
                {
                    "id": i * 4 + 4,
                    "title": f"Answer {i * 4 + 4} - 오답 설명입니다. " + "E" * (i % 20),
                    "answerKind": "X"
                }
            ]
        }
        data.append(question)
        
        # Progress indicator
        if (i + 1) % 1000 == 0:
            print(f"Generated {i + 1}/{num_questions} questions...")
    
    return data


def test_data_conversion_performance(test_data: List[Dict], monitor: PerformanceMonitor):
    """Test performance of data conversion"""
    print(f"\n=== Testing Data Conversion Performance ===")
    print(f"Input: {len(test_data)} questions")
    
    monitor.start_monitoring()
    
    try:
        answers = convert_input_to_answers(test_data)
        monitor.update_peak_memory()
        
        stats = monitor.get_stats()
        
        print(f"✅ Conversion successful")
        print(f"Output: {len(answers)} answers")
        print(f"Duration: {stats['duration']:.2f} seconds")
        print(f"Memory usage: {stats['start_memory_mb']:.1f} → {stats['end_memory_mb']:.1f} MB")
        print(f"Peak memory: {stats['peak_memory_mb']:.1f} MB")
        print(f"Memory increase: {stats['memory_increase_mb']:.1f} MB")
        
        # Performance thresholds - adjusted for larger datasets
        if stats['duration'] > 60:  # Should complete within 60 seconds for large files
            print(f"⚠️  WARNING: Conversion took {stats['duration']:.2f}s (threshold: 60s)")
        
        if stats['memory_increase_mb'] > 1000:  # Should not use more than 1GB additional
            print(f"⚠️  WARNING: Memory increase {stats['memory_increase_mb']:.1f}MB (threshold: 1000MB)")
            
        return answers, stats
        
    except Exception as e:
        print(f"❌ Conversion failed: {e}")
        return None, None


def test_classification_performance(answers: List[Dict], monitor: PerformanceMonitor):
    """Test performance of classification operations"""
    print(f"\n=== Testing Classification Performance ===")
    print(f"Input: {len(answers)} answers")
    
    results = {}
    
    # Test each classification type
    classification_types = [
        ("Category", lambda: classify_by_category(answers)),
        ("Institution", lambda: classify_by_institution(answers)),
        ("Year", lambda: classify_by_year(answers))
    ]
    
    for name, classify_func in classification_types:
        print(f"\nTesting {name} Classification...")
        
        monitor.start_monitoring()
        
        try:
            result = classify_func()
            monitor.update_peak_memory()
            
            stats = monitor.get_stats()
            
            # Count items in result
            if isinstance(result, dict):
                if name == "Category":
                    # Nested structure for category
                    total_items = sum(
                        len(items) for cat2_dict in result.values() 
                        for items in cat2_dict.values()
                    )
                else:
                    # Flat structure for institution/year
                    total_items = sum(len(items) for items in result.values())
            else:
                total_items = len(result) if result else 0
            
            print(f"✅ {name} classification successful")
            print(f"Groups created: {len(result) if result else 0}")
            print(f"Total items classified: {total_items}")
            print(f"Duration: {stats['duration']:.2f} seconds")
            print(f"Memory usage: {stats['start_memory_mb']:.1f} → {stats['end_memory_mb']:.1f} MB")
            print(f"Peak memory: {stats['peak_memory_mb']:.1f} MB")
            
            results[name] = {
                'success': True,
                'groups': len(result) if result else 0,
                'items': total_items,
                'stats': stats
            }
            
            # Performance thresholds
            if stats['duration'] > 60:  # Should complete within 60 seconds
                print(f"⚠️  WARNING: {name} classification took {stats['duration']:.2f}s (threshold: 60s)")
            
            if stats['memory_increase_mb'] > 200:  # Should not use more than 200MB additional
                print(f"⚠️  WARNING: Memory increase {stats['memory_increase_mb']:.1f}MB (threshold: 200MB)")
                
        except Exception as e:
            print(f"❌ {name} classification failed: {e}")
            results[name] = {
                'success': False,
                'error': str(e),
                'stats': None
            }
    
    return results


def test_classification_engine_performance(answers: List[Dict], monitor: PerformanceMonitor):
    """Test performance of classification engine with multiple simultaneous classifications"""
    print(f"\n=== Testing Classification Engine Performance ===")
    print(f"Input: {len(answers)} answers")
    
    monitor.start_monitoring()
    
    try:
        engine = ClassificationEngine()
        
        # Test multiple classifications simultaneously
        options = ['category', 'institution', 'year']
        results = engine.process_multiple_classifications(answers, options)
        
        monitor.update_peak_memory()
        stats = monitor.get_stats()
        
        print(f"✅ Engine processing successful")
        print(f"Classifications processed: {len(results)}")
        print(f"Duration: {stats['duration']:.2f} seconds")
        print(f"Memory usage: {stats['start_memory_mb']:.1f} → {stats['end_memory_mb']:.1f} MB")
        print(f"Peak memory: {stats['peak_memory_mb']:.1f} MB")
        
        # Verify results
        for result in results:
            print(f"  - {result.type}: {len(result.data)} groups")
        
        # Performance thresholds
        if stats['duration'] > 90:  # Should complete within 90 seconds for all three
            print(f"⚠️  WARNING: Engine processing took {stats['duration']:.2f}s (threshold: 90s)")
        
        if stats['memory_increase_mb'] > 300:  # Should not use more than 300MB additional
            print(f"⚠️  WARNING: Memory increase {stats['memory_increase_mb']:.1f}MB (threshold: 300MB)")
            
        return results, stats
        
    except Exception as e:
        print(f"❌ Engine processing failed: {e}")
        return None, None


def test_file_size_limits():
    """Test file size handling and limits"""
    print(f"\n=== Testing File Size Limits ===")
    
    # Test different file sizes - enhanced with larger datasets
    sizes_to_test = [
        (1000, "1K questions"),
        (5000, "5K questions"),
        (10000, "10K questions"),
        (25000, "25K questions"),
        (50000, "50K questions")  # Large dataset test
    ]
    
    results = {}
    
    for size, description in sizes_to_test:
        print(f"\nTesting {description}...")
        
        try:
            # Generate test data
            test_data = generate_large_test_data(size)
            
            # Calculate file size
            json_str = json.dumps(test_data, ensure_ascii=False)
            file_size_mb = len(json_str.encode('utf-8')) / 1024 / 1024
            
            print(f"Generated file size: {file_size_mb:.1f} MB")
            
            # Test conversion
            monitor = PerformanceMonitor()
            answers, conversion_stats = test_data_conversion_performance(test_data, monitor)
            
            if answers:
                # Test classification
                classification_results = test_classification_performance(answers, monitor)
                
                results[size] = {
                    'description': description,
                    'file_size_mb': file_size_mb,
                    'conversion_stats': conversion_stats,
                    'classification_results': classification_results,
                    'success': True
                }
            else:
                results[size] = {
                    'description': description,
                    'file_size_mb': file_size_mb,
                    'success': False,
                    'error': 'Conversion failed'
                }
                
            # Clean up memory
            del test_data
            if answers:
                del answers
            gc.collect()
            
        except Exception as e:
            print(f"❌ Failed to test {description}: {e}")
            results[size] = {
                'description': description,
                'success': False,
                'error': str(e)
            }
    
    return results


def test_memory_cleanup():
    """Test memory cleanup and resource management"""
    print(f"\n=== Testing Memory Cleanup ===")
    
    monitor = PerformanceMonitor()
    monitor.start_monitoring()
    
    initial_memory = monitor.process.memory_info().rss / 1024 / 1024
    print(f"Initial memory: {initial_memory:.1f} MB")
    
    # Create and process multiple datasets
    for i in range(3):
        print(f"\nIteration {i + 1}/3...")
        
        # Generate data
        test_data = generate_large_test_data(2000)
        answers = convert_input_to_answers(test_data)
        
        # Process classifications
        engine = ClassificationEngine()
        results = engine.process_multiple_classifications(answers, ['category', 'institution'])
        
        current_memory = monitor.process.memory_info().rss / 1024 / 1024
        print(f"Memory after processing: {current_memory:.1f} MB")
        
        # Clean up
        del test_data
        del answers
        del results
        del engine
        gc.collect()
        
        after_cleanup_memory = monitor.process.memory_info().rss / 1024 / 1024
        print(f"Memory after cleanup: {after_cleanup_memory:.1f} MB")
    
    final_memory = monitor.process.memory_info().rss / 1024 / 1024
    memory_growth = final_memory - initial_memory
    
    print(f"\nFinal memory: {final_memory:.1f} MB")
    print(f"Total memory growth: {memory_growth:.1f} MB")
    
    if memory_growth > 100:  # Should not grow more than 100MB after cleanup
        print(f"⚠️  WARNING: Memory growth {memory_growth:.1f}MB (threshold: 100MB)")
        print("Possible memory leak detected!")
    else:
        print(f"✅ Memory cleanup successful (growth: {memory_growth:.1f}MB)")
    
    return {
        'initial_memory_mb': initial_memory,
        'final_memory_mb': final_memory,
        'memory_growth_mb': memory_growth,
        'cleanup_successful': memory_growth <= 100
    }


def generate_performance_report(all_results: Dict):
    """Generate comprehensive performance report"""
    print(f"\n" + "="*60)
    print(f"PERFORMANCE TEST REPORT")
    print(f"="*60)
    
    # File size test results
    if 'file_size_tests' in all_results:
        print(f"\n📊 FILE SIZE PERFORMANCE:")
        for size, result in all_results['file_size_tests'].items():
            if result['success']:
                print(f"  {result['description']}: {result['file_size_mb']:.1f}MB - ✅")
                if result.get('conversion_stats'):
                    print(f"    Conversion: {result['conversion_stats']['duration']:.2f}s")
            else:
                print(f"  {result['description']}: ❌ {result.get('error', 'Failed')}")
    
    # Memory cleanup results
    if 'memory_cleanup' in all_results:
        cleanup = all_results['memory_cleanup']
        print(f"\n🧹 MEMORY CLEANUP:")
        print(f"  Initial: {cleanup['initial_memory_mb']:.1f}MB")
        print(f"  Final: {cleanup['final_memory_mb']:.1f}MB")
        print(f"  Growth: {cleanup['memory_growth_mb']:.1f}MB")
        status = "✅" if cleanup['cleanup_successful'] else "❌"
        print(f"  Status: {status}")
    
    # Performance recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    
    # Check if any tests failed
    failed_tests = []
    if 'file_size_tests' in all_results:
        for size, result in all_results['file_size_tests'].items():
            if not result['success']:
                failed_tests.append(f"File size test: {result['description']}")
    
    if failed_tests:
        print(f"  ⚠️  Failed tests found:")
        for test in failed_tests:
            print(f"    - {test}")
    else:
        print(f"  ✅ All performance tests passed!")
    
    # Memory recommendations
    if 'memory_cleanup' in all_results:
        if not all_results['memory_cleanup']['cleanup_successful']:
            print(f"  ⚠️  Consider implementing better memory management")
            print(f"  ⚠️  Review object lifecycle and garbage collection")
    
    print(f"\n" + "="*60)


def main():
    """Run all performance tests"""
    print("React File Processor - Performance Testing Suite")
    print("=" * 60)
    
    all_results = {}
    
    try:
        # Test file size limits and performance
        all_results['file_size_tests'] = test_file_size_limits()
        
        # Test memory cleanup
        all_results['memory_cleanup'] = test_memory_cleanup()
        
        # Generate report
        generate_performance_report(all_results)
        
    except Exception as e:
        print(f"❌ Performance testing failed: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\nPerformance testing completed!")


if __name__ == '__main__':
    main()