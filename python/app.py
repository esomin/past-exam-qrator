"""
Flask API server for React File Processor
Provides endpoints for file processing and downloads
"""

import os
import json
import uuid
import base64
import tempfile
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import defaultdict
from flask import Flask, request, jsonify, send_file, abort
from flask_cors import CORS
from werkzeug.exceptions import BadRequest

from remove_similarity_duplicates import SimilarityDeduplicator
from processors.classifier import ClassificationEngine
from optimize_file_cleanup import ResourceManager


app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend communication

# Global classification engine for managing results
classification_engine = ClassificationEngine()

# Global resource manager for memory and file optimization
resource_manager = ResourceManager(max_memory_mb=1000)  # 1GB memory limit


class ProcessingError(Exception):
    """Custom exception for processing errors"""
    pass


def extract_institution_from_solve(solve: str) -> str:
    """solve 필드에서 기관명 추출"""
    if not solve:
        return "Unknown"
    
    # 일반적인 패턴: "기관명 / 연도" 또는 "기관명"
    parts = solve.split('/')
    if parts:
        return parts[0].strip()
    return solve.strip()


def extract_year_from_solve(solve: str) -> str:
    """solve 필드에서 연도 추출"""
    if not solve:
        return "Unknown"
    
    # 4자리 숫자 패턴 찾기
    year_match = re.search(r'\b(20\d{2}|19\d{2})\b', solve)
    if year_match:
        return year_match.group(1)
    return "Unknown"


def determine_is_correct(title_type: str, answer_kind: str) -> Optional[bool]:
    """titleType과 answerKind를 기반으로 isCorrect 값 결정"""
    if title_type == "NEGATIVE" and answer_kind == "X":
        return True
    elif title_type == "POSITIVE" and answer_kind == "O":
        return True
    elif title_type == "NEGATIVE" and answer_kind == "O":
        return False
    elif title_type == "POSITIVE" and answer_kind == "X":
        return False
    else:
        # titleType이 NEGATIVE도 POSITIVE도 아닌 경우
        return None


def flatten_original_data(input_data: List[Dict[str, Any]]) -> tuple[List[Dict[str, Any]], Dict[str, int]]:
    """원본 데이터를 플래튼하여 필요한 속성만 추출하고 통계 정보 반환"""
    flattened_data = []
    seen_ids = set()  # ID 중복 체크용
    
    # 통계 정보
    original_questions = len(input_data)
    original_answers = 0
    duplicate_count = 0
    
    for question in input_data:
        # question 레벨 속성 추출
        question_data = {
            "answerRate": question.get("answerRate"),
            "title": question.get("title"),
            "titleType": question.get("titleType"),
            "solve": question.get("solve"),
            "categoryTitle": question.get("categoryTitle")
        }
        
        # solve에서 기관과 연도 추출
        institution = extract_institution_from_solve(question_data["solve"] or "")
        year = extract_year_from_solve(question_data["solve"] or "")
        
        # answerSet의 각 항목 처리
        answer_set = question.get("answerSet", [])
        original_answers += len(answer_set)
        
        for answer in answer_set:
            # ID 중복 체크
            answer_id = answer.get("id")
            if answer_id in seen_ids:
                duplicate_count += 1
                continue  # 중복된 ID는 건너뛰기
            seen_ids.add(answer_id)
            
            # answerSet 항목 속성 추출
            answer_data = {
                "id": answer_id,
                "answer_title": answer.get("title"),
                "commentary": answer.get("commentary"),
                "answerKind": answer.get("answerKind")
            }
            
            # isCorrect 결정
            is_correct = determine_is_correct(
                question_data["titleType"], 
                answer_data["answerKind"]
            )
            
            # 최종 플래튼 항목 생성 (solve 제거, institution/year 추가)
            flattened_item = {
                # question 속성들
                "answerRate": question_data["answerRate"],
                "question_title": question_data["title"],
                "titleType": question_data["titleType"],
                "categoryTitle": question_data["categoryTitle"],
                "institution": institution,
                "year": year,
                
                # answer 속성들
                "id": answer_data["id"],
                "answer_title": answer_data["answer_title"],
                "commentary": answer_data["commentary"],
                "answerKind": answer_data["answerKind"],
                
                # 계산된 속성
                "isCorrect": is_correct
            }
            
            flattened_data.append(flattened_item)
    
    # categoryTitle로 정렬
    flattened_data.sort(key=lambda x: (x.get('categoryTitle', ''), x.get('id', 0)))
    
    # 결과 문제 수 계산 (고유한 question_title 개수)
    unique_questions = len(set(item.get('question_title', '') for item in flattened_data))
    
    stats = {
        'original_questions': original_questions,
        'original_answers': original_answers,
        'result_questions': unique_questions,
        'result_answers': len(flattened_data),
        'duplicate_count': duplicate_count
    }
    
    return flattened_data, stats


def classify_by_institution(data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """플래튼된 데이터를 기관별로 분류"""
    institution_groups = defaultdict(list)
    
    for item in data:
        institution = item.get('institution', 'Unknown')
        institution_groups[institution].append(item)
    
    # 각 기관별로 categoryTitle, 연도순, ID순 정렬
    for institution in institution_groups:
        institution_groups[institution].sort(key=lambda x: (
            x.get('categoryTitle', ''), 
            x.get('year', 'Unknown'), 
            x.get('id', 0)
        ))
    
    return dict(institution_groups)


def classify_by_year(data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """플래튼된 데이터를 연도별로 분류"""
    year_groups = defaultdict(list)
    
    for item in data:
        year = item.get('year', 'Unknown')
        year_groups[year].append(item)
    
    # 각 연도별로 categoryTitle, ID순 정렬
    for year in year_groups:
        year_groups[year].sort(key=lambda x: (
            x.get('categoryTitle', ''), 
            x.get('id', 0)
        ))
    
    # 연도순으로 정렬된 결과 생성
    sorted_years = sorted(year_groups.keys(), key=lambda x: x if x != 'Unknown' else '0000')
    result = {year: year_groups[year] for year in sorted_years}
    
    return result


def convert_input_to_answers(input_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """기존 호환성을 위한 래퍼 함수 - 플래튼된 데이터 반환"""
    flattened_data, _ = flatten_original_data(input_data)
    return flattened_data


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
    Memory-optimized version with resource management
    
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
        # Check file size before processing
        file_size_mb = len(file_data) * 3 / 4 / 1024 / 1024  # Estimate decoded size
        app.logger.info(f"Processing file: {filename} (~{file_size_mb:.1f}MB)")
        
        # Implement file size limits
        max_file_size_mb = 100  # 100MB limit
        if file_size_mb > max_file_size_mb:
            raise ProcessingError(f"File too large: {file_size_mb:.1f}MB (max: {max_file_size_mb}MB)")
        
        # Decode base64 data
        json_content = base64.b64decode(file_data).decode('utf-8')
        input_data = json.loads(json_content)
        
        # Validate input data
        validated_data = validate_json_data(input_data)
        
        # Check data size limits
        max_questions = 100000  # 100K questions limit
        if len(validated_data) > max_questions:
            raise ProcessingError(f"Too many questions: {len(validated_data)} (max: {max_questions})")
        
        # Memory-optimized conversion using resource manager
        def convert_chunk(chunk):
            return flatten_original_data(chunk)
        
        # Process in chunks if dataset is large
        if len(validated_data) > 5000:
            app.logger.info(f"Large dataset detected ({len(validated_data)} questions), processing in chunks")
            flattened_data = resource_manager.process_large_dataset(validated_data, convert_chunk)
        else:
            flattened_data = flatten_original_data(validated_data)
        
        # 분류 옵션에 따라 다른 처리
        results_data = {}
        
        if 'flatten' in options:
            results_data['flatten'] = flattened_data
        
        if 'institution' in options:
            results_data['institution'] = classify_by_institution(flattened_data)
        
        if 'year' in options:
            results_data['year'] = classify_by_year(flattened_data)
        
        # 기존 카테고리 분류를 위한 답변 형태 변환 (필요시)
        answers = flattened_data  # 기본적으로 플래튼된 데이터 사용
        
        # Create similarity processor for category classification if needed
        similarity_processor = None
        if 'category' in options:
            # Use temporary directory managed by resource manager
            temp_dir = resource_manager.file_manager.create_temp_dir()
            similarity_processor = SimilarityDeduplicator(
                input_file=None,
                output_dir=temp_dir,
                threshold=0.8
            )
        
        # 새로운 분류 결과를 API 형식으로 변환
        api_results = []
        
        for option in options:
            if option in results_data:
                # 각 분류 결과를 저장하고 다운로드 ID 생성
                download_id = str(uuid.uuid4())
                filename = f"{os.path.splitext(filename)[0]}_{option}.json"
                
                # 분류 엔진에 결과 저장 (임시)
                from dataclasses import dataclass
                from datetime import datetime
                
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
                
                result = ClassificationResult(
                    id=download_id,
                    type=option,
                    filename=filename,
                    data=results_data[option],
                    created_at=datetime.now()
                )
                
                # 결과 저장 (classification_engine 대신 간단한 저장소 사용)
                if not hasattr(app, 'stored_results'):
                    app.stored_results = {}
                app.stored_results[download_id] = result
                
                api_results.append(result.to_dict())
        
        # 기존 카테고리 분류 처리 (필요시)
        if 'category' in options and similarity_processor:
            try:
                _, similar_groups = similarity_processor.process_similarity_from_data(answers)
                
                download_id = str(uuid.uuid4())
                category_filename = f"{os.path.splitext(filename)[0]}_category.json"
                
                result = ClassificationResult(
                    id=download_id,
                    type='category',
                    filename=category_filename,
                    data=similar_groups,
                    created_at=datetime.now()
                )
                
                app.stored_results[download_id] = result
                api_results.append(result.to_dict())
                
            except Exception as e:
                app.logger.warning(f"Category classification failed: {str(e)}")
        
        results = api_results
        
        # Log processing statistics
        app.logger.info(f"Processing completed: {len(validated_data)} questions -> {len(flattened_data)} flattened items")
        app.logger.info(f"Classifications generated: {len(results)}")
        
        return {
            'success': True,
            'results': results,
            'processed_items': len(flattened_data),
            'original_questions': len(validated_data),
            'file_size_mb': file_size_mb
        }
        
    except json.JSONDecodeError as e:
        raise ProcessingError(f"Invalid JSON format: {str(e)}")
    except MemoryError:
        raise ProcessingError("File too large to process - insufficient memory")
    except Exception as e:
        app.logger.error(f"Processing error: {str(e)}")
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
        valid_options = {'category', 'institution', 'year', 'flatten'}
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
        # Check if download ID exists in stored results
        if not hasattr(app, 'stored_results') or download_id not in app.stored_results:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'FILE_NOT_FOUND',
                    'message': 'Download ID not found',
                    'details': 'The requested file may have expired or does not exist'
                }
            }), 404
        
        result = app.stored_results[download_id]
        
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
                    # Remove from stored results after successful download
                    if hasattr(app, 'stored_results') and download_id in app.stored_results:
                        del app.stored_results[download_id]
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
    """Health check endpoint with resource statistics"""
    try:
        resource_stats = resource_manager.cleanup_and_get_stats()
        stored_results_count = len(getattr(app, 'stored_results', {}))
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'stored_results_count': stored_results_count,
            'resource_stats': {
                'current_memory_mb': resource_stats['current_memory_mb'],
                'registered_temp_files': resource_stats['file_stats']['registered_files'],
                'processing_stats': resource_stats['processing_stats']
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'stored_results_count': len(getattr(app, 'stored_results', {})),
            'note': 'Resource manager not available'
        })


@app.route('/api/cleanup', methods=['POST'])
def cleanup_resources():
    """Manual cleanup endpoint for maintenance"""
    try:
        # Clean up expired stored results (older than 1 hour)
        expired_count = 0
        if hasattr(app, 'stored_results'):
            current_time = datetime.now()
            expired_ids = []
            
            for result_id, result in app.stored_results.items():
                if hasattr(result, 'created_at'):
                    age_hours = (current_time - result.created_at).total_seconds() / 3600
                    if age_hours > 1:
                        expired_ids.append(result_id)
            
            for result_id in expired_ids:
                del app.stored_results[result_id]
                expired_count += 1
        
        # Clean up resource manager
        try:
            resource_stats = resource_manager.cleanup_and_get_stats()
            cleanup_stats = {
                'expired_results_cleaned': expired_count,
                'files_cleaned': resource_stats['cleanup_stats']['cleaned_files'],
                'memory_freed': resource_stats['memory_stats']['objects_freed'],
                'current_memory_mb': resource_stats['current_memory_mb']
            }
        except:
            cleanup_stats = {
                'expired_results_cleaned': expired_count,
                'note': 'Resource manager cleanup not available'
            }
        
        return jsonify({
            'success': True,
            'cleanup_stats': cleanup_stats
        })
        
    except Exception as e:
        app.logger.error(f"Cleanup error: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'CLEANUP_ERROR',
                'message': 'Failed to cleanup resources',
                'details': str(e)
            }
        }), 500


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
    app.run(debug=True, host='0.0.0.0', port=5001)