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


def create_nested_structure_from_groups(similar_groups: List[Dict[str, Any]]) -> Dict[str, Dict[str, List[Dict]]]:
    """similar_groups에서 nested 구조 생성"""
    print("Creating nested structure from similarity groups...")
    
    nested_output = defaultdict(lambda: defaultdict(list))
    
    for item in similar_groups:
        category1_key = item['category1']
        category2_key = item['category2']
        nested_output[category1_key][category2_key].append(item)
    
    # Convert to regular dict
    result = {
        cat1: dict(cat2_dict) 
        for cat1, cat2_dict in nested_output.items()
    }
    
    # 결과 저장
    output_path = "data/grouped_answers_by_similarity.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f'Successfully created: {output_path}')
    print(f'Total categories: {len(result)}')
    for cat1 in result:
        print(f'  {cat1}: {len(result[cat1])} subcategories')
    
    return result


def classify_by_institution(data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Group data by institution extracted from solve field"""
    print("Classifying data by institution...")
    
    institution_groups = defaultdict(list)
    
    for item in data:
        institution = item.get('institution', 'Unknown')
        institution_groups[institution].append(item)
    
    result = dict(institution_groups)
    
    # 결과 저장
    output_path = "data/institution_classification.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f'Successfully created: {output_path}')
    print(f'Total institutions: {len(result)}')
    for institution in result:
        print(f'  {institution}: {len(result[institution])} items')
    
    return result


def classify_by_year(data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Group data by year extracted from solve field"""
    print("Classifying data by year...")
    
    year_groups = defaultdict(list)
    
    for item in data:
        year = item.get('year', 'Unknown')
        year_groups[year].append(item)
    
    result = dict(year_groups)
    
    # 결과 저장
    output_path = "data/year_classification.json"
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
            
            # Nested 구조 생성 및 저장
            print('\nStep 3a-final: Creating category nested structure...')
            results['category'] = create_nested_structure_from_groups(similar_groups)
        
        if 'institution' in classification_options:
            print('\nStep 3b: Processing institution-based classification...')
            results['institution'] = classify_by_institution(answers)
        
        if 'year' in classification_options:
            print('\nStep 3c: Processing year-based classification...')
            results['year'] = classify_by_year(answers)
        
        print('\nEnhanced pipeline processing completed successfully!')
        print('Generated outputs:')
        if 'category' in classification_options:
            print('   - data/grouped_answers_by_similarity.json (Category classification)')
            print('   - data/similarity_deduplication.log (Processing log)')
        if 'institution' in classification_options:
            print('   - data/institution_classification.json (Institution classification)')
        if 'year' in classification_options:
            print('   - data/year_classification.json (Year classification)')
        
        return results
        
    except Exception as error:
        print(f'Pipeline processing failed: {error}')
        raise


if __name__ == "__main__":
    main()