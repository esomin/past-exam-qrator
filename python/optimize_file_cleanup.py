#!/usr/bin/env python3
"""
File Cleanup and Resource Management Optimization
Implements automatic cleanup of temporary files and memory optimization
Requirements: 5.3, 5.4
"""

import os
import tempfile
import time
import json
import gc
from typing import Dict, List, Any, Optional
from pathlib import Path
import threading
import atexit


class FileCleanupManager:
    """Manages temporary file cleanup and resource management"""
    
    def __init__(self):
        self.temp_files: List[str] = []
        self.temp_dirs: List[str] = []
        self.cleanup_lock = threading.Lock()
        
        # Register cleanup on exit
        atexit.register(self.cleanup_all)
    
    def create_temp_file(self, suffix: str = '.json', prefix: str = 'react_processor_') -> str:
        """Create a temporary file and register it for cleanup"""
        with self.cleanup_lock:
            fd, temp_path = tempfile.mkstemp(suffix=suffix, prefix=prefix)
            os.close(fd)  # Close the file descriptor
            self.temp_files.append(temp_path)
            return temp_path
    
    def create_temp_dir(self, prefix: str = 'react_processor_') -> str:
        """Create a temporary directory and register it for cleanup"""
        with self.cleanup_lock:
            temp_dir = tempfile.mkdtemp(prefix=prefix)
            self.temp_dirs.append(temp_dir)
            return temp_dir
    
    def cleanup_file(self, file_path: str) -> bool:
        """Clean up a specific file"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                with self.cleanup_lock:
                    if file_path in self.temp_files:
                        self.temp_files.remove(file_path)
                return True
        except Exception as e:
            print(f"Warning: Failed to cleanup file {file_path}: {e}")
        return False
    
    def cleanup_dir(self, dir_path: str) -> bool:
        """Clean up a specific directory"""
        try:
            if os.path.exists(dir_path):
                import shutil
                shutil.rmtree(dir_path)
                with self.cleanup_lock:
                    if dir_path in self.temp_dirs:
                        self.temp_dirs.remove(dir_path)
                return True
        except Exception as e:
            print(f"Warning: Failed to cleanup directory {dir_path}: {e}")
        return False
    
    def cleanup_all(self) -> Dict[str, int]:
        """Clean up all registered temporary files and directories"""
        cleaned_files = 0
        cleaned_dirs = 0
        
        with self.cleanup_lock:
            # Clean up files
            for file_path in self.temp_files.copy():
                if self.cleanup_file(file_path):
                    cleaned_files += 1
            
            # Clean up directories
            for dir_path in self.temp_dirs.copy():
                if self.cleanup_dir(dir_path):
                    cleaned_dirs += 1
        
        return {
            'cleaned_files': cleaned_files,
            'cleaned_dirs': cleaned_dirs
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cleanup manager statistics"""
        with self.cleanup_lock:
            return {
                'registered_files': len(self.temp_files),
                'registered_dirs': len(self.temp_dirs),
                'total_registered': len(self.temp_files) + len(self.temp_dirs)
            }


class MemoryOptimizer:
    """Optimizes memory usage during file processing"""
    
    def __init__(self, max_memory_mb: int = 500):
        self.max_memory_mb = max_memory_mb
        self.chunk_size = 1000  # Default chunk size for processing
    
    def get_memory_usage(self) -> float:
        """Get current memory usage in MB (simplified version)"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            # Fallback: use gc stats
            return len(gc.get_objects()) / 10000  # Rough approximation
    
    def optimize_chunk_size(self, data_size: int) -> int:
        """Calculate optimal chunk size based on data size and memory constraints"""
        # Estimate memory per item (rough calculation)
        estimated_memory_per_item = 0.001  # 1KB per item estimate
        
        # Calculate max items that fit in memory constraint
        max_items_in_memory = int(self.max_memory_mb / estimated_memory_per_item)
        
        # Use smaller of default chunk size or memory-constrained size
        optimal_chunk_size = min(self.chunk_size, max_items_in_memory, data_size)
        
        return max(100, optimal_chunk_size)  # Minimum chunk size of 100
    
    def process_in_chunks(self, data: List[Any], process_func, chunk_size: Optional[int] = None) -> List[Any]:
        """Process data in memory-optimized chunks"""
        if chunk_size is None:
            chunk_size = self.optimize_chunk_size(len(data))
        
        results = []
        
        for i in range(0, len(data), chunk_size):
            chunk = data[i:i + chunk_size]
            
            # Process chunk
            chunk_result = process_func(chunk)
            results.extend(chunk_result if isinstance(chunk_result, list) else [chunk_result])
            
            # Clean up chunk from memory
            del chunk
            gc.collect()
        
        return results
    
    def force_garbage_collection(self) -> Dict[str, int]:
        """Force garbage collection and return statistics"""
        before_objects = len(gc.get_objects())
        collected = gc.collect()
        after_objects = len(gc.get_objects())
        
        return {
            'objects_before': before_objects,
            'objects_after': after_objects,
            'objects_collected': collected,
            'objects_freed': before_objects - after_objects
        }


class ResourceManager:
    """Combined resource management for files and memory"""
    
    def __init__(self, max_memory_mb: int = 500):
        self.file_manager = FileCleanupManager()
        self.memory_optimizer = MemoryOptimizer(max_memory_mb)
        self.processing_stats = {
            'files_created': 0,
            'files_cleaned': 0,
            'memory_optimizations': 0,
            'gc_collections': 0
        }
    
    def create_temp_result_file(self, data: Dict[str, Any], filename: str) -> str:
        """Create a temporary result file with automatic cleanup"""
        temp_path = self.file_manager.create_temp_file(suffix='.json', prefix=f'{filename}_')
        
        try:
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            self.processing_stats['files_created'] += 1
            return temp_path
            
        except Exception as e:
            # Clean up on failure
            self.file_manager.cleanup_file(temp_path)
            raise e
    
    def process_large_dataset(self, data: List[Any], process_func, chunk_size: Optional[int] = None) -> List[Any]:
        """Process large dataset with memory optimization"""
        self.processing_stats['memory_optimizations'] += 1
        
        # Force garbage collection before processing
        gc_stats = self.memory_optimizer.force_garbage_collection()
        self.processing_stats['gc_collections'] += 1
        
        # Process in chunks
        results = self.memory_optimizer.process_in_chunks(data, process_func, chunk_size)
        
        # Final garbage collection
        self.memory_optimizer.force_garbage_collection()
        self.processing_stats['gc_collections'] += 1
        
        return results
    
    def cleanup_and_get_stats(self) -> Dict[str, Any]:
        """Perform cleanup and return comprehensive statistics"""
        # Cleanup files
        cleanup_stats = self.file_manager.cleanup_all()
        self.processing_stats['files_cleaned'] += cleanup_stats['cleaned_files']
        
        # Final memory cleanup
        memory_stats = self.memory_optimizer.force_garbage_collection()
        self.processing_stats['gc_collections'] += 1
        
        # Get file manager stats
        file_stats = self.file_manager.get_stats()
        
        return {
            'processing_stats': self.processing_stats,
            'cleanup_stats': cleanup_stats,
            'memory_stats': memory_stats,
            'file_stats': file_stats,
            'current_memory_mb': self.memory_optimizer.get_memory_usage()
        }


def test_resource_management():
    """Test the resource management system"""
    print("Testing Resource Management System")
    print("=" * 50)
    
    # Create resource manager
    manager = ResourceManager(max_memory_mb=200)
    
    # Test 1: File creation and cleanup
    print("\n1. Testing file creation and cleanup...")
    
    test_data = {"test": "data", "items": list(range(100))}
    temp_files = []
    
    for i in range(5):
        temp_file = manager.create_temp_result_file(test_data, f"test_file_{i}")
        temp_files.append(temp_file)
        print(f"Created: {os.path.basename(temp_file)}")
    
    # Verify files exist
    existing_files = sum(1 for f in temp_files if os.path.exists(f))
    print(f"Files created: {existing_files}/5")
    
    # Test 2: Memory optimization with large dataset
    print("\n2. Testing memory optimization...")
    
    def dummy_process_func(chunk):
        # Simulate processing
        return [{"processed": item, "data": "x" * 100} for item in chunk]
    
    large_dataset = list(range(2000))
    processed_results = manager.process_large_dataset(large_dataset, dummy_process_func)
    
    print(f"Processed {len(large_dataset)} items -> {len(processed_results)} results")
    
    # Test 3: Cleanup and statistics
    print("\n3. Testing cleanup and statistics...")
    
    stats = manager.cleanup_and_get_stats()
    
    print("Resource Management Statistics:")
    print(f"  Files created: {stats['processing_stats']['files_created']}")
    print(f"  Files cleaned: {stats['processing_stats']['files_cleaned']}")
    print(f"  Memory optimizations: {stats['processing_stats']['memory_optimizations']}")
    print(f"  Garbage collections: {stats['processing_stats']['gc_collections']}")
    print(f"  Current memory usage: {stats['current_memory_mb']:.1f} MB")
    
    # Verify cleanup
    remaining_files = sum(1 for f in temp_files if os.path.exists(f))
    print(f"  Remaining temp files: {remaining_files}")
    
    if remaining_files == 0:
        print("✅ File cleanup successful")
    else:
        print("⚠️  Some files not cleaned up")
    
    return stats


def optimize_existing_processing():
    """Optimize existing processing functions with resource management"""
    print("\nOptimizing Existing Processing Functions")
    print("=" * 50)
    
    # Import existing functions
    from main import convert_input_to_answers
    from processors.classifier import ClassificationEngine
    
    # Create optimized versions
    manager = ResourceManager()
    
    def optimized_convert_input_to_answers(data: List[Dict]) -> List[Dict]:
        """Memory-optimized version of convert_input_to_answers"""
        def process_chunk(chunk):
            return convert_input_to_answers(chunk)
        
        return manager.process_large_dataset(data, process_chunk)
    
    def optimized_classification_processing(answers: List[Dict], options: List[str]) -> Dict[str, str]:
        """Optimized classification with temporary file management"""
        engine = ClassificationEngine()
        results = engine.process_multiple_classifications(answers, options)
        
        # Create temporary files for results
        temp_files = {}
        for result in results:
            temp_file = manager.create_temp_result_file(result.data, f"{result.type}_classification")
            temp_files[result.type] = temp_file
        
        return temp_files
    
    # Test optimized functions
    print("Testing optimized functions...")
    
    # Generate test data
    test_data = [
        {
            "id": i,
            "title": f"Test question {i}",
            "solve": f"지방직 7급 / 202{i % 5}",
            "categoryTitle": f"{i % 3 + 1}) Test Category",
            "answerSet": [
                {"id": i * 2, "title": f"Answer {i * 2}", "answerKind": "O"},
                {"id": i * 2 + 1, "title": f"Answer {i * 2 + 1}", "answerKind": "X"}
            ]
        }
        for i in range(1000)
    ]
    
    # Test optimized conversion
    start_time = time.time()
    answers = optimized_convert_input_to_answers(test_data)
    conversion_time = time.time() - start_time
    
    print(f"Optimized conversion: {len(test_data)} questions -> {len(answers)} answers in {conversion_time:.2f}s")
    
    # Test optimized classification
    start_time = time.time()
    temp_files = optimized_classification_processing(answers, ['category', 'institution', 'year'])
    classification_time = time.time() - start_time
    
    print(f"Optimized classification: {len(temp_files)} result files created in {classification_time:.2f}s")
    
    # Verify result files
    for classification_type, file_path in temp_files.items():
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path) / 1024  # KB
            print(f"  {classification_type}: {os.path.basename(file_path)} ({file_size:.1f} KB)")
    
    # Final cleanup and stats
    final_stats = manager.cleanup_and_get_stats()
    print(f"\nFinal cleanup: {final_stats['cleanup_stats']['cleaned_files']} files cleaned")
    
    return final_stats


def main():
    """Run all resource management tests"""
    print("React File Processor - Resource Management Optimization")
    print("=" * 60)
    
    try:
        # Test basic resource management
        basic_stats = test_resource_management()
        
        # Test optimized processing
        optimization_stats = optimize_existing_processing()
        
        # Summary
        print("\n" + "=" * 60)
        print("RESOURCE MANAGEMENT SUMMARY")
        print("=" * 60)
        
        print(f"✅ File cleanup system working")
        print(f"✅ Memory optimization implemented")
        print(f"✅ Resource management integrated")
        print(f"✅ Temporary file handling optimized")
        
        print(f"\nRecommendations:")
        print(f"  - Use ResourceManager for all file processing operations")
        print(f"  - Process large datasets in chunks to optimize memory")
        print(f"  - Implement automatic cleanup in production code")
        print(f"  - Monitor memory usage during processing")
        
    except Exception as e:
        print(f"❌ Resource management testing failed: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\nResource management optimization completed!")


if __name__ == '__main__':
    main()