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


app = Flask(__name__, static_folder='static', static_url_path='')
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


def convert_json_to_markdown(data: Any, exclude_columns: List[str] = None) -> str:
    """Convert JSON data to Markdown format"""
    if exclude_columns is None:
        exclude_columns = []
    
    if not data:
        return "# No Data Available\n\nThe provided data is empty."
    
    # Handle different data structures
    if isinstance(data, dict):
        # If it's a dictionary (grouped data), process each group
        markdown_content = []
        
        for group_name, items in data.items():
            markdown_content.append(f"# {group_name}\n")
            
            if isinstance(items, list) and items:
                # Create table from list of items
                table_md = create_markdown_table(items, exclude_columns)
                markdown_content.append(table_md)
            else:
                markdown_content.append("No items in this group.\n")
            
            markdown_content.append("\n---\n")
        
        return "\n".join(markdown_content)
    
    elif isinstance(data, list):
        # If it's a list, create a single table
        if not data:
            return "# No Data Available\n\nThe provided list is empty."
        
        markdown_content = ["# Data\n"]
        table_md = create_markdown_table(data, exclude_columns)
        markdown_content.append(table_md)
        
        return "\n".join(markdown_content)
    
    else:
        return f"# Data\n\n```json\n{json.dumps(data, ensure_ascii=False, indent=2)}\n```"


def create_markdown_table(items: List[Dict], exclude_columns: List[str] = None) -> str:
    """Create a markdown table from a list of dictionaries"""
    if exclude_columns is None:
        exclude_columns = []
    
    if not items:
        return "No data available.\n"
    
    # Get all unique keys from all items, excluding specified columns
    all_keys = set()
    for item in items:
        if isinstance(item, dict):
            all_keys.update(item.keys())
    
    # Remove excluded columns
    columns = [key for key in all_keys if key not in exclude_columns]
    
    if not columns:
        return "No columns to display after filtering.\n"
    
    # Sort columns for consistent output, but put 'id' first if it exists
    if 'id' in columns:
        # Remove 'id' from the list and sort the rest
        columns.remove('id')
        columns.sort()
        # Put 'id' at the beginning
        columns = ['id'] + columns
    else:
        columns.sort()
    
    # Create table header
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"
    
    # Create table rows
    rows = []
    for item in items:
        if isinstance(item, dict):
            row_values = []
            for col in columns:
                value = item.get(col, "")
                # Clean up the value for markdown
                if value is None:
                    value = ""
                else:
                    value = str(value).replace("|", "\\|").replace("\n", " ").replace("\r", "")
                    # Limit cell content length
                    if len(value) > 100:
                        value = value[:97] + "..."
                row_values.append(value)
            
            row = "| " + " | ".join(row_values) + " |"
            rows.append(row)
    
    # Combine all parts
    table_parts = [header, separator] + rows
    return "\n".join(table_parts) + "\n"


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
    from add_category2_to_qn import add_category2_to_data
    
    # category2 추가
    data_with_category2 = add_category2_to_data(input_data)
    
    flattened_data = []
    seen_ids = set()  # ID 중복 체크용
    seen_questions = set()  # 문제 중복 체크용
    
    # 통계 정보
    original_questions = len(data_with_category2)
    original_answers = 0
    removed_duplicate_answers = 0  # 제거된 중복 선택지 수
    
    for question in data_with_category2:
        # question 레벨 속성 추출
        question_data = {
            "title": question.get("title"),
            "text": question.get("text"),
            "titleType": question.get("titleType"),
            "solve": question.get("solve"),
            "categoryTitle": question.get("categoryTitle"),
            "category2": question.get("category2")  # category2 추가
        }
        
        # solve에서 기관과 연도 추출
        institution = extract_institution_from_solve(question_data["solve"] or "")
        year = extract_year_from_solve(question_data["solve"] or "")
        
        # answerSet의 각 항목 처리
        answer_set = question.get("answerSet", [])
        original_answers += len(answer_set)
        
        for answer in answer_set:
            # ID 중복 체크 (선택지 중복)
            answer_id = answer.get("id")
            if answer_id in seen_ids:
                removed_duplicate_answers += 1
                continue  # 중복된 ID는 건너뛰기
            seen_ids.add(answer_id)
            
            # answerSet 항목 속성 추출
            answer_data = {
                "id": answer_id,
                "title": answer.get("title"),
                "commentary": answer.get("commentary"),
                "answerKind": answer.get("answerKind")
            }
            
            # isCorrect 결정
            is_correct = determine_is_correct(
                question_data["titleType"], 
                answer_data["answerKind"]
            )
            
            # 최종 플래튼 항목 생성 - 개선된 컬럼 순서
            # question 필드에 title과 text 합치기
            question_title = question_data["title"] or ""
            question_text = question_data["text"] or ""
            combined_question = f"{question_title} {question_text}".strip()
            
            flattened_item = {
                # Primary Information First
                "id": answer_data["id"],
                "question": combined_question,
                "answer": answer_data["title"],
                
                # Classification & Context
                "category1": question_data["categoryTitle"],
                "category2": question_data["category2"],
                "institution": institution,
                "year": year,
                
                # Answer Analysis
                "answerKind": answer_data["answerKind"],
                "isCorrect": is_correct,
                "commentary": answer_data["commentary"]
            }
            
            flattened_data.append(flattened_item)
            
            # 문제 제목 추가 (중복 문제 계산용)
            seen_questions.add(question_data["title"])
    
    # category1로 정렬
    flattened_data.sort(key=lambda x: (x.get('category1', ''), x.get('id', 0)))
    
    # 결과 문제 수 계산 (고유한 question_title 개수)
    unique_questions = len(seen_questions)
    
    # 제거된 동일 문제 수 계산
    removed_duplicate_questions = original_questions - unique_questions
    
    stats = {
        'original_questions': original_questions,
        'original_answers': original_answers,
        'result_questions': unique_questions,
        'result_answers': len(flattened_data),
        'duplicate_count': removed_duplicate_questions,  # 제거된 동일 문제 수
        'removed_duplicate_answers': removed_duplicate_answers  # 제거된 동일 선택지 수
    }
    
    return flattened_data, stats


def classify_by_institution(data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """플래튼된 데이터를 기관별로 분류"""
    institution_groups = defaultdict(list)
    
    for item in data:
        institution = item.get('institution', 'Unknown')
        institution_groups[institution].append(item)
    
    # 각 기관별로 category1, category2, ID순 정렬
    for institution in institution_groups:
        institution_groups[institution].sort(key=lambda x: (
            x.get('category1', ''),  # 1차 정렬: category1
            x.get('category2', ''),      # 2차 정렬: category2
            x.get('id', 0)               # 3차 정렬: id
        ))
    
    return dict(institution_groups)


def classify_by_year(data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """플래튼된 데이터를 연도별로 분류"""
    year_groups = defaultdict(list)
    
    for item in data:
        year = item.get('year', 'Unknown')
        year_groups[year].append(item)
    
    # 각 연도별로 category1, category2, ID순 정렬
    for year in year_groups:
        year_groups[year].sort(key=lambda x: (
            x.get('category1', ''),  # 1차 정렬: category1
            x.get('category2', ''),      # 2차 정렬: category2
            x.get('id', 0)               # 3차 정렬: id
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
            flattened_data, _ = flatten_original_data(chunk)
            return flattened_data
        
        # Process in chunks if dataset is large
        if len(validated_data) > 5000:
            app.logger.info(f"Large dataset detected ({len(validated_data)} questions), processing in chunks")
            flattened_data = resource_manager.process_large_dataset(validated_data, convert_chunk)
            # 청크 처리 시 통계는 별도 계산
            original_answers = sum(len(q.get("answerSet", [])) for q in validated_data)
            unique_questions = len(set(item.get('question', '') for item in flattened_data))
            removed_duplicate_answers = original_answers - len(flattened_data)
            removed_duplicate_questions = len(validated_data) - unique_questions
            stats = {
                'original_questions': len(validated_data),
                'original_answers': original_answers,
                'result_questions': unique_questions,
                'result_answers': len(flattened_data),
                'duplicate_count': removed_duplicate_questions,
                'removed_duplicate_answers': removed_duplicate_answers
            }
        else:
            flattened_data, stats = flatten_original_data(validated_data)
        
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
                
                # 파일명 생성 - 한국어 접미사 사용
                base_filename = os.path.splitext(filename)[0]
                if option == 'institution':
                    result_filename = f"{base_filename}_기관별.json"
                elif option == 'year':
                    result_filename = f"{base_filename}_연도별.json"
                else:
                    result_filename = f"{base_filename}_{option}.json"
                
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
                    filename=result_filename,
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
                base_filename = os.path.splitext(filename)[0]
                category_filename = f"{base_filename}_category.json"
                
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
            'file_size_mb': file_size_mb,
            'statistics': stats
        }
        
    except json.JSONDecodeError as e:
        raise ProcessingError(f"Invalid JSON format: {str(e)}")
    except MemoryError:
        raise ProcessingError("File too large to process - insufficient memory")
    except Exception as e:
        app.logger.error(f"Processing error: {str(e)}")
        raise ProcessingError(f"Processing failed: {str(e)}")


@app.route('/api/process-multiple', methods=['POST'])
def process_multiple_files():
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


@app.route('/api/data/<download_id>', methods=['GET'])
def get_data(download_id: str):
    """
    Get processed data by ID (for markdown conversion)
    
    Args:
        download_id: UUID of the processed file
        
    Returns:
        JSON data or error response
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
        
        # Return the data directly as JSON
        return jsonify(result.data)
            
    except Exception as e:
        app.logger.error(f"Data fetch error: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'DATA_FETCH_ERROR',
                'message': 'Failed to fetch data',
                'details': str(e)
            }
        }), 500


@app.route('/api/test-download-multiple', methods=['POST'])
def test_download_multiple():
    """Test endpoint for download-multiple"""
    return jsonify({
        'success': True,
        'message': 'Test endpoint working',
        'method': request.method,
        'path': request.path
    })

@app.route('/api/download-multiple', methods=['POST'])
def download_multiple_files():
    """
    Download multiple processed files as a ZIP archive
    
    Expected JSON payload:
    {
        "result_ids": ["uuid1", "uuid2", "uuid3"],
        "archive_name": "processed_files.zip"
    }
    
    Returns:
        ZIP file download or error response
    """
    try:
        app.logger.info(f"Received download-multiple request from {request.remote_addr}")
        app.logger.info(f"Request method: {request.method}")
        app.logger.info(f"Request content type: {request.content_type}")
        
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
        if 'result_ids' not in data:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'MISSING_FIELD',
                    'message': 'Missing required field: result_ids',
                    'details': 'The field "result_ids" is required in the request body'
                }
            }), 400
        
        result_ids = data['result_ids']
        archive_name = data.get('archive_name', 'processed_files.zip')
        
        # Validate result_ids
        if not isinstance(result_ids, list) or not result_ids:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_RESULT_IDS',
                    'message': 'result_ids must be a non-empty array',
                    'details': 'Provide at least one result ID to download'
                }
            }), 400
        
        # Check if all result IDs exist
        if not hasattr(app, 'stored_results'):
            return jsonify({
                'success': False,
                'error': {
                    'code': 'NO_RESULTS',
                    'message': 'No processed results available',
                    'details': 'No files have been processed yet'
                }
            }), 404
        
        missing_ids = []
        valid_result_ids = []
        
        for result_id in result_ids:
            # Check if this is a markdown request (result_id ends with '_md')
            if result_id.endswith('_md'):
                # For markdown requests, check if the original ID exists
                original_id = result_id[:-3]  # Remove '_md' suffix
                if original_id in app.stored_results:
                    valid_result_ids.append(result_id)
                else:
                    missing_ids.append(result_id)
            else:
                # For regular requests, check if the ID exists directly
                if result_id in app.stored_results:
                    valid_result_ids.append(result_id)
                else:
                    missing_ids.append(result_id)
        
        if missing_ids:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'FILES_NOT_FOUND',
                    'message': f'Some files not found: {len(missing_ids)} missing',
                    'details': f'Missing IDs: {", ".join(missing_ids[:5])}{"..." if len(missing_ids) > 5 else ""}'
                }
            }), 404
        
        if not valid_result_ids:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'NO_VALID_FILES',
                    'message': 'No valid files to download',
                    'details': 'All requested files are invalid or expired'
                }
            }), 404
        
        # Create ZIP archive
        import zipfile
        import io
        
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for result_id in valid_result_ids:
                
                try:
                    # Check if this is a markdown request (result_id ends with '_md')
                    if result_id.endswith('_md'):
                        # This is a markdown conversion request
                        original_id = result_id[:-3]  # Remove '_md' suffix
                        if original_id in app.stored_results:
                            original_result = app.stored_results[original_id]
                            
                            # Determine exclude columns based on result type
                            exclude_columns = []
                            if 'year' in original_result.type:
                                exclude_columns = ['year']
                            elif 'institution' in original_result.type:
                                exclude_columns = ['institution']
                            
                            # Convert to markdown
                            markdown_content = convert_json_to_markdown(original_result.data, exclude_columns)
                            markdown_filename = original_result.filename.replace('.json', '.md')
                            
                            # Add markdown file to ZIP
                            zip_file.writestr(markdown_filename, markdown_content.encode('utf-8'))
                        else:
                            app.logger.warning(f"Original result not found for markdown conversion: {original_id}")
                    else:
                        # Regular JSON file
                        if result_id in app.stored_results:
                            result = app.stored_results[result_id]
                            json_content = json.dumps(result.data, ensure_ascii=False, indent=2)
                            zip_file.writestr(result.filename, json_content.encode('utf-8'))
                        else:
                            app.logger.warning(f"Result not found: {result_id}")
                    
                except Exception as e:
                    app.logger.warning(f"Failed to add file {result_id} to ZIP: {str(e)}")
                    continue
        
        zip_buffer.seek(0)
        
        # Validate ZIP content
        if zip_buffer.getvalue() == b'':
            return jsonify({
                'success': False,
                'error': {
                    'code': 'EMPTY_ARCHIVE',
                    'message': 'Failed to create archive',
                    'details': 'No files could be added to the archive'
                }
            }), 500
        
        # Create response with ZIP file
        response = send_file(
            io.BytesIO(zip_buffer.getvalue()),
            as_attachment=True,
            download_name=archive_name,
            mimetype='application/zip'
        )
        
        # Clean up downloaded results after successful bulk download
        @response.call_on_close
        def cleanup():
            try:
                for result_id in result_ids:
                    # For markdown requests, don't delete the original result
                    if result_id.endswith('_md'):
                        continue
                    # Only delete actual stored results
                    if hasattr(app, 'stored_results') and result_id in app.stored_results:
                        del app.stored_results[result_id]
            except Exception as e:
                app.logger.error(f"Cleanup error after bulk download: {str(e)}")
        
        app.logger.info(f"Bulk download completed: {len(valid_result_ids)} files in {archive_name}")
        return response
        
    except Exception as e:
        app.logger.error(f"Bulk download error: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'BULK_DOWNLOAD_ERROR',
                'message': 'Failed to create bulk download',
                'details': str(e)
            }
        }), 500


@app.route('/api/convert-to-markdown/<download_id>', methods=['GET'])
def convert_to_markdown(download_id: str):
    """
    Convert processed JSON data to Markdown format
    
    Args:
        download_id: UUID of the processed file
        
    Query parameters:
        exclude_columns: Comma-separated list of columns to exclude
        
    Returns:
        Markdown file download or error response
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
        
        # Get exclude columns from query parameters
        exclude_columns_param = request.args.get('exclude_columns', '')
        exclude_columns = [col.strip() for col in exclude_columns_param.split(',') if col.strip()]
        
        # Convert to markdown
        markdown_content = convert_json_to_markdown(result.data, exclude_columns)
        
        # Generate markdown filename
        markdown_filename = result.filename.replace('.json', '.md')
        
        # Create temporary file for download
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as temp_file:
            temp_file.write(markdown_content)
            temp_file_path = temp_file.name
        
        try:
            # Send file and clean up
            response = send_file(
                temp_file_path,
                as_attachment=True,
                download_name=markdown_filename,
                mimetype='text/markdown'
            )
            
            # Clean up temporary file after sending
            @response.call_on_close
            def cleanup():
                try:
                    os.unlink(temp_file_path)
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
        app.logger.error(f"Markdown conversion error: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'MARKDOWN_CONVERSION_ERROR',
                'message': 'Failed to convert to markdown',
                'details': str(e)
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


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    """Serve React frontend for all non-API routes"""
    if path.startswith('api/'):
        # API routes should return 404 if not found
        abort(404)
    
    # Try to serve static file first
    if path and os.path.exists(os.path.join(app.static_folder, path)):
        return app.send_static_file(path)
    
    # Fallback to index.html for React routing
    return app.send_static_file('index.html')


if __name__ == '__main__':
    # Development server
    app.run(debug=True, host='0.0.0.0', port=5001)