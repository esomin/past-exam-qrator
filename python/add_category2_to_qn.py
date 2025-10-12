#!/usr/bin/env python3
"""
질문 데이터에 키워드 추출하여 category2 추가 모듈
input.json의 질문들에서 키워드를 추출하여 category2 필드를 추가합니다.
"""

import json
import re
import unicodedata
from typing import List, Dict, Any


class Category2Adder:
    """질문에 category2 키워드를 추가하는 클래스"""
    
    def __init__(self):
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
    
    def strip_p_tag(self, text: str) -> str:
        """HTML p 태그를 제거하고 텍스트를 정리"""
        if not text or not text.strip():
            return ""
        cleaned_text = re.sub(r'</?p[^>]*>', '', text).strip()
        return cleaned_text if cleaned_text else ""
    
    def add_category2_to_questions(self, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """질문 데이터에 category2 키워드를 추가"""
        # ETC 타입 필터링
        filtered_questions = [q for q in questions if q.get('titleType') != "ETC"]
        
        # 각 질문에 category2 추가
        for question in filtered_questions:
            question['category2'] = self.extract_keyword(question['title'])
        
        return filtered_questions
    
    def create_qna_pairs(self, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Q&A 쌍 데이터를 생성"""
        # category2 추가
        data_with_category2 = self.add_category2_to_questions(questions)
        
        # 카테고리별 정렬
        sorted_data = sorted(data_with_category2, key=lambda q: q.get('categoryTitle', ''))
        
        qna_pairs = []
        for q in sorted_data:
            qna_pair = {
                'id': q['id'],
                'category1': q.get('categoryTitle', ''),
                'category2': q.get('category2', ''),
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
            qna_pairs.append(qna_pair)
        
        return qna_pairs


def add_category2_to_data(input_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """입력 데이터에 category2를 추가하는 함수"""
    adder = Category2Adder()
    return adder.add_category2_to_questions(input_data)


def create_qna_pairs_with_category2(input_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """입력 데이터에서 category2가 포함된 Q&A 쌍을 생성하는 함수"""
    adder = Category2Adder()
    return adder.create_qna_pairs(input_data)


if __name__ == "__main__":
    # 테스트용 실행
    with open("data/input.json", 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    result = add_category2_to_data(data)
    print(f"✅ Added category2 to {len(result)} questions")