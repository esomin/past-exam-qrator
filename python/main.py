#!/usr/bin/env python3
"""
원본 데이터 플래튼 처리 파이프라인
원본 JSON 데이터를 플래튼하여 필요한 속성만 추출하고 isCorrect 로직 적용
- 최종 출력: 연도별/기관별 정렬된 플래튼 데이터
"""

import json
import os
import re
from typing import List, Dict, Any, Optional
from collections import defaultdict


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


def flatten_original_data(input_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """원본 데이터를 플래튼하여 필요한 속성만 추출"""
    print("Flattening original data...")
    
    flattened_data = []
    
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
        for answer in answer_set:
            # answerSet 항목 속성 추출
            answer_data = {
                "id": answer.get("id"),
                "answer_title": answer.get("title"),
                "commentary": answer.get("commentary"),
                "answerKind": answer.get("answerKind")
            }
            
            # isCorrect 결정
            is_correct = determine_is_correct(
                question_data["titleType"], 
                answer_data["answerKind"]
            )
            
            # 최종 플래튼 항목 생성
            flattened_item = {
                # question 속성들
                "answerRate": question_data["answerRate"],
                "question_title": question_data["title"],
                "titleType": question_data["titleType"],
                "solve": question_data["solve"],
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
    
    print(f"Flattened {len(input_data)} questions into {len(flattened_data)} answer items")
    return flattened_data


def create_category_array_from_groups(similar_groups: List[Dict[str, Any]], input_filename: str) -> List[Dict[str, Any]]:
    """similar_groups를 answer object 배열로 변환하고 두 개의 파일 생성"""
    print("Creating category array structure from similarity groups...")
    
    # 배열 형식으로 변환
    result_array = []
    
    for item in similar_groups:
        # 기본 구조 생성
        answer_obj = {
            "representativeId": item.get("representativeId"),
            "category1": item.get("category1"),
            "category2": item.get("category2"),
            "question": item.get("question"),
            "representativeAnswer": item.get("representativeAnswer"),
            "similarityCount": item.get("similarityCount", 0),
            "avgSimilarity": item.get("avgSimilarity", 0.0),
            "removedAnswers": item.get("removedAnswers", [])
        }
        result_array.append(answer_obj)
    
    # 파일명 설정
    base_name = os.path.splitext(input_filename)[0]
    
    # 1. removedAnswers 포함 버전 저장
    output_path_full = f"data/{base_name}_by_category.json"
    with open(output_path_full, 'w', encoding='utf-8') as f:
        json.dump(result_array, f, ensure_ascii=False, indent=2)
    
    print(f'Successfully created: {output_path_full}')
    print(f'Total items: {len(result_array)}')
    
    # 2. removedAnswers 없는 버전 생성
    result_array_simple = []
    for item in result_array:
        simple_obj = {
            "representativeId": item["representativeId"],
            "category1": item["category1"],
            "category2": item["category2"],
            "question": item["question"],
            "representativeAnswer": item["representativeAnswer"],
            "similarityCount": item["similarityCount"],
            "avgSimilarity": item["avgSimilarity"]
        }
        result_array_simple.append(simple_obj)
    
    output_path_simple = f"data/{base_name}_by_category_simple.json"
    with open(output_path_simple, 'w', encoding='utf-8') as f:
        json.dump(result_array_simple, f, ensure_ascii=False, indent=2)
    
    print(f'Successfully created: {output_path_simple}')
    
    return result_array


def classify_by_institution(data: List[Dict[str, Any]], input_filename: str) -> Dict[str, List[Dict[str, Any]]]:
    """플래튼된 데이터를 기관별로 분류"""
    print("Classifying flattened data by institution...")
    
    institution_groups = defaultdict(list)
    
    for item in data:
        institution = item.get('institution', 'Unknown')
        institution_groups[institution].append(item)
    
    # 각 기관별로 연도순 정렬
    for institution in institution_groups:
        institution_groups[institution].sort(key=lambda x: (x.get('year', 'Unknown'), x.get('id', 0)))
    
    result = dict(institution_groups)
    
    # 결과 저장
    base_name = os.path.splitext(input_filename)[0]
    output_path = f"data/{base_name}_flattened_by_institution.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f'Successfully created: {output_path}')
    print(f'Total institutions: {len(result)}')
    for institution in result:
        print(f'  {institution}: {len(result[institution])} items')
    
    return result


def classify_by_year(data: List[Dict[str, Any]], input_filename: str) -> Dict[str, List[Dict[str, Any]]]:
    """플래튼된 데이터를 연도별로 분류"""
    print("Classifying flattened data by year...")
    
    year_groups = defaultdict(list)
    
    for item in data:
        year = item.get('year', 'Unknown')
        year_groups[year].append(item)
    
    # 각 연도별로 기관순, ID순 정렬
    for year in year_groups:
        year_groups[year].sort(key=lambda x: (x.get('institution', 'Unknown'), x.get('id', 0)))
    
    # 연도순으로 정렬된 결과 생성
    sorted_years = sorted(year_groups.keys(), key=lambda x: x if x != 'Unknown' else '0000')
    result = {year: year_groups[year] for year in sorted_years}
    
    # 결과 저장
    base_name = os.path.splitext(input_filename)[0]
    output_path = f"data/{base_name}_flattened_by_year.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f'Successfully created: {output_path}')
    print(f'Total years: {len(result)}')
    for year in result:
        print(f'  {year}: {len(result[year])} items')
    
    return result


def main(classification_options: List[str] = None):
    """
    메인 함수 - 원본 데이터 플래튼 및 분류 파이프라인
    
    Args:
        classification_options: List of classification types to perform
                              Options: ['category', 'institution', 'year', 'flatten']
                              Default: ['flatten', 'institution', 'year']
    """
    if classification_options is None:
        classification_options = ['flatten', 'institution', 'year']
    
    print('Starting Original Data Flattening and Classification Pipeline')
    print(f'Classifications to perform: {", ".join(classification_options)}')
    
    try:
        # 1단계: input.json 로드
        print('\nStep 1: Loading input.json...')
        input_path = "data/input.json"
        input_filename = os.path.basename(input_path)
        with open(input_path, 'r', encoding='utf-8') as f:
            input_data = json.load(f)
        print(f"Loaded {len(input_data)} questions from {input_path}")
        
        # 2단계: 원본 데이터 플래튼
        print('\nStep 2: Flattening original data...')
        flattened_data = flatten_original_data(input_data)
        
        # 3단계: 분류 처리
        results = {}
        
        # 플래튼된 데이터 저장
        if 'flatten' in classification_options:
            print('\nStep 3a: Saving flattened data...')
            base_name = os.path.splitext(input_filename)[0]
            flattened_path = f"data/{base_name}_flattened.json"
            with open(flattened_path, 'w', encoding='utf-8') as f:
                json.dump(flattened_data, f, ensure_ascii=False, indent=2)
            print(f'Successfully created: {flattened_path}')
            results['flatten'] = flattened_data
        
        # 기관별 분류 (플래튼된 데이터 기반)
        if 'institution' in classification_options:
            print('\nStep 3b: Processing institution-based classification...')
            results['institution'] = classify_by_institution(flattened_data, input_filename)
        
        # 연도별 분류 (플래튼된 데이터 기반)
        if 'year' in classification_options:
            print('\nStep 3c: Processing year-based classification...')
            results['year'] = classify_by_year(flattened_data, input_filename)
        
        # 기존 카테고리 분류 (유사도 기반 - 별도 로직)
        if 'category' in classification_options:
            print('\nStep 3d: Processing similarity-based category grouping...')
            # 기존 로직을 위한 답변 형태 변환
            from add_category2_to_qn import create_qna_pairs_with_category2
            from remove_similarity_duplicates import SimilarityDeduplicator
            
            qna_pairs = create_qna_pairs_with_category2(input_data)
            answers = []
            for qna in qna_pairs:
                for answer in qna["answers"]:
                    answer_item = {
                        "id": answer["id"],
                        "category1": qna["category1"],
                        "category2": qna["category2"],
                        "question": qna["question"],
                        "answer": answer["answer"],
                        "isTrue": answer["isTrue"]
                    }
                    answers.append(answer_item)
            
            deduplicator = SimilarityDeduplicator(
                input_file=None,
                output_dir="data",
                threshold=0.8
            )
            
            _, similar_groups = deduplicator.process_similarity_from_data(answers)
            results['category'] = create_category_array_from_groups(similar_groups, input_filename)
        
        print('\nFlattening and classification pipeline completed successfully!')
        print('Generated outputs:')
        base_name = os.path.splitext(input_filename)[0]
        
        if 'flatten' in classification_options:
            print(f'   - data/{base_name}_flattened.json (Flattened original data)')
        if 'institution' in classification_options:
            print(f'   - data/{base_name}_flattened_by_institution.json (Institution classification)')
        if 'year' in classification_options:
            print(f'   - data/{base_name}_flattened_by_year.json (Year classification)')
        if 'category' in classification_options:
            print(f'   - data/{base_name}_by_category.json (Category classification with removedAnswers)')
            print(f'   - data/{base_name}_by_category_simple.json (Category classification without removedAnswers)')
        
        return results
        
    except Exception as error:
        print(f'Pipeline processing failed: {error}')
        raise


if __name__ == "__main__":
    # 기본적으로 플래튼, 기관별, 연도별 분류 실행
    main(['flatten', 'institution', 'year'])
    
    # 카테고리 분류도 함께 실행하려면:
    # main(['flatten', 'institution', 'year', 'category'])