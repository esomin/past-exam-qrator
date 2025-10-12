#!/usr/bin/env python3
"""
Q&A 쌍 처리 메인 파이프라인
input.json에서 시작하여 전체 처리 과정을 거쳐 최종 결과물까지 생성합니다.
- 답변 필터링 및 유사도 기반 중복 제거
- 최종 출력: answers_similarity_unique.json, answers_similarity_removed.json
"""

import json
import os
from typing import List, Dict, Any
from add_category2_to_qn import create_qna_pairs_with_category2
from remove_similarity_duplicates import SimilarityDeduplicator


def create_qna_pairs_file(input_data: List[Dict[str, Any]], output_dir: str = "data") -> str:
    """input.json에서 category2가 포함된 qna_pairs.json을 생성"""
    qna_pairs = create_qna_pairs_with_category2(input_data)
    
    # qna_pairs.json 저장
    qna_pairs_path = os.path.join(output_dir, "qna_pairs.json")
    with open(qna_pairs_path, 'w', encoding='utf-8') as f:
        json.dump(qna_pairs, f, ensure_ascii=False, indent=2)
    print(f"Saved: {qna_pairs_path} ({len(qna_pairs)} Q&A pairs)")
    
    return qna_pairs_path


def convert_qna_pairs_to_answers(qna_pairs: List[Dict[str, Any]], output_dir: str = "data") -> List[Dict[str, Any]]:
    """qna_pairs.json을 answers.json 형태로 변환"""
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
    
    # answers.json 저장 (유사도 제거를 위한 임시 파일)
    answers_path = os.path.join(output_dir, "answers.json")
    with open(answers_path, 'w', encoding='utf-8') as f:
        json.dump(answers, f, ensure_ascii=False, indent=2)
    print(f"Saved: {answers_path} ({len(answers)} answers)")
    
    return answers


def main():
    """메인 함수 - 전체 Q&A 처리 파이프라인 실행"""
    print('Starting Complete Q&A Processing Pipeline')
    print('Pipeline: input.json → qna_pairs.json (with category2) → answers.json → similarity deduplication')
    
    try:
        # 1단계: input.json 로드
        print('\nStep 1: Loading input.json...')
        input_path = "data/input.json"
        with open(input_path, 'r', encoding='utf-8') as f:
            input_data = json.load(f)
        print(f"Loaded {len(input_data)} questions from {input_path}")
        
        # 2단계: category2가 포함된 qna_pairs.json 생성
        print('\nStep 2: Creating qna_pairs.json with category2...')
        qna_pairs_path = create_qna_pairs_file(input_data)
        
        # 3단계: qna_pairs.json을 로드하여 answers.json 생성
        print('\nStep 3: Converting qna_pairs.json to answers.json...')
        with open(qna_pairs_path, 'r', encoding='utf-8') as f:
            qna_pairs = json.load(f)
        answers = convert_qna_pairs_to_answers(qna_pairs)
        
        # 4단계: 답변 필터링 및 유사도 기반 중복 제거
        print('\nStep 4: Filtering and removing similar duplicates...')
        deduplicator = SimilarityDeduplicator(
            input_file="data/answers.json",
            output_dir="data",
            threshold=0.8
        )
        deduplicator.run()
        
        print('\nComplete pipeline processing finished successfully!')
        print('Final outputs:')
        print('   - data/qna_pairs.json (Q&A pairs with category2)')
        print('   - data/answers.json (All answers - intermediate file)')
        print('   - data/answers_similarity_unique.json (Final unique answers)')
        print('   - data/answers_similarity_removed.json (Removed similar groups)')
        print('   - data/similarity_deduplication.log (Processing log)')
        
    except Exception as error:
        print(f'Pipeline processing failed: {error}')
        raise


if __name__ == "__main__":
    main()