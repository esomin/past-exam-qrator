#!/usr/bin/env python3
"""
Q&A 쌍 처리 메인 파이프라인
input.json에서 시작하여 유사도 기반 중복 제거된 nested 구조 생성
- 최종 출력: grouped_answers_by_similarity.json
"""

import json
import os
from typing import List, Dict, Any
from collections import defaultdict
from add_category2_to_qn import create_qna_pairs_with_category2
from remove_similarity_duplicates import SimilarityDeduplicator
from processors.solve_parser import SolveInfo


def convert_input_to_answers(input_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """input.json을 answers 형태로 직접 변환 (중간 파일 생성 없음)"""
    print("Converting input data to answers format...")
    qna_pairs = create_qna_pairs_with_category2(input_data)
    
    answers = []
    for qna in qna_pairs:
        # Parse solve field to extract institution and year
        solve_info = SolveInfo.parse(qna.get("solve", ""))
        
        # 각 답변을 개별 항목으로 변환
        for answer in qna["answers"]:
            answer_item = {
                "id": answer["id"],
                "category1": qna["category1"],
                "category2": qna["category2"],
                "institution": solve_info.institution,  # New field
                "year": solve_info.year,                # New field
                "solve": qna.get("solve", ""),          # Keep original solve field
                "question": qna["question"],
                "answer": answer["answer"],
                "isTrue": answer["isTrue"]
            }
            answers.append(answer_item)
    
    print(f"Converted to {len(answers)} answers from {len(qna_pairs)} Q&A pairs")
    return answers


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
    """Group data by institution extracted from solve field"""
    print("Classifying data by institution...")
    
    institution_groups = defaultdict(list)
    
    for item in data:
        institution = item.get('institution', 'Unknown')
        institution_groups[institution].append(item)
    
    result = dict(institution_groups)
    
    # 결과 저장 - 파일명 형식: [원본파일명]_by_[option name]
    base_name = os.path.splitext(input_filename)[0]
    output_path = f"data/{base_name}_by_institution.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f'Successfully created: {output_path}')
    print(f'Total institutions: {len(result)}')
    for institution in result:
        print(f'  {institution}: {len(result[institution])} items')
    
    return result


def classify_by_year(data: List[Dict[str, Any]], input_filename: str) -> Dict[str, List[Dict[str, Any]]]:
    """Group data by year extracted from solve field"""
    print("Classifying data by year...")
    
    year_groups = defaultdict(list)
    
    for item in data:
        year = item.get('year', 'Unknown')
        year_groups[year].append(item)
    
    result = dict(year_groups)
    
    # 결과 저장 - 파일명 형식: [원본파일명]_by_[option name]
    base_name = os.path.splitext(input_filename)[0]
    output_path = f"data/{base_name}_by_year.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f'Successfully created: {output_path}')
    print(f'Total years: {len(result)}')
    for year in result:
        print(f'  {year}: {len(result[year])} items')
    
    return result


def main(classification_options: List[str] = None):
    """
    메인 함수 - 최적화된 Q&A 처리 파이프라인
    
    Args:
        classification_options: List of classification types to perform
                              Options: ['category', 'institution', 'year']
                              Default: ['category'] (original behavior)
    """
    if classification_options is None:
        classification_options = ['category']
    
    print('Starting Enhanced Q&A Processing Pipeline')
    print(f'Classifications to perform: {", ".join(classification_options)}')
    
    try:
        # 1단계: input.json 로드
        print('\nStep 1: Loading input.json...')
        input_path = "data/input.json"
        input_filename = os.path.basename(input_path)
        with open(input_path, 'r', encoding='utf-8') as f:
            input_data = json.load(f)
        print(f"Loaded {len(input_data)} questions from {input_path}")
        
        # 2단계: input을 answers 형태로 변환 (메모리에서만)
        print('\nStep 2: Converting to answers format with enhanced fields...')
        answers = convert_input_to_answers(input_data)
        
        # 3단계: 분류 처리
        results = {}
        
        if 'category' in classification_options:
            print('\nStep 3a: Processing similarity-based category grouping...')
            deduplicator = SimilarityDeduplicator(
                input_file=None,  # 파일 대신 메모리 데이터 사용
                output_dir="data",
                threshold=0.8
            )
            
            # 메모리 데이터로 직접 처리
            _, similar_groups = deduplicator.process_similarity_from_data(answers)
            
            # 배열 구조 생성 및 저장 (두 개의 파일)
            print('\nStep 3a-final: Creating category array structure...')
            results['category'] = create_category_array_from_groups(similar_groups, input_filename)
        
        if 'institution' in classification_options:
            print('\nStep 3b: Processing institution-based classification...')
            results['institution'] = classify_by_institution(answers, input_filename)
        
        if 'year' in classification_options:
            print('\nStep 3c: Processing year-based classification...')
            results['year'] = classify_by_year(answers, input_filename)
        
        print('\nEnhanced pipeline processing completed successfully!')
        print('Generated outputs:')
        base_name = os.path.splitext(input_filename)[0]
        if 'category' in classification_options:
            print(f'   - data/{base_name}_by_category.json (Category classification with removedAnswers)')
            print(f'   - data/{base_name}_by_category_simple.json (Category classification without removedAnswers)')
            print('   - data/similarity_deduplication.log (Processing log)')
        if 'institution' in classification_options:
            print(f'   - data/{base_name}_by_institution.json (Institution classification)')
        if 'year' in classification_options:
            print(f'   - data/{base_name}_by_year.json (Year classification)')
        
        return results
        
    except Exception as error:
        print(f'Pipeline processing failed: {error}')
        raise


if __name__ == "__main__":
    main()