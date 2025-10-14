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


def convert_input_to_answers(input_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """input.json을 answers 형태로 직접 변환 (중간 파일 생성 없음)"""
    print("Converting input data to answers format...")
    qna_pairs = create_qna_pairs_with_category2(input_data)
    
    answers = []
    for qna in qna_pairs:
        # 각 답변을 개별 항목으로 변환
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


def main():
    """메인 함수 - 최적화된 Q&A 처리 파이프라인"""
    print('Starting Optimized Q&A Processing Pipeline')
    print('Pipeline: input.json → similarity grouping → grouped_answers_by_similarity.json')
    
    try:
        # 1단계: input.json 로드
        print('\nStep 1: Loading input.json...')
        input_path = "data/input.json"
        with open(input_path, 'r', encoding='utf-8') as f:
            input_data = json.load(f)
        print(f"Loaded {len(input_data)} questions from {input_path}")
        
        # 2단계: input을 answers 형태로 변환 (메모리에서만)
        print('\nStep 2: Converting to answers format...')
        answers = convert_input_to_answers(input_data)
        
        # 3단계: 유사도 기반 중복 제거 (메모리에서만)
        print('\nStep 3: Processing similarity-based grouping...')
        deduplicator = SimilarityDeduplicator(
            input_file=None,  # 파일 대신 메모리 데이터 사용
            output_dir="data",
            threshold=0.8
        )
        
        # 메모리 데이터로 직접 처리
        _, similar_groups = deduplicator.process_similarity_from_data(answers)
        
        # 4단계: Nested 구조 생성 및 저장
        print('\nStep 4: Creating final nested structure...')
        create_nested_structure_from_groups(similar_groups)
        
        print('\nOptimized pipeline processing completed successfully!')
        print('Final output:')
        print('   - data/grouped_answers_by_similarity.json (Final result)')
        print('   - data/similarity_deduplication.log (Processing log)')
        
    except Exception as error:
        print(f'Pipeline processing failed: {error}')
        raise


if __name__ == "__main__":
    main()