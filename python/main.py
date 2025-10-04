#!/usr/bin/env python3
"""
Q&A 쌍 처리 메인 파이프라인
Q&A 쌍 처리 모듈을 실행하여 qna_pairs.json, questions.json, answers.json 파일을 생성합니다.
"""

import json
import os
from typing import List, Dict, Any
from process_qna_pairs import QnAPairProcessor


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
    """메인 함수 - Q&A 쌍 처리 및 분리된 파일 생성"""
    print('🚀 Starting Q&A Processing Pipeline')
    
    try:
        # Q&A 쌍 처리
        qna_pair_processor = QnAPairProcessor()
        qna_pair_processor.run()
        
        # qna_pairs.json 파일 로드
        qna_pairs_path = os.path.join("data", "qna_pairs.json")
        with open(qna_pairs_path, 'r', encoding='utf-8') as f:
            qna_pairs = json.load(f)
        
        # questions.json과 answers.json 생성
        generate_questions_and_answers(qna_pairs)
        
        print('✅ All processing completed successfully!')
        print('📁 Check qna_pairs.json, questions.json, answers.json in ./data directory')
        
    except Exception as error:
        print(f'❌ Processing failed: {error}')
        raise


if __name__ == "__main__":
    main()