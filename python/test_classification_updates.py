#!/usr/bin/env python3
"""
분류 로직 업데이트 테스트 스크립트
category2 추가 및 정렬 로직 변경 테스트
"""

import json
import sys
import os

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import flatten_original_data, classify_by_institution, classify_by_year
from add_category2_to_qn import add_category2_to_data


def create_test_data():
    """테스트용 샘플 데이터 생성"""
    return [
        {
            "id": 1,
            "title": "네트워크 보안에 대한 다음 설명 중 옳은 것은?",
            "titleType": "POSITIVE",
            "solve": "한국정보보호학회 / 2023",
            "categoryTitle": "정보보안",
            "answerSet": [
                {"id": 101, "title": "방화벽은 네트워크 보안의 핵심이다", "answerKind": "O"},
                {"id": 102, "title": "암호화는 불필요하다", "answerKind": "X"}
            ]
        },
        {
            "id": 2,
            "title": "데이터베이스 관리에 관한 다음 중 틀린 것은?",
            "titleType": "NEGATIVE",
            "solve": "한국컴퓨터정보학회 / 2022",
            "categoryTitle": "데이터베이스",
            "answerSet": [
                {"id": 201, "title": "정규화는 중요하다", "answerKind": "O"},
                {"id": 202, "title": "백업은 필요없다", "answerKind": "X"}
            ]
        },
        {
            "id": 3,
            "title": "클라우드 컴퓨팅과 관련된 다음 설명은?",
            "titleType": "POSITIVE", 
            "solve": "한국정보보호학회 / 2023",
            "categoryTitle": "클라우드",
            "answerSet": [
                {"id": 301, "title": "확장성이 좋다", "answerKind": "O"},
                {"id": 302, "title": "비용이 많이 든다", "answerKind": "X"}
            ]
        }
    ]


def test_category2_addition():
    """category2 추가 테스트"""
    print("=== category2 추가 테스트 ===")
    test_data = create_test_data()
    
    # category2 추가
    data_with_category2 = add_category2_to_data(test_data)
    
    for item in data_with_category2:
        print(f"ID: {item['id']}")
        print(f"  원본 제목: {item['title']}")
        print(f"  category2: {item.get('category2', 'None')}")
        print()
    
    return data_with_category2


def test_flatten_with_category2():
    """플래튼 데이터에 category2 포함 테스트"""
    print("=== 플래튼 데이터 category2 포함 테스트 ===")
    test_data = create_test_data()
    
    flattened_data, stats = flatten_original_data(test_data)
    
    print(f"플래튼된 항목 수: {len(flattened_data)}")
    print(f"통계: {stats}")
    print()
    
    for item in flattened_data[:3]:  # 처음 3개만 출력
        print(f"ID: {item['id']}")
        print(f"  categoryTitle: {item.get('categoryTitle')}")
        print(f"  category2: {item.get('category2')}")
        print(f"  institution: {item.get('institution')}")
        print(f"  year: {item.get('year')}")
        print()
    
    return flattened_data


def test_sorting_logic():
    """정렬 로직 테스트"""
    print("=== 정렬 로직 테스트 ===")
    test_data = create_test_data()
    
    flattened_data, _ = flatten_original_data(test_data)
    
    # 기관별 분류 테스트
    print("기관별 분류 (category1, category2, id 순 정렬):")
    institution_data = classify_by_institution(flattened_data)
    
    for institution, items in institution_data.items():
        print(f"  {institution}:")
        for item in items:
            print(f"    ID:{item['id']} | category1:{item.get('categoryTitle')} | category2:{item.get('category2')}")
    print()
    
    # 연도별 분류 테스트
    print("연도별 분류 (category1, category2, id 순 정렬):")
    year_data = classify_by_year(flattened_data)
    
    for year, items in year_data.items():
        print(f"  {year}:")
        for item in items:
            print(f"    ID:{item['id']} | category1:{item.get('categoryTitle')} | category2:{item.get('category2')}")
    print()


def test_filename_generation():
    """파일명 생성 테스트"""
    print("=== 파일명 생성 테스트 ===")
    
    original_filename = "sample_data.json"
    base_filename = os.path.splitext(original_filename)[0]
    
    # 기관별 파일명
    institution_filename = f"{base_filename}_기관별.json"
    print(f"기관별 파일명: {institution_filename}")
    
    # 연도별 파일명
    year_filename = f"{base_filename}_연도별.json"
    print(f"연도별 파일명: {year_filename}")
    
    # 카테고리 파일명
    category_filename = f"{base_filename}_category.json"
    print(f"카테고리 파일명: {category_filename}")
    print()


if __name__ == "__main__":
    print("분류 로직 업데이트 테스트 시작\n")
    
    try:
        # 각 테스트 실행
        test_category2_addition()
        test_flatten_with_category2()
        test_sorting_logic()
        test_filename_generation()
        
        print("✅ 모든 테스트가 성공적으로 완료되었습니다!")
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()