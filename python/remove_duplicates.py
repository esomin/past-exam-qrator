#!/usr/bin/env python3
"""
답변 중복 제거 모듈
answers.json 파일에서 중복된 답변을 제거하고 두 개의 출력 파일을 생성합니다.
1. answers_unique.json - 중복이 제거된 답변 목록 (원본과 동일한 스키마)
2. answers_removed.json - 제거된 답변들의 그룹 목록
"""

import json
import os
from typing import List, Dict, Any
from pathlib import Path


class DuplicateRemover:
    """중복 답변 제거 클래스"""
    
    def __init__(self, input_file: str = "data/answers.json", output_dir: str = "data"):
        self.input_file = input_file
        self.output_dir = output_dir
        self.ensure_output_dir()
    
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
    
    def remove_duplicates(self, answers: List[Dict[str, Any]]) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """중복 답변을 제거하고 유니크한 답변과 제거된 답변 그룹을 반환"""
        # 답변 텍스트를 키로 하는 딕셔너리 생성
        answer_groups = {}
        
        for answer in answers:
            answer_text = answer.get('answer', '').strip()
            if answer_text not in answer_groups:
                answer_groups[answer_text] = []
            answer_groups[answer_text].append(answer)
        
        unique_answers = []
        removed_groups = []
        
        for answer_text, group in answer_groups.items():
            if len(group) == 1:
                # 중복이 없는 경우 - duplicateCount 속성을 추가하지 않음
                unique_answers.append(group[0].copy())
            else:
                # 중복이 있는 경우
                # 첫 번째 답변을 유니크 답변에 추가 (전체 그룹 크기를 중복 개수로)
                survivor = group[0].copy()
                survivor['duplicateCount'] = len(group)
                unique_answers.append(survivor)
                
                # 나머지 답변들을 제거된 그룹에 추가
                if len(group) > 1:
                    removed_groups.append({
                        'survivorId': survivor.get('id'),
                        'survivorAnswer': survivor.get('answer', ''),
                        'duplicates': group[1:]  # 첫 번째를 제외한 나머지
                    })
        
        # duplicateCount 큰 순으로 정렬 (duplicateCount가 없는 항목은 맨 뒤로)
        unique_answers.sort(key=lambda x: x.get('duplicateCount', 0), reverse=True)
        
        return unique_answers, removed_groups
    
    def process_and_save(self) -> None:
        """중복 제거 처리 및 파일 저장"""
        print('🔍 Processing duplicate removal...')
        
        # 데이터 로드
        answers = self.load_answers()
        
        # 중복 제거 처리
        unique_answers, removed_groups = self.remove_duplicates(answers)
        
        # 결과 저장
        self.save_json_file(unique_answers, 'answers_unique.json')
        self.save_json_file(removed_groups, 'answers_removed.json')
        
        # 통계 출력
        total_removed = sum(len(group['duplicates']) for group in removed_groups)
        removal_rate = (total_removed / len(answers)) * 100 if len(answers) > 0 else 0
        duplicate_group_rate = (len(removed_groups) / len(unique_answers)) * 100 if len(unique_answers) > 0 else 0
        
        print(f'✨ Original answers: {len(answers)}')
        print(f'✨ Unique answers: {len(unique_answers)}')
        print(f'✨ Removed duplicates: {total_removed}')
        print(f'✨ Duplicate groups: {len(removed_groups)}')
        print(f'📊 Removal rate: {removal_rate:.2f}%')
        print(f'📊 Duplicate group rate: {duplicate_group_rate:.2f}%')
    
    def run(self) -> None:
        """중복 제거 실행"""
        print('🚀 Starting Duplicate Removal')
        
        try:
            self.process_and_save()
            print('✅ Duplicate removal completed successfully!')
            
        except Exception as error:
            print(f'❌ Duplicate removal failed: {error}')
            raise


def main():
    """메인 함수"""
    remover = DuplicateRemover()
    remover.run()


if __name__ == "__main__":
    main()