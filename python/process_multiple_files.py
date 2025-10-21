"""
Multiple file processing module
Contains the process_multiple_files function that was separated from app.py
Currently not in use.
"""

import os
import json
import uuid
import base64
from datetime import datetime
from typing import Dict, List, Any
from collections import defaultdict
from flask import request, jsonify
from dataclasses import dataclass

from remove_similarity_duplicates import SimilarityDeduplicator
from optimize_file_cleanup import ResourceManager


@dataclass
class ClassificationResult:
    id: str
    type: str
    filename: str
    data: Any
    created_at: datetime
    
    def to_dict(self):
        return {
            'type': self.type,
            'filename': self.filename,
            'download_id': self.id
        }


def process_multiple_files_handler(app, resource_manager, process_file_data, classify_by_institution, classify_by_year):
    """
    Process multiple uploaded files with selected classification options
    
    Expected JSON payload:
    {
        "files": [
            {
                "file_data": "base64_encoded_json_content",
                "filename": "file1.json"
            },
            {
                "file_data": "base64_encoded_json_content", 
                "filename": "file2.json"
            }
        ],
        "options": ["category", "institution", "year"]
    }
    
    Returns:
    {
        "success": true,
        "results": [
            {
                "type": "category",
                "filename": "combined_category_classification.json",
                "download_id": "uuid"
            }
        ],
        "processed_items": 2468,
        "original_questions": 1134,
        "files_processed": 2
    }
    """
    try:
        # Validate request
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_REQUEST',
                    'message': 'Request must be JSON',
                    'details': 'Content-Type must be application/json'
                }
            }), 400
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['files', 'options']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'MISSING_FIELD',
                        'message': f'Missing required field: {field}',
                        'details': f'The field "{field}" is required in the request body'
                    }
                }), 400
        
        files = data['files']
        options = data['options']
        
        # Validate files array
        if not isinstance(files, list) or not files:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_FILES',
                    'message': 'At least one file must be provided',
                    'details': 'The "files" field must be a non-empty array'
                }
            }), 400
        
        # Validate file limit
        max_files = 10
        if len(files) > max_files:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'TOO_MANY_FILES',
                    'message': f'Too many files: {len(files)} (max: {max_files})',
                    'details': f'Maximum {max_files} files can be processed at once'
                }
            }), 400
        
        # Validate each file
        for i, file_info in enumerate(files):
            if not isinstance(file_info, dict):
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'INVALID_FILE_FORMAT',
                        'message': f'File {i+1} must be an object',
                        'details': 'Each file must have "file_data" and "filename" fields'
                    }
                }), 400
            
            if 'file_data' not in file_info or 'filename' not in file_info:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'MISSING_FILE_FIELDS',
                        'message': f'File {i+1} missing required fields',
                        'details': 'Each file must have "file_data" and "filename" fields'
                    }
                }), 400
        
        # Validate options
        valid_options = {'category', 'institution', 'year', 'flatten'}
        
        if not isinstance(options, list) or not options:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_OPTIONS',
                    'message': 'At least one processing option must be selected',
                    'details': f'Valid options are: {", ".join(valid_options)}'
                }
            }), 400
        
        invalid_options = set(options) - valid_options
        if invalid_options:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_OPTIONS',
                    'message': f'Invalid processing options: {", ".join(invalid_options)}',
                    'details': f'Valid options are: {", ".join(valid_options)}'
                }
            }), 400
        
        # Process all files and combine data
        combined_data = []
        total_original_questions = 0
        total_stats = {
            'original_questions': 0,
            'original_answers': 0,
            'result_questions': 0,
            'result_answers': 0,
            'duplicate_count': 0,
            'removed_duplicate_answers': 0
        }
        
        app.logger.info(f"Processing {len(files)} files with options: {options}")
        
        for i, file_info in enumerate(files):
            try:
                app.logger.info(f"Processing file {i+1}/{len(files)}: {file_info['filename']}")
                
                # Process individual file
                file_result = process_file_data(
                    file_data=file_info['file_data'],
                    filename=file_info['filename'],
                    options=['flatten']  # Always flatten for combining
                )
                
                # Get flattened data from stored results
                if hasattr(app, 'stored_results'):
                    for result_id, result in app.stored_results.items():
                        if result.type == 'flatten':
                            combined_data.extend(result.data)
                            # Clean up individual flatten result
                            del app.stored_results[result_id]
                            break
                
                # Accumulate statistics
                if 'statistics' in file_result:
                    stats = file_result['statistics']
                    for key in total_stats:
                        total_stats[key] += stats.get(key, 0)
                
                total_original_questions += file_result.get('original_questions', 0)
                
            except Exception as e:
                app.logger.error(f"Error processing file {i+1} ({file_info['filename']}): {str(e)}")
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'FILE_PROCESSING_ERROR',
                        'message': f'Error processing file {i+1}: {file_info["filename"]}',
                        'details': str(e)
                    }
                }), 400
        
        app.logger.info(f"Combined {len(combined_data)} items from {len(files)} files")
        
        # Apply classifications to combined data
        results_data = {}
        
        if 'institution' in options:
            results_data['institution'] = classify_by_institution(combined_data)
        
        if 'year' in options:
            results_data['year'] = classify_by_year(combined_data)
        
        # Create similarity processor for category classification if needed
        if 'category' in options:
            try:
                temp_dir = resource_manager.file_manager.create_temp_dir()
                similarity_processor = SimilarityDeduplicator(
                    input_file=None,
                    output_dir=temp_dir,
                    threshold=0.8
                )
                _, similar_groups = similarity_processor.process_similarity_from_data(combined_data)
                results_data['category'] = similar_groups
            except Exception as e:
                app.logger.warning(f"Category classification failed: {str(e)}")
        
        # Generate API results
        api_results = []
        
        for option in options:
            if option in results_data:
                download_id = str(uuid.uuid4())
                
                # Generate combined filename
                if len(files) == 1:
                    base_filename = os.path.splitext(files[0]['filename'])[0]
                else:
                    base_filename = f"combined_{len(files)}_files"
                
                if option == 'institution':
                    result_filename = f"{base_filename}_기관별.json"
                elif option == 'year':
                    result_filename = f"{base_filename}_연도별.json"
                elif option == 'category':
                    result_filename = f"{base_filename}_카테고리별.json"
                else:
                    result_filename = f"{base_filename}_{option}.json"
                
                # Store result
                result = ClassificationResult(
                    id=download_id,
                    type=option,
                    filename=result_filename,
                    data=results_data[option],
                    created_at=datetime.now()
                )
                
                if not hasattr(app, 'stored_results'):
                    app.stored_results = {}
                app.stored_results[download_id] = result
                
                api_results.append(result.to_dict())
        
        app.logger.info(f"Multiple file processing completed: {len(files)} files -> {len(combined_data)} combined items")
        
        return jsonify({
            'success': True,
            'results': api_results,
            'processed_items': len(combined_data),
            'original_questions': total_original_questions,
            'files_processed': len(files),
            'statistics': total_stats
        })
        
    except Exception as e:
        app.logger.error(f"Unexpected error in process_multiple_files: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An unexpected error occurred',
                'details': 'Please try again or contact support'
            }
        }), 500