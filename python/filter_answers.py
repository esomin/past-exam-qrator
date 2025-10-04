#!/usr/bin/env python3
"""
답변 필터링 모듈
의미없는 답변들(자모 나열, 숫자개 등)을 필터링합니다.
"""

import json
import re
import os
from typing import List, Dict, Any, Tuple
from pathlib import Path


class AnswerFilter:
    """답변 필터링 클래스"""

    def __init__(self, input_file: str = "data/answers.json", output_dir: str = "data"):
        self.input_file = input_file
        self.output_dir = output_dir
        self.ensure_output_dir()

        # (1) 자모 나열만 있는 라인: "ㄱ, ㄴ, ㄷ" 같은 패턴
        self.jamo_list_re = re.compile(r'^[\sㆍ,]*[ㄱ-ㅎ](?:\s*[ㆍ,]\s*[ㄱ-ㅎ])*[\sㆍ,]*$')

        # (2) 단독 "숫자개" 또는 "xx개"
        self.count_re = re.compile(r'^(?:\d+|xx)개$')

        # [id] 같은 접두사 제거
        self.prefix_re = re.compile(r'^\[.*?\]\s*')

    def ensure_output_dir(self) -> None:
        """출력 디렉토리가 존재하는지 확인하고 없으면 생성"""
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)

    def load_answers(self) -> List[Dict[str, Any]]:
        """answers.json 파일에서 데이터 로드"""
        try:
            with open(self.input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"📁 Loaded {len(data)} answers from {self.input_file}")
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

    def extract_body(self, answer_text: str) -> str:
        """[id] 같은 접두사 제거"""
        if not answer_text:
            return ""
        return self.prefix_re.sub('', answer_text).strip()
    #!/usr/bin/env python3
"""
answers_filter_light.py
- 자모나열, 숫자개 등 의미없는 답변을 필터링합니다.
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple


class AnswerFilter:
    def __init__(self, input_file: str = "data/answers.json", output_dir: str = "data"):
        self.input_path = Path(input_file)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.jamo_list_re = re.compile(r'^[\sㆍ,]*[ㄱ-ㅎ](?:\s*[ㆍ,]\s*[ㄱ-ㅎ])*[\sㆍ,]*$')
        self.count_re = re.compile(r'^(?:\d+|xx)개$')
        self.prefix_re = re.compile(r'^\[.*?\]\s*')

    def extract_body(self, text: str) -> str:
        return self.prefix_re.sub('', text or '').strip()

    def should_remove(self, text: str) -> bool:
        body = self.extract_body(text)
        return not body or self.jamo_list_re.match(body) or self.count_re.match(body)

    def filter_answers(self, answers: List[Dict[str, Any]]) -> Tuple[List, List]:
        kept, removed = [], []
        for ans in answers:
            text = ans.get("answer", "")
            (removed if self.should_remove(text) else kept).append(ans)
        return kept, removed

    def run(self):
        with self.input_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        kept, removed = self.filter_answers(data)

        # 저장
        (self.output_dir / "answers_filtered.json").write_text(
            json.dumps(kept, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (self.output_dir / "answers_removed.json").write_text(
            json.dumps(removed, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        print(f"전체 {len(data)}개 → 남김 {len(kept)} / 제거 {len(removed)}")

        return kept, removed


if __name__ == "__main__":
    AnswerFilter().run()

    def should_filter_out(self, answer_text: str) -> bool:
        """답변을 필터링해야 하는지 판단"""
        if not answer_text:
            return True

        body = self.extract_body(answer_text)

        # 자모 나열 패턴 체크
        if self.jamo_list_re.match(body):
            return True

        # 숫자개 패턴 체크
        if self.count_re.match(body):
            return True

        return False

    def filter_answers(self, answers: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """답변들을 필터링하여 유효한 것과 제거된 것으로 분리"""
        kept = []
        removed = []

        for answer in answers:
            answer_text = answer.get('answer', '')

            if self.should_filter_out(answer_text):
                removed.append(answer)
            else:
                kept.append(answer)

        return kept, removed

    def process_and_save(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """답변 필터링 처리 및 파일 저장"""
        print('🔄 Starting answer filtering...')

        # 데이터 로드
        answers = self.load_answers()

        # 필터링 수행
        kept, removed = self.filter_answers(answers)

        # 결과 저장
        self.save_json_file(kept, 'answers_filtered.json')
        self.save_json_file(removed, 'answers_removed.json')

        # 통계 출력
        print(f'✨ Total answers: {len(answers)}')
        print(f'✨ Kept answers: {len(kept)}')
        print(f'✨ Removed answers: {len(removed)}')
        print(f'📊 Removal rate: {(len(removed) / len(answers) * 100):.2f}%')

        return kept, removed

    def run(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """답변 필터링 실행"""
        print('🚀 Starting Answer Filtering')

        try:
            kept, removed = self.process_and_save()
            print('✅ Answer filtering completed successfully!')
            return kept, removed

        except Exception as error:
            print(f'❌ Answer filtering failed: {error}')
            raise


def main():
    """메인 함수"""
    import argparse

    parser = argparse.ArgumentParser(description='답변 필터링 (자모 나열, 숫자개 등 제거)')
    parser.add_argument('--input', '-i', default='data/answers.json', help='입력 파일 경로')
    parser.add_argument('--output', '-o', default='data', help='출력 디렉토리')

    args = parser.parse_args()

    filter_processor = AnswerFilter(
        input_file=args.input,
        output_dir=args.output
    )
    filter_processor.run()


if __name__ == "__main__":
    main()