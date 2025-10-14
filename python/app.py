"""
Flask API server for React File Processor
Provides endpoints for file processing and downloads
"""

import os
import json
import uuid
import base64
import tempfile
from datetime import datetime
from typing import Dict, List, Any, Optional
from flask import Flask, request, jsonify, send_file, abort
from flask_cors import CORS
from werkzeug.exceptions import BadRequest

from main import convert_input_to_answers
from remove_similarity_duplicates import SimilarityDeduplicator
from processors.classifier import ClassificationEngine


app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend communication

# Global classification engine for managing results
classification_engine = ClassificationEngine()


class ProcessingError(Exception):
    """Custom exception for processing errors"""
    pass


def validate_json_data(data: Any) -> List[Dict[str, Any]]:
    """
    Validate that the input data is a valid JSON array of question objects
    
    Args:
        data: The data to validate
        
    Returns:
        List of validated question objects
        
    Raises:
        ProcessingError: If data is invalid
    """
    if not isinstance(data, list):
        raise ProcessingError("Input data must be a JSON array")
    
    if not data:
        raise ProcessingError("Input data cannot be empty")
    
    # Basic validation of question structure
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            raise ProcessingError(f"Item {i} must be an object")
        
        required_fields = ['id', 'title']
        for field in required_fields:
            if field not in item:
                raise ProcessingError(f"Item {i} missing required field: {field}")
    
    return data


def process_file_data(file_data: str, filename: str, options: List[str]) -> Dict[str, Any]:
    """
    Process uploaded file data with selected classification options
    
    Args:
        file_data: Base64 encoded JSON file content
        filename: Original filename
        options: List of classification options ['category', 'institution', 'year']
        
    Returns:
        Dictionary with processing results
        
    Raises:
        ProcessingError: If processing fails
    """
    try:
        # Decode base64 data
        json_content = base64.b64decode(file_data).decode('utf-8')
        input_data = json.loads(json_content)
        
        # Validate input data
        validated_data = validate_json_data(input_data)
        
        # Convert to answers format with enhanced fields
        answers = convert_input_to_answers(validated_data)
        
        # Create similarity processor for category classification if needed
        similarity_processor = None
        if 'category' in options:
            similarity_processor = SimilarityDeduplicator(
                input_file=None,
                output_dir=tempfile.gettempdir(),
                threshold=0.8
            )
        
        # Process multiple classifications using the engine
        classification_results = classification_engine.process_multiple_classifications(
            data=answers,
            options=options,
            similarity_processor=similarity_processor
        )
        
        # Convert results to API format
        results = [result.to_dict() for result in classification_results]
        
        return {
            'success': True,
            'results': results,
            'processed_items': len(answers),
            'original_questions': len(validated_data)
        }
        
    except json.JSONDecodeError as e:
        raise ProcessingError(f"Invalid JSON format: {str(e)}")
    except Exception as e:
        raise ProcessingError(f"Processing failed: {str(e)}")


@app.route('/api/process', methods=['POST'])
def process_file():
    """
    Process uploaded file with selected classification options
    
    Expected JSON payload:
    {
        "file_data": "base64_encoded_json_content",
        "filename": "original_filename.json",
        "options": ["category", "institution", "year"]
    }
    
    Returns:
    {
        "success": true,
        "results": [
            {
                "type": "category",
                "filename": "category_classification.json",
                "download_id": "uuid"
            }
        ],
        "processed_items": 1234,
        "original_questions": 567
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
        required_fields = ['file_data', 'filename', 'options']
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
        
        # Validate options
        valid_options = {'category', 'institution', 'year'}
        options = data['options']
        
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
        
        # Process the file
        result = process_file_data(
            file_data=data['file_data'],
            filename=data['filename'],
            options=options
        )
        
        return jsonify(result)
        
    except ProcessingError as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'PROCESSING_ERROR',
                'message': str(e),
                'details': 'File processing failed'
            }
        }), 400
        
    except Exception as e:
        app.logger.error(f"Unexpected error in process_file: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An unexpected error occurred',
                'details': 'Please try again or contact support'
            }
        }), 500


@app.route('/api/download/<download_id>', methods=['GET'])
def download_file(download_id: str):
    """
    Download processed file by ID
    
    Args:
        download_id: UUID of the processed file
        
    Returns:
        JSON file download or error response
    """
    try:
        # Check if download ID exists
        result = classification_engine.get_result(download_id)
        if result is None:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'FILE_NOT_FOUND',
                    'message': 'Download ID not found',
                    'details': 'The requested file may have expired or does not exist'
                }
            }), 404
        
        # Create temporary file for download
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as temp_file:
            json.dump(result.data, temp_file, ensure_ascii=False, indent=2)
            temp_file_path = temp_file.name
        
        try:
            # Send file and clean up
            response = send_file(
                temp_file_path,
                as_attachment=True,
                download_name=result.filename,
                mimetype='application/json'
            )
            
            # Clean up temporary file after sending
            @response.call_on_close
            def cleanup():
                try:
                    os.unlink(temp_file_path)
                    # Remove from classification engine after successful download
                    classification_engine.remove_result(download_id)
                except Exception as e:
                    app.logger.error(f"Cleanup error: {str(e)}")
            
            return response
            
        except Exception as e:
            # Clean up temp file if send_file fails
            try:
                os.unlink(temp_file_path)
            except:
                pass
            raise e
            
    except Exception as e:
        app.logger.error(f"Download error: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'DOWNLOAD_ERROR',
                'message': 'Failed to download file',
                'details': str(e)
            }
        }), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    stats = classification_engine.get_stats()
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'classification_stats': stats
    })


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'success': False,
        'error': {
            'code': 'NOT_FOUND',
            'message': 'Endpoint not found',
            'details': 'The requested API endpoint does not exist'
        }
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        'success': False,
        'error': {
            'code': 'INTERNAL_ERROR',
            'message': 'Internal server error',
            'details': 'An unexpected error occurred on the server'
        }
    }), 500


if __name__ == '__main__':
    # Development server
    app.run(debug=True, host='0.0.0.0', port=5000)