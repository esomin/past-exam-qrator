#!/usr/bin/env python3
"""
질문 데이터 처리 모듈
Q&A 데이터에서 질문만 추출하여 questions.json 파일을 생성합니다.
"""

import json
import os
import re
import unicodedata
from typing import List, Dict, Any
from pathlib import Path


class QuestionProcessor:
    """질문 데이터 처리 클래스"""
    
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
    
    def process_questions(self, qna_array: List[Dict[str, Any]]) -> List[str]:
        """질문 데이터를 추출하고 필터링"""
        return [
            q['title'] 
            for q in qna_array 
            if q.get('titleType') != "ETC"
        ]
    
    def process_and_save_questions(self, qna_array: List[Dict[str, Any]]) -> None:
        """질문 처리 및 파일 저장"""
        print('📊 Processing questions...')
        questions = self.process_questions(qna_array)
        self.save_json_file(questions, 'questions.json')
        print(f'✨ Processed {len(questions)} questions')
    
    def run(self) -> None:
        """질문 처리 실행"""
        print('🚀 Starting Question Processing')
        
        try:
            qna_data = self.load_data()
            self.process_and_save_questions(qna_data)
            print('✅ Question processing completed successfully!')
            
        except Exception as error:
            print(f'❌ Question processing failed: {error}')
            raise


def main():
    """메인 함수"""
    processor = QuestionProcessor()
    processor.run()


if __name__ == "__main__":
    main()