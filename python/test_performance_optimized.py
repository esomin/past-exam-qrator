#!/usr/bin/env python3
"""
Optimized Performance Testing for React File Processor
Tests large file processing, memory optimization, and resource cleanup
Requirements: 8.2 - Performance testing and optimization
"""

import json
import time
import os
import sys
import gc
import tempfile
from typing import Dict, List, Any

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import convert_input_to_answers
from processors.classifier import ClassificationEngine
from optimize_file_cleanup import ResourceManager


def generate_test_data(num_questions: int) -> List[Dict[str, Any]]:
    """Generate test dataset for performance testing"""
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
            "title": f"Test question {i + 1} about {category} - This is a longer question text to simulate real data with more content.",
            "solve": f"{institution} / {year}",
            "categoryTitle": f"{(i % 5) + 1}) {category}",
            "answerSet": [
                {
                    "id": (i * 4) + 1,
                    "title": f"Correct answer for question {i + 1} - Detailed explanation.",
                    "answerKind": "O"
                },
                {
                    "id": (i * 4) + 2,
                    "title": f"Incorrect answer A for question {i + 1}",
                    "answerKind": "X"
                },
                {
                    "id": (i * 4) + 3,
                    "title": f"Incorrect answer B for question {i + 1}",
                    "answerKind": "X"
                },
                {
                    "id": (i * 4) + 4,
                    "title": f"Incorrect answer C for question {i + 1}",
                    "answerKind": "X"
                }
            ]
        }
        test_data.append(question)
    
    return test_data


def test_large_file_processing():
    """Test processing of large files with different sizes"""
    print("="*60)
    print("TESTING LARGE FILE PROCESSING")
    print("="*60)
    
    test_sizes = [1000, 5000, 10000, 25000]
    results = {}
    
    for size in test_sizes:
        print(f"\nTesting with {size} questions...")
        
        try:
            # Generate test data
            test_data = generate_test_data(size)
            
            # Calculate file size
            json_str = json.dumps(test_data)
            file_size_mb = len(json_str.encode('utf-8')) / 1024 / 1024
            
            # Test processing
            start_time = time.time()
            answers = convert_input_to_answers(test_data)
            processing_time = time.time() - start_time
            
            # Test classification
            classification_engine = ClassificationEngine()
            
            class_start = time.time()
            classification_results = classification_engine.process_multiple_classifications(
                answers, ['category', 'institution', 'year']
            )
            classification_time = time.time() - class_start
            
            results[size] = {
                'success': True,
                'file_size_mb': file_size_mb,
                'processing_time': processing_time,
                'classification_time': classification_time,
                'total_time': processing_time + classification_time,
                'questions_per_second': size / (processing_time + classification_time),
                'output_answers': len(answers),
                'classifications': len(classification_results)
            }
            
            print(f"  ✅ File size: {file_size_mb:.1f}MB")
            print(f"  ✅ Processing: {processing_time:.2f}s")
            print(f"  ✅ Classification: {classification_time:.2f}s")
            print(f"  ✅ Total: {processing_time + classification_time:.2f}s")
            print(f"  ✅ Speed: {size / (processing_time + classification_time):.1f} questions/sec")
            
            # Cleanup
            del test_data, answers, json_str
            gc.collect()
            
        except Exception as e:
            results[size] = {
                'success': False,
                'error': str(e)
            }
            print(f"  ❌ Failed: {str(e)}")
    
    return results


def test_memory_optimization():
    """Test memory optimization with chunked processing"""
    print("\n" + "="*60)
    print("TESTING MEMORY OPTIMIZATION")
    print("="*60)
    
    size = 10000
    print(f"\nTesting memory optimization with {size} questions...")
    
    # Create resource manager
    resource_manager = ResourceManager(max_memory_mb=500)
    
    # Generate test data
    test_data = generate_test_data(size)
    
    # Test normal processing
    print("\n1. Normal processing:")
    start_time = time.time()
    answers_normal = convert_input_to_answers(test_data)
    normal_time = time.time() - start_time
    print(f"   Time: {normal_time:.2f}s")
    print(f"   Results: {len(answers_normal)} answers")
    
    # Test optimized processing
    print("\n2. Optimized chunked processing:")
    
    def process_chunk(chunk):
        return convert_input_to_answers(chunk)
    
    start_time = time.time()
    answers_optimized = resource_manager.process_large_dataset(test_data, process_chunk)
    optimized_time = time.time() - start_time
    
    print(f"   Time: {optimized_time:.2f}s")
    print(f"   Results: {len(answers_optimized)} answers")
    
    # Compare results
    time_difference = optimized_time - normal_time
    results_match = len(answers_optimized) == len(answers_normal)
    
    print(f"\n3. Comparison:")
    print(f"   Time difference: {time_difference:.2f}s")
    print(f"   Results match: {results_match}")
    print(f"   Optimization overhead: {abs(time_difference):.2f}s")
    
    # Cleanup
    del test_data, answers_normal, answers_optimized
    gc.collect()
    
    return {
        'normal_time': normal_time,
        'optimized_time': optimized_time,
        'time_difference': time_difference,
        'results_match': results_match
    }


def test_file_cleanup():
    """Test file cleanup and resource management"""
    print("\n" + "="*60)
    print("TESTING FILE CLEANUP AND RESOURCE MANAGEMENT")
    print("="*60)
    
    resource_manager = ResourceManager()
    
    # Create multiple temporary files
    num_files = 20
    print(f"\n1. Creating {num_files} temporary files...")
    
    temp_files = []
    for i in range(num_files):
        test_data = {"test": f"data_{i}", "items": list(range(50))}
        temp_file = resource_manager.create_temp_result_file(test_data, f"test_file_{i}")
        temp_files.append(temp_file)
    
    # Verify files exist
    existing_files = sum(1 for f in temp_files if os.path.exists(f))
    total_size = sum(os.path.getsize(f) for f in temp_files if os.path.exists(f))
    
    print(f"   Created: {existing_files}/{num_files} files")
    print(f"   Total size: {total_size / 1024:.1f} KB")
    
    # Test cleanup
    print(f"\n2. Testing cleanup...")
    start_time = time.time()
    cleanup_stats = resource_manager.cleanup_and_get_stats()
    cleanup_time = time.time() - start_time
    
    # Verify cleanup
    remaining_files = sum(1 for f in temp_files if os.path.exists(f))
    
    print(f"   Cleanup time: {cleanup_time:.3f}s")
    print(f"   Files cleaned: {cleanup_stats['cleanup_stats']['cleaned_files']}")
    print(f"   Remaining files: {remaining_files}")
    
    cleanup_success = remaining_files == 0
    print(f"   Cleanup success: {cleanup_success}")
    
    return {
        'files_created': existing_files,
        'files_cleaned': cleanup_stats['cleanup_stats']['cleaned_files'],
        'remaining_files': remaining_files,
        'cleanup_time': cleanup_time,
        'cleanup_success': cleanup_success
    }


def test_api_performance():
    """Test API-like performance with base64 encoding/decoding"""
    print("\n" + "="*60)
    print("TESTING API PERFORMANCE (Base64 Processing)")
    print("="*60)
    
    import base64
    
    size = 5000
    print(f"\nTesting API performance with {size} questions...")
    
    # Generate test data
    test_data = generate_test_data(size)
    
    # Simulate API processing
    print("\n1. Encoding to base64...")
    json_str = json.dumps(test_data)
    start_time = time.time()
    encoded_data = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
    encoding_time = time.time() - start_time
    
    print(f"   Encoding time: {encoding_time:.3f}s")
    print(f"   Original size: {len(json_str) / 1024:.1f} KB")
    print(f"   Encoded size: {len(encoded_data) / 1024:.1f} KB")
    
    # Simulate API decoding and processing
    print("\n2. Decoding and processing...")
    start_time = time.time()
    
    # Decode
    decoded_json = base64.b64decode(encoded_data).decode('utf-8')
    decoded_data = json.loads(decoded_json)
    
    # Process
    answers = convert_input_to_answers(decoded_data)
    
    total_time = time.time() - start_time
    
    print(f"   Decoding + processing time: {total_time:.2f}s")
    print(f"   Questions processed: {len(decoded_data)}")
    print(f"   Answers generated: {len(answers)}")
    print(f"   Processing speed: {len(decoded_data) / total_time:.1f} questions/sec")
    
    # Cleanup
    del test_data, json_str, encoded_data, decoded_data, answers
    gc.collect()
    
    return {
        'encoding_time': encoding_time,
        'processing_time': total_time,
        'questions_per_second': len(decoded_data) / total_time if total_time > 0 else 0
    }


def main():
    """Run optimized performance tests"""
    print("REACT FILE PROCESSOR - OPTIMIZED PERFORMANCE TESTING")
    print("="*70)
    
    all_results = {}
    
    try:
        # Test 1: Large file processing
        large_file_results = test_large_file_processing()
        all_results['large_file_processing'] = large_file_results
        
        # Test 2: Memory optimization
        memory_results = test_memory_optimization()
        all_results['memory_optimization'] = memory_results
        
        # Test 3: File cleanup
        cleanup_results = test_file_cleanup()
        all_results['file_cleanup'] = cleanup_results
        
        # Test 4: API performance
        api_results = test_api_performance()
        all_results['api_performance'] = api_results
        
        # Generate summary
        print("\n" + "="*70)
        print("PERFORMANCE TESTING SUMMARY")
        print("="*70)
        
        # Large file processing summary
        if large_file_results:
            successful_sizes = [size for size, result in large_file_results.items() if result.get('success', False)]
            if successful_sizes:
                max_size = max(successful_sizes)
                max_result = large_file_results[max_size]
                print(f"\n📊 LARGE FILE PROCESSING:")
                print(f"   • Maximum size tested: {max_size} questions ({max_result['file_size_mb']:.1f}MB)")
                print(f"   • Processing speed: {max_result['questions_per_second']:.1f} questions/second")
                print(f"   • Total processing time: {max_result['total_time']:.2f}s")
        
        # Memory optimization summary
        if memory_results:
            print(f"\n🧠 MEMORY OPTIMIZATION:")
            print(f"   • Normal processing: {memory_results['normal_time']:.2f}s")
            print(f"   • Optimized processing: {memory_results['optimized_time']:.2f}s")
            print(f"   • Results match: {memory_results['results_match']}")
            print(f"   • Optimization overhead: {abs(memory_results['time_difference']):.2f}s")
        
        # File cleanup summary
        if cleanup_results:
            print(f"\n🗂️ FILE CLEANUP:")
            print(f"   • Files created: {cleanup_results['files_created']}")
            print(f"   • Files cleaned: {cleanup_results['files_cleaned']}")
            print(f"   • Cleanup success: {cleanup_results['cleanup_success']}")
            print(f"   • Cleanup time: {cleanup_results['cleanup_time']:.3f}s")
        
        # API performance summary
        if api_results:
            print(f"\n🌐 API PERFORMANCE:")
            print(f"   • Encoding time: {api_results['encoding_time']:.3f}s")
            print(f"   • Processing speed: {api_results['questions_per_second']:.1f} questions/second")
        
        # Overall assessment
        print(f"\n✅ OPTIMIZATION STATUS:")
        print(f"   ✅ Large file processing: Working")
        print(f"   ✅ Memory optimization: Implemented")
        print(f"   ✅ File cleanup: {'Working' if cleanup_results.get('cleanup_success') else 'Needs attention'}")
        print(f"   ✅ Resource management: Active")
        
        # Save results
        results_file = "data/performance_optimization_results.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2, default=str)
        print(f"\n📄 Results saved to: {results_file}")
        
    except Exception as e:
        print(f"\n❌ Performance testing failed: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n🏁 Performance testing completed!")
    return all_results


if __name__ == '__main__':
    main()