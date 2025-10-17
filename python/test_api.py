#!/usr/bin/env python3
"""
Flask API /api/process 엔드포인트 테스트 스크립트
"""

import json
import base64
import requests
from pathlib import Path


def test_api_process(input_file_path: str, options: list, api_url: str = "http://localhost:5001"):
    """
    Flask API /api/process 엔드포인트를 테스트합니다.
    
    Args:
        input_file_path: 입력 JSON 파일 경로
        options: 분류 옵션 리스트
        api_url: API 서버 URL
    """
    # 파일 읽기
    input_path = Path(input_file_path)
    if not input_path.exists():
        print(f"Error: File not found: {input_file_path}")
        return
    
    print(f"Testing API with file: {input_path}")
    print(f"Options: {options}")
    
    # JSON 파일을 base64로 인코딩
    with open(input_path, 'r', encoding='utf-8') as f:
        json_content = f.read()
    
    file_data = base64.b64encode(json_content.encode('utf-8')).decode('utf-8')
    
    # API 요청 데이터 준비
    payload = {
        "file_data": file_data,
        "filename": input_path.name,
        "options": options
    }
    
    # API 요청
    try:
        print(f"Sending request to {api_url}/api/process...")
        response = requests.post(
            f"{api_url}/api/process",
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=300  # 5분 타임아웃
        )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API request successful!")
            print(f"Processed items: {result.get('processed_items', 'N/A')}")
            print(f"Original questions: {result.get('original_questions', 'N/A')}")
            print(f"Results: {len(result.get('results', []))}")
            
            for result_item in result.get('results', []):
                print(f"  - {result_item['type']}: {result_item['filename']}")
        else:
            print("❌ API request failed!")
            try:
                error_data = response.json()
                print(f"Error: {error_data}")
            except:
                print(f"Error response: {response.text}")
    
    except requests.exceptions.ConnectionError:
        print("❌ Connection error: Make sure Flask server is running on port 5001")
    except requests.exceptions.Timeout:
        print("❌ Request timeout: Processing took too long")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Flask API /api/process 엔드포인트 테스트')
    parser.add_argument('input_file', help='입력 JSON 파일 경로')
    parser.add_argument('options', help='분류 옵션 (쉼표로 구분): category, institution, year')
    parser.add_argument('--url', default='http://localhost:5001', help='API 서버 URL')
    
    args = parser.parse_args()
    
    # 옵션 파싱
    options = [opt.strip() for opt in args.options.split(',')]
    
    # API 테스트 실행
    test_api_process(args.input_file, options, args.url)


if __name__ == "__main__":
    main()