#!/usr/bin/env python3
"""
간단한 API 테스트 - category 옵션 문제 확인
"""

import json
import base64
from pathlib import Path

# 작은 테스트 데이터 생성 (올바른 구조)
test_data = [
    {
        "id": 1,
        "title": "지방자치에 대한 설명으로 옳은 것은?",
        "text": "",
        "titleType": "POSITIVE",
        "categoryTitle": "행정학",
        "answerSet": [
            {"id": 1, "title": "지방자치는 민주주의의 기초이다", "answerKind": "O"},
            {"id": 2, "title": "지방자치는 중앙집권을 의미한다", "answerKind": "X"}
        ],
        "solve": "2023년 행정고시"
    },
    {
        "id": 2,
        "title": "공무원의 의무에 관한 내용으로 틀린 것은?", 
        "text": "",
        "titleType": "NEGATIVE",
        "categoryTitle": "행정학",
        "answerSet": [
            {"id": 3, "title": "성실의무를 져야 한다", "answerKind": "O"},
            {"id": 4, "title": "복무규정을 무시할 수 있다", "answerKind": "X"}
        ],
        "solve": "2022년 지방고시"
    }
]

# 테스트 파일 저장
with open('data/test_small.json', 'w', encoding='utf-8') as f:
    json.dump(test_data, f, ensure_ascii=False, indent=2)

print("Small test file created: data/test_small.json")

# Base64 인코딩
json_content = json.dumps(test_data, ensure_ascii=False)
file_data = base64.b64encode(json_content.encode('utf-8')).decode('utf-8')

# API 요청 데이터
payload = {
    "file_data": file_data,
    "filename": "test_small.json",
    "options": ["category"]
}

# curl 명령어 생성
curl_command = f"""curl -X POST http://localhost:5001/api/process \\
  -H "Content-Type: application/json" \\
  -d '{json.dumps(payload)}'"""

print("\nCurl command to test API:")
print(curl_command)

# 파일로도 저장
with open('test_payload.json', 'w', encoding='utf-8') as f:
    json.dump(payload, f, ensure_ascii=False, indent=2)

print("\nPayload saved to: test_payload.json")
print("You can also test with: curl -X POST http://localhost:5001/api/process -H 'Content-Type: application/json' -d @test_payload.json")