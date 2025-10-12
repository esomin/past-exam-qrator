#!/usr/bin/env python3
"""
Q&A 쌍 처리 메인 파이프라인
input.json에서 시작하여 전체 처리 과정을 거쳐 최종 결과물까지 생성합니다.
- qna_pairs.json, questions.json, answers.json 생성
- 답변 필터링 및 유사도 기반 중복 제거
- 최종 출력: answers_similarity_unique.json, answers_similarity_removed.json
"""

import json
import os
from typing import List, Dict, Any
from process_qna_pairs import QnAPairProcessor
from remove_similarity_duplicates import SimilarityDeduplicator


def generate_questions_and_answers(qna_pairs: List[Dict[str, Any]], output_dir: str = "data") -> None:
    """Q&A 쌍 데이터에서 questions.json과 answers.json을 생성"""
    questions = []
    answers = []
    
    for qna in qna_pairs:
        # questions.json용 데이터 (answers 속성 제외)
        question = {
            "id": qna["id"],
            "category1": qna["category1"],
            "category2": qna["category2"],
            "question": qna["question"]
        }
        questions.append(question)
        
        # answers.json용 데이터 (각 답변을 개별 항목으로)
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
    
    # questions.json 저장
    questions_path = os.path.join(output_dir, "questions.json")
    with open(questions_path, 'w', encoding='utf-8') as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)
    print(f"✅ Saved: {questions_path} ({len(questions)} questions)")
    
    # answers.json 저장
    answers_path = os.path.join(output_dir, "answers.json")
    with open(answers_path, 'w', encoding='utf-8') as f:
        json.dump(answers, f, ensure_ascii=False, indent=2)
    print(f"✅ Saved: {answers_path} ({len(answers)} answers)")


def main():
    """메인 함수 - 전체 Q&A 처리 파이프라인 실행"""
    print('🚀 Starting Complete Q&A Processing Pipeline')
    print('📋 Pipeline: input.json → qna_pairs.json → questions.json, answers.json → similarity deduplication')
    
    try:
        # 1단계: Q&A 쌍 처리
        print('\n📋 Step 1: Processing Q&A pairs...')
        qna_pair_processor = QnAPairProcessor()
        qna_pair_processor.run()
        
        # 2단계: qna_pairs.json 파일 로드 및 분리된 파일 생성
        print('\n📋 Step 2: Generating questions.json and answers.json...')
        qna_pairs_path = os.path.join("data", "qna_pairs.json")
        with open(qna_pairs_path, 'r', encoding='utf-8') as f:
            qna_pairs = json.load(f)
        
        # questions.json과 answers.json 생성
        generate_questions_and_answers(qna_pairs)
        
        # 3단계: 답변 필터링 및 유사도 기반 중복 제거
        print('\n📋 Step 3: Filtering and removing similar duplicates...')
        deduplicator = SimilarityDeduplicator(
            input_file="data/answers.json",
            output_dir="data",
            threshold=0.8
        )
        deduplicator.run()
        
        print('\n✅ Complete pipeline processing finished successfully!')
        print('📁 Final outputs:')
        print('   - data/qna_pairs.json (Q&A pairs)')
        print('   - data/questions.json (Questions only)')
        print('   - data/answers.json (All answers)')
        print('   - data/answers_similarity_unique.json (Final unique answers)')
        print('   - data/answers_similarity_removed.json (Removed similar groups)')
        print('   - data/similarity_deduplication.log (Processing log)')
        
    except Exception as error:
        print(f'❌ Pipeline processing failed: {error}')
        raise


if __name__ == "__main__":
    main()