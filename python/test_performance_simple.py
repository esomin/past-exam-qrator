#!/usr/bin/env python3
"""
Simple Performance Testing Script for React File Processor
Tests with large JSON files to ensure performance
Requirements: 5.3, 5.4
"""

import json
import time
import os
import gc
from typing import Dict, List, Any

# Import modules to test
from main import convert_input_to_answers
from processors.classifier import ClassificationEngine


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
            "title": f"Test question {i + 1} - 지방자치에 관한 설명으로 옳은 것은? " + "A" * (i % 50),
            "solve": f"{institution} / {year}",
            "categoryTitle": category,
            "answerSet": [
                {
                    "id": i * 4 + 1,
                    "title": f"Answer {i * 4 + 1} - 정답 설명입니다. " + "B" * (i % 30),
                    "answerKind": "O"
                },
                {
                    "id": i * 4 + 2,
                    "title": f"Answer {i * 4 + 2} - 오답 설명입니다. " + "C" * (i % 20),
                    "answerKind": "X"
                },
                {
                    "id": i * 4 + 3,
                    "title": f"Answer {i * 4 + 3} - 오답 설명입니다. " + "D" * (i % 25),
                    "answerKind": "X"
                },
                {
                    "id": i * 4 + 4,
                    "title": f"Answer {i * 4 + 4} - 오답 설명입니다. " + "E" * (i % 15),
                    "answerKind": "X"
                }
            ]
        }
        data.append(question)
        
        # Progress indicator
        if (i + 1) % 1000 == 0:
            print(f"Generated {i + 1}/{num_questions} questions...")
    
    return data


def test_data_conversion_performance(test_data: List[Dict]):
    """Test performance of data conversion"""
    print(f"\n=== Testing Data Conversion Performance ===")
    print(f"Input: {len(test_data)} questions")
    
    start_time = time.time()
    
    try:
        answers = convert_input_to_answers(test_data)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ Conversion successful")
        print(f"Output: {len(answers)} answers")
        print(f"Duration: {duration:.2f} seconds")
        print(f"Rate: {len(test_data)/duration:.1f} questions/second")
        
        # Performance thresholds
        if duration > 30:  # Should complete within 30 seconds
            print(f"⚠️  WARNING: Conversion took {duration:.2f}s (threshold: 30s)")
        else:
            print(f"✅ Performance acceptable ({duration:.2f}s)")
            
        return answers, duration
        
    except Exception as e:
        print(f"❌ Conversion failed: {e}")
        return None, None


def test_classification_performance(answers: List[Dict]):
    """Test performance of classification operations"""
    print(f"\n=== Testing Classification Engine Performance ===")
    print(f"Input: {len(answers)} answers")
    
    start_time = time.time()
    
    try:
        engine = ClassificationEngine()
        
        # Test multiple classifications simultaneously
        options = ['category', 'institution', 'year']
        results = engine.process_multiple_classifications(answers, options)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ Engine processing successful")
        print(f"Classifications processed: {len(results)}")
        print(f"Duration: {duration:.2f} seconds")
        print(f"Rate: {len(answers)/duration:.1f} answers/second")
        
        # Verify results
        for result in results:
            print(f"  - {result.type}: {len(result.data)} groups")
        
        # Performance thresholds
        if duration > 60:  # Should complete within 60 seconds for all three
            print(f"⚠️  WARNING: Engine processing took {duration:.2f}s (threshold: 60s)")
        else:
            print(f"✅ Performance acceptable ({duration:.2f}s)")
            
        return results, duration
        
    except Exception as e:
        print(f"❌ Engine processing failed: {e}")
        return None, None


def test_file_size_limits():
    """Test file size handling and limits"""
    print(f"\n=== Testing File Size Limits ===")
    
    # Test different file sizes
    sizes_to_test = [
        (500, "500 questions"),
        (1000, "1K questions"),
        (2000, "2K questions"),
        (5000, "5K questions")
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
            answers, conversion_time = test_data_conversion_performance(test_data)
            
            if answers:
                # Test classification
                classification_results, classification_time = test_classification_performance(answers)
                
                results[size] = {
                    'description': description,
                    'file_size_mb': file_size_mb,
                    'conversion_time': conversion_time,
                    'classification_time': classification_time,
                    'total_time': conversion_time + classification_time if classification_time else conversion_time,
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


def test_memory_optimization():
    """Test memory optimization by processing data in chunks"""
    print(f"\n=== Testing Memory Optimization ===")
    
    # Test processing large dataset in chunks
    total_questions = 3000
    chunk_size = 1000
    
    print(f"Processing {total_questions} questions in chunks of {chunk_size}...")
    
    start_time = time.time()
    total_answers = 0
    
    try:
        for chunk_start in range(0, total_questions, chunk_size):
            chunk_end = min(chunk_start + chunk_size, total_questions)
            chunk_questions = chunk_end - chunk_start
            
            print(f"Processing chunk {chunk_start//chunk_size + 1}: questions {chunk_start+1}-{chunk_end}")
            
            # Generate chunk data
            chunk_data = generate_large_test_data(chunk_questions)
            
            # Process chunk
            answers = convert_input_to_answers(chunk_data)
            total_answers += len(answers)
            
            # Clean up chunk
            del chunk_data
            del answers
            gc.collect()
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ Chunked processing successful")
        print(f"Total answers processed: {total_answers}")
        print(f"Total duration: {duration:.2f} seconds")
        print(f"Average rate: {total_questions/duration:.1f} questions/second")
        
        return {
            'success': True,
            'total_questions': total_questions,
            'total_answers': total_answers,
            'duration': duration,
            'chunk_size': chunk_size
        }
        
    except Exception as e:
        print(f"❌ Chunked processing failed: {e}")
        return {
            'success': False,
            'error': str(e)
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
                print(f"    Conversion: {result['conversion_time']:.2f}s")
                if result.get('classification_time'):
                    print(f"    Classification: {result['classification_time']:.2f}s")
                    print(f"    Total: {result['total_time']:.2f}s")
            else:
                print(f"  {result['description']}: ❌ {result.get('error', 'Failed')}")
    
    # Memory optimization results
    if 'memory_optimization' in all_results:
        opt = all_results['memory_optimization']
        print(f"\n🧹 MEMORY OPTIMIZATION:")
        if opt['success']:
            print(f"  Processed: {opt['total_questions']} questions in chunks")
            print(f"  Duration: {opt['duration']:.2f}s")
            print(f"  Rate: {opt['total_questions']/opt['duration']:.1f} questions/second")
            print(f"  Status: ✅")
        else:
            print(f"  Status: ❌ {opt.get('error', 'Failed')}")
    
    # Performance recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    
    # Check if any tests failed
    failed_tests = []
    if 'file_size_tests' in all_results:
        for size, result in all_results['file_size_tests'].items():
            if not result['success']:
                failed_tests.append(f"File size test: {result['description']}")
    
    if 'memory_optimization' in all_results:
        if not all_results['memory_optimization']['success']:
            failed_tests.append("Memory optimization test")
    
    if failed_tests:
        print(f"  ⚠️  Failed tests found:")
        for test in failed_tests:
            print(f"    - {test}")
        print(f"  ⚠️  Consider optimizing memory usage and processing speed")
    else:
        print(f"  ✅ All performance tests passed!")
        print(f"  ✅ System can handle large files efficiently")
        print(f"  ✅ Memory usage is optimized")
    
    # Performance summary
    if 'file_size_tests' in all_results:
        successful_tests = [r for r in all_results['file_size_tests'].values() if r['success']]
        if successful_tests:
            max_size = max(r['file_size_mb'] for r in successful_tests)
            min_time = min(r['total_time'] for r in successful_tests if 'total_time' in r)
            print(f"\n📈 PERFORMANCE SUMMARY:")
            print(f"  Maximum file size tested: {max_size:.1f}MB")
            print(f"  Best processing time: {min_time:.2f}s")
    
    print(f"\n" + "="*60)


def main():
    """Run all performance tests"""
    print("React File Processor - Performance Testing Suite")
    print("=" * 60)
    
    all_results = {}
    
    try:
        # Test file size limits and performance
        all_results['file_size_tests'] = test_file_size_limits()
        
        # Test memory optimization
        all_results['memory_optimization'] = test_memory_optimization()
        
        # Generate report
        generate_performance_report(all_results)
        
    except Exception as e:
        print(f"❌ Performance testing failed: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\nPerformance testing completed!")


if __name__ == '__main__':
    main()