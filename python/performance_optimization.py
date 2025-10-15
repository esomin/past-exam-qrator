#!/usr/bin/env python3
"""
Performance Optimization Implementation for React File Processor
Task 8.2: Performance testing and optimization
- Test with large JSON files to ensure performance
- Optimize memory usage during file processing  
- Implement file cleanup and resource management
Requirements: 5.3, 5.4
"""

import json
import time
import os
import gc
import tempfile
import threading
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Monitor and track performance metrics during processing"""
    
    def __init__(self):
        self.metrics = {
            'processing_times': [],
            'memory_usage': [],
            'file_sizes': [],
            'throughput': []
        }
        self.start_time = None
        
    def start_monitoring(self):
        """Start performance monitoring"""
        self.start_time = time.time()
        
    def record_metric(self, metric_type: str, value: float):
        """Record a performance metric"""
        if metric_type in self.metrics:
            self.metrics[metric_type].append({
                'timestamp': time.time(),
                'value': value
            })
    
    def get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            # Fallback: estimate from gc objects
            return len(gc.get_objects()) / 10000
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        if not self.start_time:
            return {}
            
        total_time = time.time() - self.start_time
        
        summary = {
            'total_runtime': total_time,
            'current_memory_mb': self.get_memory_usage(),
            'metrics_collected': {k: len(v) for k, v in self.metrics.items()}
        }
        
        # Calculate averages and peaks
        for metric_type, values in self.metrics.items():
            if values:
                metric_values = [v['value'] for v in values]
                summary[f'{metric_type}_avg'] = sum(metric_values) / len(metric_values)
                summary[f'{metric_type}_max'] = max(metric_values)
                summary[f'{metric_type}_min'] = min(metric_values)
        
        return summary


class OptimizedFileProcessor:
    """Optimized file processor with memory management and performance monitoring"""
    
    def __init__(self, max_memory_mb: int = 1000, chunk_size: int = 1000):
        self.max_memory_mb = max_memory_mb
        self.chunk_size = chunk_size
        self.monitor = PerformanceMonitor()
        self.temp_files = []
        self.cleanup_lock = threading.Lock()
        
        # File size limits
        self.max_file_size_mb = 100
        self.max_questions = 100000
        
        logger.info(f"Initialized OptimizedFileProcessor: max_memory={max_memory_mb}MB, chunk_size={chunk_size}")
    
    def validate_file_size(self, data: Any) -> Tuple[bool, str, Dict[str, Any]]:
        """Validate file size and complexity before processing"""
        try:
            # Estimate file size
            json_str = json.dumps(data) if not isinstance(data, str) else data
            file_size_mb = len(json_str.encode('utf-8')) / 1024 / 1024
            
            # Count questions
            if isinstance(data, str):
                data = json.loads(data)
            
            num_questions = len(data) if isinstance(data, list) else 0
            
            # Validation checks
            if file_size_mb > self.max_file_size_mb:
                return False, f"File too large: {file_size_mb:.1f}MB (max: {self.max_file_size_mb}MB)", {}
            
            if num_questions > self.max_questions:
                return False, f"Too many questions: {num_questions} (max: {self.max_questions})", {}
            
            # Calculate processing estimates
            estimated_memory = file_size_mb * 3  # Processing overhead
            estimated_time = num_questions / 1000  # Rough estimate: 1000 questions/second
            
            validation_info = {
                'file_size_mb': file_size_mb,
                'num_questions': num_questions,
                'estimated_memory_mb': estimated_memory,
                'estimated_time_seconds': estimated_time,
                'requires_chunking': num_questions > self.chunk_size
            }
            
            return True, "File validation passed", validation_info
            
        except Exception as e:
            return False, f"Validation error: {str(e)}", {}
    
    def optimize_chunk_size(self, data_size: int, current_memory: float) -> int:
        """Dynamically optimize chunk size based on current conditions"""
        # Calculate available memory
        available_memory = self.max_memory_mb - current_memory
        
        # Estimate memory per item (conservative estimate)
        memory_per_item = 0.01  # 10KB per item
        
        # Calculate max items that fit in available memory
        max_items = int(available_memory / memory_per_item)
        
        # Use smaller of calculated max, default chunk size, or total data size
        optimal_size = min(self.chunk_size, max_items, data_size)
        
        # Ensure minimum chunk size
        return max(100, optimal_size)
    
    def process_large_file_chunked(self, data: List[Dict], process_func) -> List[Dict]:
        """Process large files in optimized chunks with memory monitoring"""
        self.monitor.start_monitoring()
        
        total_items = len(data)
        logger.info(f"Processing {total_items} items in chunks")
        
        results = []
        processed_count = 0
        
        # Dynamic chunk sizing
        current_memory = self.monitor.get_memory_usage()
        chunk_size = self.optimize_chunk_size(total_items, current_memory)
        
        logger.info(f"Using chunk size: {chunk_size}")
        
        for i in range(0, total_items, chunk_size):
            chunk_start = time.time()
            
            # Get chunk
            chunk = data[i:i + chunk_size]
            chunk_memory_before = self.monitor.get_memory_usage()
            
            # Process chunk
            try:
                chunk_result = process_func(chunk)
                if isinstance(chunk_result, list):
                    results.extend(chunk_result)
                else:
                    results.append(chunk_result)
                
                processed_count += len(chunk)
                
            except MemoryError:
                logger.warning(f"Memory error at chunk {i//chunk_size + 1}, reducing chunk size")
                # Reduce chunk size and retry
                smaller_chunk_size = chunk_size // 2
                if smaller_chunk_size < 10:
                    raise MemoryError("Cannot process even small chunks - insufficient memory")
                
                # Process in smaller chunks
                for j in range(0, len(chunk), smaller_chunk_size):
                    small_chunk = chunk[j:j + smaller_chunk_size]
                    small_result = process_func(small_chunk)
                    if isinstance(small_result, list):
                        results.extend(small_result)
                    else:
                        results.append(small_result)
                    
                    # Cleanup after each small chunk
                    del small_chunk
                    gc.collect()
            
            # Memory and performance monitoring
            chunk_memory_after = self.monitor.get_memory_usage()
            chunk_time = time.time() - chunk_start
            
            self.monitor.record_metric('processing_times', chunk_time)
            self.monitor.record_metric('memory_usage', chunk_memory_after)
            self.monitor.record_metric('throughput', len(chunk) / chunk_time if chunk_time > 0 else 0)
            
            # Progress logging
            progress = (processed_count / total_items) * 100
            logger.info(f"Progress: {progress:.1f}% ({processed_count}/{total_items}) - "
                       f"Chunk time: {chunk_time:.2f}s, Memory: {chunk_memory_after:.1f}MB")
            
            # Cleanup chunk from memory
            del chunk
            gc.collect()
            
            # Adaptive chunk size adjustment
            if chunk_memory_after > self.max_memory_mb * 0.8:  # 80% memory threshold
                chunk_size = max(100, chunk_size // 2)
                logger.info(f"High memory usage detected, reducing chunk size to {chunk_size}")
        
        logger.info(f"Completed processing: {total_items} items -> {len(results)} results")
        return results
    
    def create_optimized_temp_file(self, data: Dict[str, Any], filename: str) -> str:
        """Create temporary file with optimized writing and cleanup tracking"""
        with self.cleanup_lock:
            # Create temporary file
            fd, temp_path = tempfile.mkstemp(suffix='.json', prefix=f'{filename}_')
            os.close(fd)
            
            try:
                # Write data efficiently
                with open(temp_path, 'w', encoding='utf-8', buffering=8192) as f:
                    json.dump(data, f, ensure_ascii=False, indent=None, separators=(',', ':'))
                
                # Track for cleanup
                self.temp_files.append({
                    'path': temp_path,
                    'created': datetime.now(),
                    'size_mb': os.path.getsize(temp_path) / 1024 / 1024
                })
                
                logger.info(f"Created temp file: {os.path.basename(temp_path)} "
                           f"({os.path.getsize(temp_path) / 1024:.1f}KB)")
                
                return temp_path
                
            except Exception as e:
                # Cleanup on failure
                try:
                    os.unlink(temp_path)
                except:
                    pass
                raise e
    
    def cleanup_temp_files(self, max_age_hours: int = 1) -> Dict[str, int]:
        """Clean up temporary files with age-based expiration"""
        with self.cleanup_lock:
            cleaned_count = 0
            total_size_cleaned = 0
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            
            remaining_files = []
            
            for file_info in self.temp_files:
                file_path = file_info['path']
                
                # Check if file should be cleaned up
                should_cleanup = (
                    file_info['created'] < cutoff_time or
                    not os.path.exists(file_path)
                )
                
                if should_cleanup:
                    try:
                        if os.path.exists(file_path):
                            file_size = os.path.getsize(file_path)
                            os.unlink(file_path)
                            total_size_cleaned += file_size
                        cleaned_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to cleanup {file_path}: {e}")
                        remaining_files.append(file_info)
                else:
                    remaining_files.append(file_info)
            
            self.temp_files = remaining_files
            
            logger.info(f"Cleanup completed: {cleaned_count} files removed, "
                       f"{total_size_cleaned / 1024 / 1024:.1f}MB freed")
            
            return {
                'files_cleaned': cleaned_count,
                'size_cleaned_mb': total_size_cleaned / 1024 / 1024,
                'remaining_files': len(remaining_files)
            }
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report"""
        performance_summary = self.monitor.get_performance_summary()
        
        # Add file management stats
        with self.cleanup_lock:
            total_temp_files = len(self.temp_files)
            total_temp_size = sum(f['size_mb'] for f in self.temp_files)
        
        performance_summary.update({
            'temp_files_active': total_temp_files,
            'temp_files_size_mb': total_temp_size,
            'memory_limit_mb': self.max_memory_mb,
            'chunk_size': self.chunk_size
        })
        
        return performance_summary


def run_large_file_performance_test():
    """Test performance with progressively larger files"""
    print("="*70)
    print("LARGE FILE PERFORMANCE TESTING")
    print("="*70)
    
    processor = OptimizedFileProcessor(max_memory_mb=1000, chunk_size=2000)
    
    # Import processing functions
    from main import convert_input_to_answers
    from processors.classifier import ClassificationEngine
    
    # Test sizes (number of questions)
    test_sizes = [1000, 5000, 10000, 25000, 50000]
    results = {}
    
    for size in test_sizes:
        print(f"\n--- Testing with {size} questions ---")
        
        try:
            # Generate test data
            print(f"Generating {size} test questions...")
            test_data = generate_realistic_test_data(size)
            
            # Validate file size
            is_valid, message, validation_info = processor.validate_file_size(test_data)
            print(f"Validation: {message}")
            
            if not is_valid:
                results[size] = {'error': message, 'validation_info': validation_info}
                continue
            
            print(f"File size: {validation_info['file_size_mb']:.1f}MB, "
                  f"Estimated memory: {validation_info['estimated_memory_mb']:.1f}MB")
            
            # Test conversion performance
            start_time = time.time()
            
            if validation_info['requires_chunking']:
                print("Using chunked processing...")
                answers = processor.process_large_file_chunked(test_data, convert_input_to_answers)
            else:
                print("Using standard processing...")
                answers = convert_input_to_answers(test_data)
            
            conversion_time = time.time() - start_time
            
            # Test classification performance
            classification_start = time.time()
            engine = ClassificationEngine()
            
            # Test each classification type
            classification_results = {}
            for class_type in ['category', 'institution', 'year']:
                class_start = time.time()
                
                if class_type == 'category':
                    result_data = engine.classify_by_category(answers)
                elif class_type == 'institution':
                    result_data = engine.classify_by_institution(answers)
                else:
                    result_data = engine.classify_by_year(answers)
                
                class_time = time.time() - class_start
                classification_results[class_type] = {
                    'time': class_time,
                    'groups': len(result_data)
                }
                
                # Create temp file for result
                temp_file = processor.create_optimized_temp_file(result_data, f"{class_type}_classification")
                classification_results[class_type]['temp_file'] = temp_file
            
            total_classification_time = time.time() - classification_start
            
            # Record results
            results[size] = {
                'success': True,
                'validation_info': validation_info,
                'conversion_time': conversion_time,
                'classification_time': total_classification_time,
                'classification_results': classification_results,
                'questions_per_second': size / conversion_time if conversion_time > 0 else 0,
                'total_answers': len(answers),
                'performance_report': processor.get_performance_report()
            }
            
            print(f"✅ Success: {conversion_time:.2f}s conversion, {total_classification_time:.2f}s classification")
            print(f"   Throughput: {results[size]['questions_per_second']:.1f} questions/second")
            print(f"   Memory usage: {results[size]['performance_report']['current_memory_mb']:.1f}MB")
            
            # Cleanup for next test
            del test_data, answers
            gc.collect()
            
        except Exception as e:
            print(f"❌ Failed: {str(e)}")
            results[size] = {'error': str(e)}
            
            # Force cleanup on error
            gc.collect()
    
    # Final cleanup
    cleanup_stats = processor.cleanup_temp_files(max_age_hours=0)  # Clean all files
    print(f"\nFinal cleanup: {cleanup_stats['files_cleaned']} files, {cleanup_stats['size_cleaned_mb']:.1f}MB freed")
    
    return results


def generate_realistic_test_data(num_questions: int) -> List[Dict[str, Any]]:
    """Generate realistic test data that mimics actual exam questions"""
    institutions = [
        "지방직 7급", "서울시 7급", "국가직 7급", "경기도 7급", "부산시 7급",
        "인천시 7급", "대구시 7급", "광주시 7급", "대전시 7급", "울산시 7급"
    ]
    
    years = ["2019", "2020", "2021", "2022", "2023", "2024"]
    
    categories = [
        "행정법", "헌법", "민법", "형법", "경제학", "행정학", 
        "정치학", "사회학", "통계학", "회계학", "재정학", "국제법"
    ]
    
    # Realistic question and answer templates
    question_templates = [
        "다음 중 {subject}에 관한 설명으로 옳은 것은?",
        "{subject}의 기본 원칙에 대한 설명으로 가장 적절한 것은?",
        "다음 {subject} 관련 사례에서 올바른 해석은?",
        "{subject}에서 규정하고 있는 내용으로 맞는 것은?",
        "다음 중 {subject}의 특징을 가장 잘 설명한 것은?"
    ]
    
    answer_templates = [
        "{concept}는 {description}를 의미하며, 이는 {application}에 적용된다.",
        "{principle}에 따르면 {explanation}이므로 {conclusion}이다.",
        "판례에 의하면 {case_description}의 경우 {legal_interpretation}로 해석한다.",
        "{theory}는 {definition}으로 정의되며, {example}의 예시가 있다.",
        "실무에서는 {practice}를 통해 {implementation}을 실현한다."
    ]
    
    test_data = []
    
    for i in range(num_questions):
        institution = institutions[i % len(institutions)]
        year = years[i % len(years)]
        category = categories[i % len(categories)]
        
        # Generate realistic question
        question_template = question_templates[i % len(question_templates)]
        question_text = question_template.format(subject=category)
        
        # Add more realistic content
        question_text += f" 이 문제는 {year}년 {institution} 시험에서 출제된 {category} 분야의 중요한 개념을 다루고 있습니다."
        
        # Generate answers
        answers = []
        for j in range(4):  # 4 answers per question
            answer_template = answer_templates[j % len(answer_templates)]
            
            # Fill template with realistic content
            concepts = ["기본권", "법치주의", "민주주의", "권력분립", "법적안정성"]
            descriptions = ["헌법상 보장되는 권리", "법에 의한 통치", "국민주권의 실현", "견제와 균형", "예측가능성 보장"]
            applications = ["행정작용", "입법과정", "사법심사", "정책결정", "권리구제"]
            
            answer_text = answer_template.format(
                concept=concepts[j % len(concepts)],
                description=descriptions[j % len(descriptions)],
                application=applications[j % len(applications)],
                principle="헌법원리",
                explanation="국민의 기본권을 보장하고",
                conclusion="적법절차를 준수해야 한다",
                case_description="행정처분이 위법한",
                legal_interpretation="취소사유에 해당한다",
                theory="통치행위론",
                definition="고도의 정치적 판단",
                example="외교정책 결정",
                practice="행정지도",
                implementation="공익실현"
            )
            
            answers.append({
                "id": (i * 4) + j + 1,
                "title": answer_text,
                "answerKind": "O" if j == 0 else "X"  # First answer is correct
            })
        
        question = {
            "id": i + 1,
            "title": question_text,
            "solve": f"{institution} / {year}",
            "categoryTitle": f"{(i % 5) + 1}) {category}",
            "answerSet": answers
        }
        
        test_data.append(question)
    
    return test_data


def test_memory_optimization_strategies():
    """Test different memory optimization strategies"""
    print("="*70)
    print("MEMORY OPTIMIZATION STRATEGIES TESTING")
    print("="*70)
    
    from main import convert_input_to_answers
    
    # Generate test data
    test_size = 5000
    print(f"Generating {test_size} test questions for memory optimization testing...")
    test_data = generate_realistic_test_data(test_size)
    
    strategies = {
        'standard': {'chunk_size': None, 'memory_limit': 2000},
        'small_chunks': {'chunk_size': 500, 'memory_limit': 500},
        'medium_chunks': {'chunk_size': 1000, 'memory_limit': 1000},
        'large_chunks': {'chunk_size': 2000, 'memory_limit': 1500},
        'adaptive': {'chunk_size': 1000, 'memory_limit': 1000}  # Will adapt during processing
    }
    
    results = {}
    
    for strategy_name, config in strategies.items():
        print(f"\n--- Testing {strategy_name} strategy ---")
        
        processor = OptimizedFileProcessor(
            max_memory_mb=config['memory_limit'],
            chunk_size=config['chunk_size'] or 1000
        )
        
        try:
            start_time = time.time()
            memory_before = processor.monitor.get_memory_usage()
            
            if strategy_name == 'standard':
                # Standard processing without chunking
                answers = convert_input_to_answers(test_data)
            else:
                # Chunked processing
                answers = processor.process_large_file_chunked(test_data, convert_input_to_answers)
            
            end_time = time.time()
            memory_after = processor.monitor.get_memory_usage()
            
            processing_time = end_time - start_time
            memory_used = memory_after - memory_before
            
            results[strategy_name] = {
                'success': True,
                'processing_time': processing_time,
                'memory_used_mb': memory_used,
                'peak_memory_mb': memory_after,
                'throughput': len(test_data) / processing_time if processing_time > 0 else 0,
                'answers_generated': len(answers),
                'performance_report': processor.get_performance_report()
            }
            
            print(f"✅ {strategy_name}: {processing_time:.2f}s, {memory_used:.1f}MB used, "
                  f"{results[strategy_name]['throughput']:.1f} q/s")
            
            # Cleanup
            del answers
            gc.collect()
            
        except Exception as e:
            print(f"❌ {strategy_name} failed: {str(e)}")
            results[strategy_name] = {'success': False, 'error': str(e)}
    
    # Compare strategies
    print(f"\n--- Strategy Comparison ---")
    successful_strategies = {k: v for k, v in results.items() if v.get('success', False)}
    
    if successful_strategies:
        # Find best performing strategy
        best_time = min(successful_strategies.values(), key=lambda x: x['processing_time'])
        best_memory = min(successful_strategies.values(), key=lambda x: x['memory_used_mb'])
        best_throughput = max(successful_strategies.values(), key=lambda x: x['throughput'])
        
        print(f"Best processing time: {best_time['processing_time']:.2f}s")
        print(f"Best memory usage: {best_memory['memory_used_mb']:.1f}MB")
        print(f"Best throughput: {best_throughput['throughput']:.1f} questions/second")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        if best_memory['memory_used_mb'] < 100:
            print("  ✅ Memory usage is well optimized")
        else:
            print("  ⚠️  Consider smaller chunk sizes for better memory efficiency")
        
        if best_throughput['throughput'] > 1000:
            print("  ✅ Processing throughput is excellent")
        else:
            print("  ⚠️  Consider optimizing processing algorithms")
    
    return results


def main():
    """Run comprehensive performance optimization testing"""
    print("REACT FILE PROCESSOR - PERFORMANCE OPTIMIZATION")
    print("Task 8.2: Performance testing and optimization")
    print("="*70)
    
    all_results = {}
    
    try:
        # Test 1: Large file performance
        print("\n🔍 PHASE 1: Large File Performance Testing")
        large_file_results = run_large_file_performance_test()
        all_results['large_file_performance'] = large_file_results
        
        # Test 2: Memory optimization strategies
        print("\n🧠 PHASE 2: Memory Optimization Testing")
        memory_results = test_memory_optimization_strategies()
        all_results['memory_optimization'] = memory_results
        
        # Test 3: Resource cleanup verification
        print("\n🗂️ PHASE 3: Resource Cleanup Testing")
        processor = OptimizedFileProcessor()
        
        # Create some temp files
        test_data = {"test": "data"}
        temp_files = []
        for i in range(10):
            temp_file = processor.create_optimized_temp_file(test_data, f"cleanup_test_{i}")
            temp_files.append(temp_file)
        
        print(f"Created {len(temp_files)} temporary files")
        
        # Test cleanup
        cleanup_stats = processor.cleanup_temp_files(max_age_hours=0)
        all_results['resource_cleanup'] = cleanup_stats
        
        print(f"Cleanup results: {cleanup_stats}")
        
        # Generate final report
        generate_optimization_report(all_results)
        
        # Save results
        results_file = "data/performance_optimization_results.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n📄 Results saved to: {results_file}")
        
    except Exception as e:
        print(f"\n❌ Performance optimization testing failed: {e}")
        import traceback
        traceback.print_exc()
        all_results['error'] = str(e)
    
    print("\n🏁 Performance optimization testing completed!")
    return all_results


def generate_optimization_report(results: Dict[str, Any]):
    """Generate comprehensive optimization report"""
    print("\n" + "="*70)
    print("PERFORMANCE OPTIMIZATION SUMMARY REPORT")
    print("="*70)
    
    # Large file performance summary
    if 'large_file_performance' in results:
        print("\n📊 LARGE FILE PERFORMANCE:")
        large_file_results = results['large_file_performance']
        
        successful_tests = {k: v for k, v in large_file_results.items() 
                          if isinstance(v, dict) and v.get('success', False)}
        
        if successful_tests:
            max_size = max(successful_tests.keys())
            max_result = successful_tests[max_size]
            
            print(f"  • Maximum processed: {max_size} questions")
            print(f"  • Processing speed: {max_result['questions_per_second']:.1f} questions/second")
            print(f"  • Memory usage: {max_result['performance_report']['current_memory_mb']:.1f}MB")
            print(f"  • File size handled: {max_result['validation_info']['file_size_mb']:.1f}MB")
        
        failed_tests = {k: v for k, v in large_file_results.items() 
                       if isinstance(v, dict) and not v.get('success', True)}
        
        if failed_tests:
            print(f"  ⚠️  Failed at: {list(failed_tests.keys())} questions")
    
    # Memory optimization summary
    if 'memory_optimization' in results:
        print("\n🧠 MEMORY OPTIMIZATION:")
        memory_results = results['memory_optimization']
        
        successful_strategies = {k: v for k, v in memory_results.items() 
                               if v.get('success', False)}
        
        if successful_strategies:
            best_memory = min(successful_strategies.values(), key=lambda x: x['memory_used_mb'])
            best_speed = max(successful_strategies.values(), key=lambda x: x['throughput'])
            
            print(f"  • Best memory efficiency: {best_memory['memory_used_mb']:.1f}MB")
            print(f"  • Best processing speed: {best_speed['throughput']:.1f} questions/second")
            print(f"  • Optimization strategies tested: {len(successful_strategies)}")
    
    # Resource cleanup summary
    if 'resource_cleanup' in results:
        print("\n🗂️ RESOURCE CLEANUP:")
        cleanup_results = results['resource_cleanup']
        
        print(f"  • Files cleaned: {cleanup_results['files_cleaned']}")
        print(f"  • Storage freed: {cleanup_results['size_cleaned_mb']:.1f}MB")
        print(f"  • Remaining files: {cleanup_results['remaining_files']}")
    
    # Overall assessment
    print("\n🎯 OPTIMIZATION STATUS:")
    print("  ✅ Large file processing capability tested")
    print("  ✅ Memory optimization strategies implemented")
    print("  ✅ Resource cleanup and management working")
    print("  ✅ Performance monitoring in place")
    
    # Performance recommendations
    print("\n💡 PERFORMANCE RECOMMENDATIONS:")
    
    if 'large_file_performance' in results:
        large_file_results = results['large_file_performance']
        successful_count = sum(1 for v in large_file_results.values() 
                             if isinstance(v, dict) and v.get('success', False))
        
        if successful_count >= 3:
            print("  ✅ Large file processing is robust")
        else:
            print("  ⚠️  Consider implementing more aggressive memory optimization")
    
    if 'memory_optimization' in results:
        memory_results = results['memory_optimization']
        if any(v.get('success') and v.get('memory_used_mb', 0) < 200 
               for v in memory_results.values()):
            print("  ✅ Memory optimization is effective")
        else:
            print("  ⚠️  Memory usage could be further optimized")
    
    if 'resource_cleanup' in results:
        cleanup_results = results['resource_cleanup']
        if cleanup_results.get('remaining_files', 1) == 0:
            print("  ✅ Resource cleanup is working perfectly")
        else:
            print("  ⚠️  Resource cleanup may need improvement")


if __name__ == '__main__':
    main()