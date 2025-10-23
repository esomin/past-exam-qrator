# Category Classification with Duplicate Detection

## 개요

카테고리 분류 기능에 SimilarityDeduplicator의 핵심 로직을 통합하여 중복 검출 기능을 추가했습니다. 이제 카테고리별로 분류하면서 동시에 유사한 답변들을 자동으로 검출하고 마킹합니다.

## 주요 변경사항

### 1. SimilarityDeduplicator 완전 제거 및 통합
- `remove_similarity_duplicates.py` 파일 완전 삭제
- 임시 디렉토리 생성 및 파일 저장 로직 제거
- 로깅 및 통계 출력 등 부수적 기능 제거
- 핵심 중복 검출 알고리즘을 `classify_by_category()` 함수에 직접 통합

### 2. `classify_by_category()` 함수 개선
- category1 기준 그룹화 + 각 그룹 내 중복 검출
- TF-IDF + 코사인 유사도 기반 중복 검출
- 유사도 임계값: 0.8 (80% 이상 유사시 중복으로 판단)

## 추가된 데이터 속성

### 1. 독립적인 항목 (중복 그룹 없음)

중복 그룹이 없는 독립적인 항목

```json
{
  "isUnique": true,           // 유일성 여부 (항상 true)
  "similarityCount": null,    // 중복 그룹 없음 (null)
  "similarity": null          // 유사도 없음 (null)
}
```

### 2. 중복 그룹 내 대표 항목

중복 그룹 내에서 선정된 대표 항목 (가장 긴 답변)

```json
{
  "isUnique": true,           // 유일성 여부 (true - 대표 항목)
  "similarityCount": 3,       // 대표항목 포함 전체 중복 개수
  "similarity": 1.0000        // 자기 자신과의 유사도 (1.0000)
}
```

### 3. 중복 그룹 내 중복 항목

중복 그룹 내의 중복된 항목

```json
{
  "isUnique": false,          // 유일성 여부 (false - 중복 항목)
  "similarityCount": 3,       // 대표항목 포함 전체 중복 개수
  "similarity": 0.8924        // 대표 항목과의 유사도 (소숫점 넷째자리)
}
```

## 중복 검출 알고리즘

### 1. 텍스트 전처리
- HTML 태그 제거
- 숫자 정규화 (연도, 퍼센트, 번호 등)
- 조사/어미 간소화 (`입니다` → `이다`, `습니다` → `다`)
- 특수문자 제거 및 공백 정규화
- 길이 1인 토큰 제거

### 2. TF-IDF 벡터화
- **TF (Term Frequency)**: 단어 빈도 계산 및 정규화
- **IDF (Inverse Document Frequency)**: 역문서 빈도 계산
- 각 답변을 TF-IDF 벡터로 변환

### 3. 유사도 계산
- **코사인 유사도**: 두 벡터 간의 각도 기반 유사도
- **임계값**: 0.8 (80% 이상 유사시 중복으로 판단)

### 4. 사전 필터링 (성능 최적화)
- 길이 차이가 3배 이상인 경우 비교 제외
- 토큰 수 차이가 2.5배 이상인 경우 비교 제외
- 공통 토큰 비율이 30% 미만인 경우 비교 제외

### 5. 대표 항목 선정 기준
- **기준**: 중복 그룹 내에서 **가장 긴 답변**을 대표로 선정
- **이유**: 긴 답변이 더 상세하고 완전한 정보를 포함할 가능성이 높음
- **측정**: `answer` 필드의 문자열 길이 기준

## 처리 과정

### 1. 카테고리별 그룹화
```
category1 기준으로 데이터를 그룹화
├── "수학"
├── "영어"
├── "과학"
└── ...
```

### 2. 각 카테고리 내 중복 검출
```
각 카테고리 그룹 내에서:
1. 텍스트 전처리
2. TF-IDF 벡터 생성
3. 유사도 계산
4. 중복 마킹 및 속성 추가
```

### 3. 정렬 및 결과 생성
```
정렬 순서:
1. similarityCount (중복 그룹이 있는 것 먼저, 내림차순)
2. category2 (오름차순)
3. id (오름차순)
```

## 사용 예시

### API 요청
```json
{
  "file_data": "base64_encoded_json_content",
  "filename": "questions.json",
  "options": ["category"]
}
```

### API 응답 예시
```json
{
  "success": true,
  "results": [
    {
      "type": "category",
      "filename": "questions_카테고리별.json",
      "download_id": "uuid"
    }
  ]
}
```

### 결과 데이터 구조
```json
{
  "수학": [
    {
      "id": 1001,
      "question": "다음 중 올바른 것은?",
      "answer": "정답은 A입니다. 이는 대수학의 기본 원리에 따른 것입니다.",
      "category1": "수학",
      "category2": "대수",
      "isUnique": true,
      "similarityCount": 2,
      "similarity": 1.0000
    },
    {
      "id": 1002,
      "question": "다음 중 맞는 것은?",
      "answer": "답은 A입니다.",
      "category1": "수학",
      "category2": "대수",
      "isUnique": false,
      "similarityCount": 2,
      "similarity": 0.8924
    },
    {
      "id": 1003,
      "question": "독립적인 문제입니다.",
      "answer": "이것은 유일한 답변입니다.",
      "category1": "수학",
      "category2": "기하",
      "isUnique": true,
      "similarityCount": null,
      "similarity": null
    }
  ]
}
```

## 성능 최적화

### 1. 사전 필터링
- 불필요한 유사도 계산을 줄여 성능 향상
- 길이, 토큰 수, 공통 토큰 비율 기반 필터링

### 2. 카테고리별 분할 처리
- 전체 데이터를 한 번에 처리하지 않고 카테고리별로 분할
- 메모리 사용량 최적화 및 처리 속도 향상

### 3. 벡터화 최적화
- 카테고리별로 독립적인 어휘 사전 생성
- 불필요한 차원 축소로 계산 효율성 증대

## 프론트엔드 연동

### 1. 옵션 활성화
- `FileProcessorPage.tsx`에서 category 옵션 활성화
- `disabled: false`로 설정

### 2. 결과 표시
- `ResultsDisplay.tsx`에서 중복 정보 표시 가능
- `isUnique`, `similarityCount`, `similarity` 등 활용

### 3. 통계 정보 표시
카테고리 분류 선택 시 추가 통계 정보가 표시됩니다:

```typescript
interface CategoryStatistics {
  total_items: number;           // 전체 항목 수
  duplicate_items: number;       // 중복 항목 수
  unique_items: number;          // 유일 항목 수 (대표 항목 + 독립 항목)
  duplicate_percentage: number;  // 중복 비율 (%)
  unique_percentage: number;     // 유일 비율 (%)
}
```

**표시 예시:**
- "제거된 중복 선택지 수: 245개 (12.3%)"
- "중복제거 최종 선택지 수: 1,755개 (87.7%)"

### 4. 필터링 기능
- 중복 항목 숨기기/보이기 토글
- 대표 항목만 표시 옵션

## 향후 개선 방향

### 1. 임계값 조정 기능
- 사용자가 유사도 임계값을 조정할 수 있는 옵션 추가
- 0.7, 0.8, 0.9 등 다양한 임계값 제공

### 2. 중복 검출 범위 확장
- 카테고리 간 중복 검출 옵션
- 전체 데이터셋 대상 중복 검출

### 3. 성능 개선
- 병렬 처리를 통한 속도 향상
- 캐싱을 통한 반복 계산 최적화

### 4. 시각화 기능
- 중복 그룹 시각화
- 유사도 분포 차트

## 마크다운 변환 특별 처리

### 카테고리 분류 결과의 마크다운 변환 시:

1. **제외되는 컬럼**: `category1`, `category2` 자동 제외
2. **`isUnique` 컬럼 특별 처리**:
   - `true` → "O" 표시
   - `false` → 빈값 표시
3. **정렬 순서 유지**: similarityCount → category2 → id 순서 그대로 표시

## 기술적 세부사항

### 알고리즘 복잡도
- **시간 복잡도**: O(n²) (카테고리 내 모든 쌍 비교)
- **공간 복잡도**: O(n×v) (n: 항목 수, v: 어휘 크기)

### 메모리 사용량
- 카테고리별 분할 처리로 메모리 사용량 최적화
- 대용량 데이터셋 처리 가능

### 정확도
- TF-IDF + 코사인 유사도: 높은 정확도
- 한국어 텍스트 특성을 고려한 전처리
- 임계값 0.8: 적절한 정밀도/재현율 균형

## 결론

카테고리 분류와 중복 검출을 통합하여 더욱 효율적이고 유용한 기능을 제공합니다. 사용자는 카테고리별로 정리된 데이터에서 중복된 내용을 쉽게 식별하고 관리할 수 있습니다.