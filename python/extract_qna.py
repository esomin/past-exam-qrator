#!/usr/bin/env python3
"""
Q&A 데이터 처리 파이프라인
data/a.json 파일을 읽어서 여러 형태의 output 파일들을 생성합니다.
"""

import json
import os
import re
from typing import List, Dict, Any, Optional
from pathlib import Path


class QnAProcessor:
    """Q&A 데이터 처리 클래스"""
    
    def __init__(self, input_file: str = "data/input.json", output_dir: str = "data"):
        self.input_file = input_file
        self.output_dir = output_dir
        self.ensure_output_dir()
    
    def ensure_output_dir(self) -> None:
        """출력 디렉토리가 존재하는지 확인하고 없으면 생성"""
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
    
    def load_data(self) -> List[Dict[str, Any]]:
        """JSON 파일에서 데이터 로드"""
        try:
            with open(self.input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"📁 Loaded {len(data)} questions from {self.input_file}")
            return data
        except FileNotFoundError:
            print(f"❌ File not found: {self.input_file}")
            raise
        except json.JSONDecodeError as e:
            print(f"❌ JSON decode error: {e}")
            raise
    
    def save_json_file(self, data: Any, filename: str) -> None:
        """JSON 데이터를 파일로 저장"""
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ Saved: {filepath}")
    
    def strip_p_tag(self, text: Optional[str]) -> str:
        """HTML p 태그를 제거하고 텍스트를 정리"""
        if not text:
            return ""
        return re.sub(r'</?p[^>]*>', '', text).strip()
    
    def strip_all_html(self, text: Optional[str]) -> str:
        """모든 HTML 태그를 제거"""
        if not text:
            return ""
        return re.sub(r'<[^>]*>', '', text).strip()
    
    def process_questions(self, qna_array: List[Dict[str, Any]]) -> List[str]:
        """질문 데이터를 추출하고 필터링"""
        return [
            q['title'] 
            for q in qna_array 
            if q.get('titleType') != "ETC"
        ]
    
    def process_answers(self, qna_array: List[Dict[str, Any]]) -> List[str]:
        """답변 데이터를 추출하고 HTML을 정리"""
        answers = []
        for q in qna_array:
            if q.get('titleType') != "ETC":
                for answer in q.get('answerSet', []):
                    answers.append(self.strip_p_tag(answer.get('title', '')))
        return answers
    
    def process_qna_pairs(self, qna_array: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Q&A 쌍 데이터를 생성 (extractQna.ts의 transform 함수와 동일한 형태)"""
        # ETC 타입 필터링 및 카테고리별 정렬
        filtered_data = [q for q in qna_array if q.get('titleType') != "ETC"]
        sorted_data = sorted(filtered_data, key=lambda q: q.get('categoryTitle', ''))
        
        return [
            {
                'id': q['id'],
                'category1': q.get('categoryTitle', ''),
                'question': q['title'],
                'answers': [
                    {
                        'id': answer['id'],
                        'answer': answer.get('title', ''),
                        'isCorrect': answer.get('answerKind') == "O",
                        'isTrue': (answer.get('answerKind') == "O" if q.get('titleType') == "POSITIVE" 
                                 else answer.get('answerKind') == "X")
                    }
                    for answer in q.get('answerSet', [])
                ]
            }
            for q in sorted_data
        ]
    
    def process_and_save_questions(self, qna_array: List[Dict[str, Any]]) -> None:
        """질문 처리 및 파일 저장"""
        print('📊 Processing questions...')
        questions = self.process_questions(qna_array)
        self.save_json_file(questions, 'questions.json')
        print(f'✨ Processed {len(questions)} questions')
    
    def process_and_save_answers(self, qna_array: List[Dict[str, Any]]) -> None:
        """답변 처리 및 파일 저장"""
        print('💬 Processing answers...')
        answers = self.process_answers(qna_array)
        self.save_json_file(answers, 'answers.json')
        print(f'✨ Processed {len(answers)} answers')
    
    def process_and_save_qna_pairs(self, qna_array: List[Dict[str, Any]]) -> None:
        """Q&A 쌍 처리 및 파일 저장"""
        print('🔄 Processing Q&A pairs...')
        qna_pairs = self.process_qna_pairs(qna_array)
        self.save_json_file(qna_pairs, 'qna_pairs.json')
        print(f'✨ Processed {len(qna_pairs)} Q&A pairs')
    
    def run_pipeline(self) -> None:
        """전체 파이프라인 실행"""
        print('🚀 Starting Q&A Processing Pipeline')
        
        try:
            # 데이터 로드
            qna_data = self.load_data()
            
            # 각 프로세서 실행
            self.process_and_save_questions(qna_data)
            self.process_and_save_answers(qna_data)
            self.process_and_save_qna_pairs(qna_data)
            
            print('✅ Pipeline completed successfully!')
            print('📁 Check output files in ./data directory')
            
        except Exception as error:
            print(f'❌ Pipeline failed: {error}')
            raise


def main():
    """메인 함수"""
    processor = QnAProcessor()
    processor.run_pipeline()


if __name__ == "__main__":
    main()