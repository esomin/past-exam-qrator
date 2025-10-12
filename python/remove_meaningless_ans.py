#!/usr/bin/env python3
"""
답변 필터링 모듈
의미없는 답변들(자모 나열, 숫자개 등)을 필터링합니다.
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple


class AnswerFilter:
    """답변 필터링 클래스"""

    def __init__(self, input_file: str = "data/answers.json", output_dir: str = "data"):
        self.input_path = Path(input_file)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # (1) 자모 나열만 있는 라인: "ㄱ, ㄴ, ㄷ" 같은 패턴
        self.jamo_list_re = re.compile(r'^[\sㆍ,]*[ㄱ-ㅎ](?:\s*[ㆍ,]\s*[ㄱ-ㅎ])*[\sㆍ,]*$')

        # (2) 단독 "숫자개" 또는 "xx개"
        self.count_re = re.compile(r'^(?:\d+|xx)개$')

        # [id] 같은 접두사 제거
        self.prefix_re = re.compile(r'^\[.*?\]\s*')

    def extract_body(self, text: str) -> str:
        """[id] 같은 접두사 제거"""
        return self.prefix_re.sub('', text or '').strip()

    def should_remove(self, text: str) -> bool:
        """답변을 제거해야 하는지 판단"""
        body = self.extract_body(text)
        return not body or self.jamo_list_re.match(body) or self.count_re.match(body)

    def filter_answers(self, answers: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """답변들을 필터링하여 유효한 것과 제거된 것으로 분리"""
        kept, removed = [], []
        for ans in answers:
            text = ans.get("answer", "")
            (removed if self.should_remove(text) else kept).append(ans)
        return kept, removed

    def run(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """답변 필터링 실행"""
        with self.input_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        kept, removed = self.filter_answers(data)

        print(f"전체 {len(data)}개 → 남김 {len(kept)} / 제거 {len(removed)}")

        return kept, removed


if __name__ == "__main__":
    AnswerFilter().run()