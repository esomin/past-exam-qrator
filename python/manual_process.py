#!/usr/bin/env python3
"""
Flask API /api/process 엔드포인트의 핵심 로직을 터미널에서 수동 실행하는 스크립트

사용법:
python manual_process.py <input_file_path> [options]

예시:
python manual_process.py data/행정학\ 1,2\(원본\).json category
python manual_process.py data/행정학\ 5,6,7\(원본\).json category,institution,year
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any

# 현재 스크립트의 디렉토리를 Python path에 추가
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from main import convert_input_to_answers
from remove_similarity_duplicates import SimilarityDeduplicator
from processors.classifier import ClassificationEngine


def validate_json_data(data: Any) -> List[Dict[str, Any]]:
    """JSON 데이터 유효성 검사"""
    if not isinstance(data, list):
        raise ValueError("Input data must be a JSON array")
    
    if not data:
        raise ValueError("Input data cannot be empty")
    
    # 기본 구조 검증
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            raise ValueError(f"Item {i} must be an object")
        
        required_fields = ['id', 'title']
        for field in required_fields:
            if field not in item:
                raise ValueError(f"Item {i} missing required field: {field}")
    
    return data


def process_file_manual(input_file_path: str, options: List[str], output_dir: str = None, output_prefix: str = None) -> Dict[str, Any]:
    """
    파일을 수동으로 처리하는 함수
    
    Args:
        input_file_path: 입력 JSON 파일 경로
        options: 분류 옵션 리스트 ['category', 'institution', 'year']
        output_dir: 출력 디렉토리 (기본값: 입력 파일과 같은 디렉토리)
        output_prefix: 출력 파일명 접두사 (기본값: 입력 파일명에서 확장자 제거)
    
    Returns:
        처리 결과 딕셔너리
    """
    # 입력 파일 경로 검증
    input_path = Path(input_file_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_file_path}")
    
    # 출력 디렉토리 설정
    if output_dir is None:
        output_dir = input_path.parent
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 출력 파일명 접두사 설정
    if output_prefix is None:
        output_prefix = input_path.stem  # 확장자 제거한 파일명
    
    print(f"Processing file: {input_path}")
    print(f"Output directory: {output_dir}")
    print(f"Output prefix: {output_prefix}")
    print(f"Classification options: {', '.join(options)}")
    
    # 파일 크기 확인
    file_size_mb = input_path.stat().st_size / 1024 / 1024
    print(f"File size: {file_size_mb:.1f}MB")
    
    if file_size_mb > 100:  # 100MB 제한
        raise ValueError(f"File too large: {file_size_mb:.1f}MB (max: 100MB)")
    
    # JSON 파일 로드
    print("Loading JSON file...")
    with open(input_path, 'r', encoding='utf-8') as f:
        input_data = json.load(f)
    
    # 데이터 유효성 검사
    validated_data = validate_json_data(input_data)
    print(f"Loaded {len(validated_data)} questions")
    
    # 질문 수 제한 확인
    max_questions = 100000
    if len(validated_data) > max_questions:
        raise ValueError(f"Too many questions: {len(validated_data)} (max: {max_questions})")
    
    # answers 형태로 변환
    print("Converting to answers format...")
    answers = convert_input_to_answers(validated_data)
    print(f"Converted to {len(answers)} answers")
    
    # 분류 엔진 초기화
    classification_engine = ClassificationEngine()
    
    # 유사도 프로세서 초기화 (category 옵션이 있는 경우)
    similarity_processor = None
    if 'category' in options:
        similarity_processor = SimilarityDeduplicator(
            input_file=None,
            output_dir=str(output_dir),
            threshold=0.8
        )
    
    # 다중 분류 처리
    print("Processing classifications...")
    classification_results = classification_engine.process_multiple_classifications(
        data=answers,
        options=options,
        similarity_processor=similarity_processor
    )
    
    # 결과 파일 저장
    output_files = []
    for result in classification_results:
        # 커스텀 파일명 생성 - main.py와 동일한 형식: [원본파일명]_by_[option name]
        custom_filename = f"{output_prefix}_by_{result.type}.json"
        output_file = output_dir / custom_filename
        
        print(f"Saving {result.type} classification to: {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result.data, f, ensure_ascii=False, indent=2)
        
        output_files.append({
            'type': result.type,
            'filename': custom_filename,
            'path': str(output_file),
            'items': len(result.data) if isinstance(result.data, (list, dict)) else 0
        })
        
        # category 옵션인 경우 removedAnswers 없는 버전도 생성
        if result.type == 'category' and isinstance(result.data, list):
            simple_data = []
            for item in result.data:
                simple_obj = {
                    "representativeId": item.get("representativeId"),
                    "category1": item.get("category1"),
                    "category2": item.get("category2"),
                    "question": item.get("question"),
                    "representativeAnswer": item.get("representativeAnswer"),
                    "similarityCount": item.get("similarityCount", 0),
                    "avgSimilarity": item.get("avgSimilarity", 0.0)
                }
                simple_data.append(simple_obj)
            
            simple_filename = f"{output_prefix}_by_{result.type}_simple.json"
            simple_output_file = output_dir / simple_filename
            
            print(f"Saving {result.type} simple classification to: {simple_output_file}")
            with open(simple_output_file, 'w', encoding='utf-8') as f:
                json.dump(simple_data, f, ensure_ascii=False, indent=2)
            
            output_files.append({
                'type': f'{result.type}_simple',
                'filename': simple_filename,
                'path': str(simple_output_file),
                'items': len(simple_data)
            })
    
    # 처리 결과 반환
    result_summary = {
        'success': True,
        'input_file': str(input_path),
        'output_directory': str(output_dir),
        'processed_items': len(answers),
        'original_questions': len(validated_data),
        'file_size_mb': file_size_mb,
        'output_files': output_files
    }
    
    return result_summary


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description='Flask API /api/process 엔드포인트 수동 실행 스크립트',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python manual_process.py "data/행정학 1,2(원본).json" category
  python manual_process.py "data/행정학 5,6,7(원본).json" category,institution,year
  python manual_process.py input.json category --output-dir results/
  python manual_process.py input.json category --output-prefix "행정학_1차"
  python manual_process.py input.json category,year -o results/ -p "final_result"
        """
    )
    
    parser.add_argument(
        'input_file',
        help='입력 JSON 파일 경로'
    )
    
    parser.add_argument(
        'options',
        help='분류 옵션 (쉼표로 구분): category, institution, year'
    )
    
    parser.add_argument(
        '--output-dir', '-o',
        help='출력 디렉토리 (기본값: 입력 파일과 같은 디렉토리)'
    )
    
    parser.add_argument(
        '--output-prefix', '-p',
        help='출력 파일명 접두사 (기본값: 입력 파일명)'
    )
    
    args = parser.parse_args()
    
    # 옵션 파싱
    valid_options = {'category', 'institution', 'year'}
    options = [opt.strip() for opt in args.options.split(',')]
    
    # 옵션 유효성 검사
    invalid_options = set(options) - valid_options
    if invalid_options:
        print(f"Error: Invalid options: {', '.join(invalid_options)}")
        print(f"Valid options: {', '.join(valid_options)}")
        sys.exit(1)
    
    if not options:
        print("Error: At least one option must be specified")
        sys.exit(1)
    
    try:
        # 파일 처리 실행
        result = process_file_manual(
            input_file_path=args.input_file,
            options=options,
            output_dir=args.output_dir,
            output_prefix=args.output_prefix
        )
        
        # 결과 출력
        print("\n" + "="*60)
        print("PROCESSING COMPLETED SUCCESSFULLY")
        print("="*60)
        print(f"Input file: {result['input_file']}")
        print(f"Output directory: {result['output_directory']}")
        print(f"Original questions: {result['original_questions']}")
        print(f"Processed answers: {result['processed_items']}")
        print(f"File size: {result['file_size_mb']:.1f}MB")
        print("\nGenerated files:")
        
        for output_file in result['output_files']:
            print(f"  - {output_file['type']}: {output_file['path']}")
            if isinstance(output_file['items'], int):
                print(f"    Items: {output_file['items']}")
        
        print("\nAll files saved successfully!")
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()