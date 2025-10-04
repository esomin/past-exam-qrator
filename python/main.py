#!/usr/bin/env python3
"""
Q&A 데이터 처리 메인 파이프라인
세 가지 처리 모듈을 실행하여 questions.json, answers.json, qna_pairs.json 파일을 생성합니다.
"""

from process_questions import QuestionProcessor
from process_answers import AnswerProcessor
from process_qna_pairs import QnAPairProcessor


def main():
    """메인 함수 - 세 가지 처리 모듈을 순차적으로 실행"""
    print('🚀 Starting Q&A Processing Pipeline')
    
    try:
        # 1. 질문 처리
        question_processor = QuestionProcessor()
        question_processor.run()
        
        # 2. 답변 처리
        answer_processor = AnswerProcessor()
        answer_processor.run()
        
        # 3. Q&A 쌍 처리
        qna_pair_processor = QnAPairProcessor()
        qna_pair_processor.run()
        
        print('✅ Pipeline completed successfully!')
        print('📁 Check output files in ./data directory')
        
    except Exception as error:
        print(f'❌ Pipeline failed: {error}')
        raise


if __name__ == "__main__":
    main()