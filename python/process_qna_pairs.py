#!/usr/bin/env python3
"""
Q&A 쌍 데이터 처리 모듈
Q&A 데이터에서 질문-답변 쌍을 생성하여 qna_pairs.json 파일을 생성합니다.
"""

import json
import os
import re
import unicodedata
from typing import List, Dict, Any, Optional
from pathlib import Path


class QnAPairProcessor:
    """Q&A 쌍 데이터 처리 클래스"""
    
    def __init__(self, input_file: str = "data/input.json", output_dir: str = "data"):
        self.input_file = input_file
        self.output_dir = output_dir
        self.ensure_output_dir()
        
        # 키워드 추출을 위한 정규식 패턴
        self.keyword_pattern = re.compile(r"""
            (.+?)                   # 캡처: 핵심 키워드
            (?=                     # Lookahead 시작
                에\s+(대한|관한)       # "에 대한/에 관한"
                | [과와]\s*관련(된|한|하여) # "과/와 관련된/관련한/관련하여"
                | 의\s*내용\s*중        # "의 내용 중"
                | 에\s*해당(하는|하지)   # "에 해당하는/에 해당하지"
                | 로만\s*묶은          # "로만 묶은"
                | 으로                 # "으로"
            )                       # Lookahead 끝
        """, re.VERBOSE)
    
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
    
    def normalize_text(self, text: str) -> str:
        """유니코드 정규화"""
        return unicodedata.normalize("NFKC", text).strip()
    
    def clean_prefix(self, text: str) -> str:
        """문제 번호 및 불필요한 접두사 제거"""
        text = self.normalize_text(text)
        # 1. [숫자] 문제번호 제거
        text = re.sub(r"^\[\d+\]\s*", "", text)
        # 2. "다음", "다음 중" 제거 (맨 앞 또는 카테고리 뒤)
        text = re.sub(r"(^|\]\s*)다음\s*중\s*", r"\1", text)
        text = re.sub(r"(^|\]\s*)다음\s*", r"\1", text)
        return text.strip()
    
    def extract_keyword(self, question_text: str) -> str:
        """질문에서 핵심 키워드 추출"""
        normalized_text = self.normalize_text(question_text)
        match = self.keyword_pattern.search(normalized_text)
        if match:
            subject = match.group(1).strip()
        else:
            subject = normalized_text
        return self.clean_prefix(subject)
    
    def process_qna_pairs(self, qna_array: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Q&A 쌍 데이터를 생성 (extractQna.ts의 transform 함수와 동일한 형태 + 키워드 추출)"""
        # ETC 타입 필터링 및 카테고리별 정렬
        filtered_data = [q for q in qna_array if q.get('titleType') != "ETC"]
        sorted_data = sorted(filtered_data, key=lambda q: q.get('categoryTitle', ''))
        
        return [
            {
                'id': q['id'],
                'category1': q.get('categoryTitle', ''),
                'category2': self.extract_keyword(q['title']),  # 키워드 추출하여 category2에 저장
                'question': q['title'],
                'answers': [
                    {
                        'id': answer['id'],
                        'answer': self.strip_p_tag(answer.get('title', '')),
                        'isAnswer': answer.get('answerKind') == "O",
                        'isTrue': (answer.get('answerKind') == "O" if q.get('titleType') == "POSITIVE" 
                                 else answer.get('answerKind') == "X")
                    }
                    for answer in q.get('answerSet', [])
                ]
            }
            for q in sorted_data
        ]
    
    def process_and_save_qna_pairs(self, qna_array: List[Dict[str, Any]]) -> None:
        """Q&A 쌍 처리 및 파일 저장"""
        print('🔄 Processing Q&A pairs...')
        qna_pairs = self.process_qna_pairs(qna_array)
        self.save_json_file(qna_pairs, 'qna_pairs.json')
        print(f'✨ Processed {len(qna_pairs)} Q&A pairs')
    
    def run(self) -> None:
        """Q&A 쌍 처리 실행"""
        print('🚀 Starting Q&A Pair Processing')
        
        try:
            qna_data = self.load_data()
            self.process_and_save_qna_pairs(qna_data)
            print('✅ Q&A pair processing completed successfully!')
            
        except Exception as error:
            print(f'❌ Q&A pair processing failed: {error}')
            raise


def main():
    """메인 함수"""
    processor = QnAPairProcessor()
    processor.run()


if __name__ == "__main__":
    main()