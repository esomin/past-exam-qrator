"""
Classification engine for different grouping options
"""

import uuid
import tempfile
import gc
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
from datetime import datetime

from .solve_parser import SolveInfo


class ClassificationResult:
    """Container for classification results"""
    
    def __init__(self, classification_type: str, data: Dict[str, Any], filename: str):
        self.type = classification_type
        self.data = data
        self.filename = filename
        self.id = str(uuid.uuid4())
        self.created_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        return {
            'type': self.type,
            'filename': self.filename,
            'download_id': self.id
        }


class ClassificationEngine:
    """Handles multiple simultaneous data classifications with temporary file management"""
    
    def __init__(self):
        self.temp_results: Dict[str, ClassificationResult] = {}
    
    def classify_by_category(self, data: List[Dict[str, Any]], 
                           similarity_processor=None) -> Dict[str, Any]:
        """
        Group data by category using similarity-based deduplication
        
        Args:
            data: List of answer items
            similarity_processor: SimilarityDeduplicator instance for processing
            
        Returns:
            Nested dictionary grouped by category1 and category2
        """
        if similarity_processor is None:
            # Simple category grouping without similarity processing
            result = defaultdict(lambda: defaultdict(list))
            for item in data:
                category1 = item.get('category1', 'Unknown')
                category2 = item.get('category2', 'Unknown')
                result[category1][category2].append(item)
            
            return {cat1: dict(cat2_dict) for cat1, cat2_dict in result.items()}
        
        # Use similarity processor for advanced grouping
        with tempfile.TemporaryDirectory() as temp_dir:
            similarity_processor.output_dir = temp_dir
            _, similar_groups = similarity_processor.process_similarity_from_data(data)
            
            # Create nested structure from similarity groups
            nested_output = defaultdict(lambda: defaultdict(list))
            for item in similar_groups:
                category1_key = item['category1']
                category2_key = item['category2']
                nested_output[category1_key][category2_key].append(item)
            
            return {cat1: dict(cat2_dict) for cat1, cat2_dict in nested_output.items()}
    
    def classify_by_institution(self, data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group data by institution extracted from solve field"""
        result = defaultdict(list)
        for item in data:
            institution = item.get('institution', 'Unknown')
            result[institution].append(item)
        return dict(result)
    
    def classify_by_year(self, data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group data by year extracted from solve field"""
        result = defaultdict(list)
        for item in data:
            year = item.get('year', 'Unknown')
            result[year].append(item)
        return dict(result)
    
    def process_multiple_classifications(self, 
                                      data: List[Dict[str, Any]], 
                                      options: List[str],
                                      similarity_processor=None) -> List[ClassificationResult]:
        """
        Process multiple classification types simultaneously
        
        Args:
            data: List of answer items with enhanced fields
            options: List of classification types ['category', 'institution', 'year']
            similarity_processor: Optional SimilarityDeduplicator for category processing
            
        Returns:
            List of ClassificationResult objects
        """
        results = []
        
        # Process each classification option
        if 'category' in options:
            category_data = self.classify_by_category(data, similarity_processor)
            result = ClassificationResult(
                classification_type='category',
                data=category_data,
                filename='category_classification.json'
            )
            self.temp_results[result.id] = result
            results.append(result)
        
        if 'institution' in options:
            institution_data = self.classify_by_institution(data)
            result = ClassificationResult(
                classification_type='institution',
                data=institution_data,
                filename='institution_classification.json'
            )
            self.temp_results[result.id] = result
            results.append(result)
        
        if 'year' in options:
            year_data = self.classify_by_year(data)
            result = ClassificationResult(
                classification_type='year',
                data=year_data,
                filename='year_classification.json'
            )
            self.temp_results[result.id] = result
            results.append(result)
        
        return results
    
    def get_result(self, result_id: str) -> Optional[ClassificationResult]:
        """Get classification result by ID"""
        return self.temp_results.get(result_id)
    
    def remove_result(self, result_id: str) -> bool:
        """Remove classification result from temporary storage"""
        if result_id in self.temp_results:
            del self.temp_results[result_id]
            return True
        return False
    
    def cleanup_expired_results(self, max_age_hours: int = 24) -> int:
        """
        Clean up results older than specified hours
        
        Args:
            max_age_hours: Maximum age in hours before cleanup
            
        Returns:
            Number of results cleaned up
        """
        current_time = datetime.now()
        expired_ids = []
        
        for result_id, result in self.temp_results.items():
            age_hours = (current_time - result.created_at).total_seconds() / 3600
            if age_hours > max_age_hours:
                expired_ids.append(result_id)
        
        for result_id in expired_ids:
            del self.temp_results[result_id]
        
        return len(expired_ids)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about stored results"""
        stats = {
            'total_results': len(self.temp_results),
            'by_type': defaultdict(int),
            'oldest_result': None,
            'newest_result': None
        }
        
        if self.temp_results:
            creation_times = [result.created_at for result in self.temp_results.values()]
            stats['oldest_result'] = min(creation_times).isoformat()
            stats['newest_result'] = max(creation_times).isoformat()
            
            for result in self.temp_results.values():
                stats['by_type'][result.type] += 1
        
        stats['by_type'] = dict(stats['by_type'])
        return stats