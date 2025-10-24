# Category Option 유사도 선별 로직

## 개요
`classify_by_category` 함수에서 구현된 유사도 선별 로직은 TF-IDF 벡터화와 코사인 유사도를 사용하여 같은 카테고리 내에서 의미적으로 유사한 답변들을 자동으로 식별하고 중복을 제거합니다.

## 1. 텍스트 전처리 (`preprocess_text`)

### 목적
원시 텍스트를 정규화하고 토큰화하여 유사도 계산에 적합한 형태로 변환

### 처리 단계
```python
def preprocess_text(text: str) -> List[str]:
    # 1. HTML 태그 제거
    text = re.sub(r'<[^>]+>', '', text)
    
    # 2. 숫자 정규화 (연도, 퍼센트, 번호 등)
    text = re.sub(r'\d{4}년', 'YEAR년', text)
    text = re.sub(r'\d+%', 'PERCENT', text)
    text = re.sub(r'\d+번', 'NUMBER번', text)
    text = re.sub(r'\d+\.', 'NUMBER.', text)
    
    # 3. 특수문자 제거 및 공백 정규화
    text = re.sub(r'[^\w\s가-힣]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    
    # 4. 조사, 어미 간소화
    text = re.sub(r'입니다', '이다', text)
    text = re.sub(r'습니다', '다', text)
    text = re.sub(r'에서', '에', text)
    
    # 5. 토큰화 및 짧은 토큰 제거
    tokens = [token for token in text.strip().split() if len(token) > 1]
    return tokens
```

### 정규화 효과
- **숫자 정규화**: "2023년", "2024년" → "YEAR년"으로 통일
- **퍼센트 정규화**: "50%", "80%" → "PERCENT"로 통일
- **조사/어미 간소화**: 문법적 변화를 줄여 의미 중심 비교

## 2. TF-IDF 벡터화

### TF (Term Frequency) 계산
```python
def calculate_tf(tokens: List[str]) -> Dict[str, float]:
    tf_dict = Counter(tokens)
    total_words = len(tokens)
    
    # 정규화: 단어빈도 / 전체단어수
    for word in tf_dict:
        tf_dict[word] = tf_dict[word] / total_words
    
    return dict(tf_dict)
```

### IDF (Inverse Document Frequency) 계산
```python
def calculate_idf(documents: List[List[str]]) -> Dict[str, float]:
    N = len(documents)  # 전체 문서 수
    
    for word in all_words:
        containing_docs = sum(1 for doc in documents if word in doc)
        if containing_docs > 0:
            idf_dict[word] = math.log(N / containing_docs)
```

### TF-IDF 벡터 생성
각 답변을 수치 벡터로 변환하여 수학적 유사도 계산 가능

## 3. 사전 필터링 (`should_skip_comparison`)

### 목적
명백히 다른 답변들을 사전에 걸러내어 성능 최적화

### 필터링 조건
```python
def should_skip_comparison(answer1, answer2, tokens1, tokens2):
    # 1. 길이 차이가 3배 이상
    ratio = max(len1, len2) / min(len1, len2)
    if ratio > 3.0:
        return True
    
    # 2. 토큰 수 차이가 2.5배 이상
    token_ratio = max(token_len1, token_len2) / min(token_len1, token_len2)
    if token_ratio > 2.5:
        return True
    
    # 3. 공통 토큰이 30% 미만
    common_ratio = len(common_tokens) / total_unique_tokens
    if common_ratio < 0.3:
        return True
    
    return False
```

### 필터링 효과
- **성능 향상**: 불필요한 유사도 계산 제거
- **정확도 향상**: 명백히 다른 텍스트 간 오판 방지

## 4. 코사인 유사도 계산

### 공식
```python
def cosine_similarity(vec1, vec2):
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = math.sqrt(sum(a * a for a in vec1))
    magnitude2 = math.sqrt(sum(b * b for b in vec2))
    
    return dot_product / (magnitude1 * magnitude2)
```

### 특징
- **범위**: 0.0 ~ 1.0 (0: 완전히 다름, 1: 완전히 같음)
- **각도 기반**: 벡터 간의 각도를 측정하여 방향성 유사도 계산
- **크기 무관**: 텍스트 길이에 상관없이 의미적 유사성 측정

## 5. 유사도 임계값 및 중복 판단

### 임계값 설정
```python
threshold = similarity_threshold  # 사용자 설정 가능 (기본값: 0.8)
```

### 프론트엔드 설정
- **범위**: 0.5 ~ 0.95 (50% ~ 95%)
- **기본값**: 0.8 (80%)
- **단계**: 0.05 (5% 단위)
- **UI**: 슬라이더 형태로 직관적 조정 가능

### 중복 그룹 형성
- **유사도 ≥ 0.8**: 같은 중복 그룹으로 분류
- **대표 선정**: 가장 긴 답변을 그룹 대표로 선택
- **속성 부여**:
  - `isUnique: true` (대표 항목)
  - `isUnique: false` (중복 항목)
  - `similarity`: 대표 항목과의 유사도 값 (소수점 4자리)
  - `similarityCount`: 중복 그룹 내 총 항목 수

## 6. 정렬 및 결과 생성

### 정렬 우선순위

#### 1단계: 중복 그룹별 그룹화
- 같은 `similarityCount`를 가진 항목들을 하나의 그룹으로 묶음
- 대표 항목(`isUnique: true`)의 ID를 그룹 식별자로 사용

#### 2단계: 각 중복 그룹 내 정렬
```python
group_items.sort(key=lambda x: (
    not x.get('isUnique', False),        # 1순위: isUnique=True가 먼저
    -(x.get('similarity') or 0),         # 2순위: 유사도 높은 순
    x.get('id', 0)                       # 3순위: ID 오름차순
))
```

#### 3단계: 고유 항목 정렬
```python
unique_items.sort(key=lambda x: (
    x.get('category2', ''),              # 1순위: category2 오름차순
    x.get('id', 0)                       # 2순위: id 오름차순
))
```

#### 4단계: 최종 배치
- 중복 그룹들 (그룹 ID 순서대로)
- 고유 항목들

### 결과 구조
- **category**: 중복 포함 전체 결과 (repId 포함)
- **category_deduplicated**: 대표 항목만 포함된 중복 제거 결과 (repId 제외)

## 7. 통계 정보

### 제공 통계
```python
category_stats = {
    'total_items': 전체_항목_수,
    'duplicate_items': 중복_항목_수,
    'unique_items': 고유_항목_수,
    'duplicate_percentage': 중복률_백분율,
    'unique_percentage': 고유율_백분율
}
```

## 8. 알고리즘 특징

### 장점
- **의미 기반 비교**: 단순 문자열 매칭이 아닌 의미적 유사성 측정
- **정규화 효과**: 숫자, 조사 등의 변화에 강건함
- **성능 최적화**: 사전 필터링으로 불필요한 계산 제거
- **투명성**: 유사도 값과 통계 정보 제공

### 한계
- **언어 의존적**: 한국어 특화 전처리 규칙
- **계산 복잡도**: O(n²) 시간 복잡도
- **임계값 범위**: 0.5~0.95로 제한 (극단값 방지)

## 9. 사용 예시

### 입력 예시
```
답변1: "2023년 정부 정책은 경제 성장을 목표로 합니다."
답변2: "2024년 정부 정책은 경제 성장을 목표로 한다."
답변3: "환경 보호는 중요한 과제입니다."
```

### 처리 결과
```
답변1: isUnique=true, similarity=1.0000, similarityCount=2 (대표)
답변2: isUnique=false, similarity=0.8542, similarityCount=2 (중복)
답변3: isUnique=true, similarity=null, similarityCount=null (고유)
```

## 10. 성능 고려사항

### 메모리 최적화
- 대용량 데이터셋의 경우 청크 단위 처리
- 임시 벡터 데이터 즉시 해제

### 처리 시간
- 사전 필터링으로 약 60-70% 계산량 감소
- 카테고리별 독립 처리로 병렬화 가능
#
# 11. 유사도 임계값 설정 기능

### 프론트엔드 UI
- **위치**: Category 옵션 선택 시 자동 표시
- **형태**: 슬라이더 컨트롤
- **범위**: 50% ~ 95% (0.5 ~ 0.95)
- **기본값**: 80% (0.8)
- **단계**: 5% 단위 (0.05)

### 임계값별 특성
- **95% (0.95)**: 매우 엄격한 중복 검출 (거의 동일한 답변만 중복으로 판단)
- **90% (0.90)**: 엄격한 중복 검출 (매우 유사한 답변만 중복으로 판단)
- **80% (0.80)**: 권장 설정 (적절한 수준의 중복 검출)
- **70% (0.70)**: 보통 중복 검출 (어느 정도 유사한 답변도 중복으로 판단)
- **60% (0.60)**: 관대한 중복 검출 (상당히 다른 답변도 중복으로 판단)
- **50% (0.50)**: 매우 관대한 중복 검출 (최소 수준의 유사성만으로도 중복 판단)

### API 요청 형식
```json
{
  "file_data": "base64_encoded_json_content",
  "filename": "original_filename.json",
  "options": ["category"],
  "similarity_threshold": 0.8
}
```

### 실시간 피드백
- 슬라이더 조정 시 실시간으로 설정값 표시
- 각 임계값에 대한 설명 텍스트 제공
- 시각적 가이드라인으로 사용자 이해도 향상

### 사용 권장사항
- **첫 사용자**: 기본값 0.8 사용 권장
- **엄격한 중복 제거**: 0.85~0.9 사용
- **관대한 중복 제거**: 0.7~0.75 사용
- **테스트 목적**: 다양한 값으로 실험하여 최적값 찾기## 12. 
개선된 정렬 시스템

### 중복 그룹 연속 배치 ✅
같은 중복 그룹의 모든 항목이 연속으로 나오도록 정렬됩니다.

### 대표항목 ID 추가 ✅
- **속성명**: `repId`
- **대표항목**: `repId: null`
- **중복항목**: `repId: 대표항목의_ID`

### 그룹 내 정렬 순서
1. **대표 항목 우선**: `isUnique: true`인 항목이 맨 앞
2. **유사도 순서**: 중복 항목들은 유사도 높은 순서대로
3. **ID 순서**: 동일한 조건일 때 ID 오름차순

### 실제 정렬 예시
```json
[
  // 중복그룹 1 (대표항목 ID: 101)
  {
    "id": 101,
    "isUnique": true,
    "similarity": 1.0000,
    "similarityCount": 3,
    "repId": null
  },
  {
    "id": 205,
    "isUnique": false,
    "similarity": 0.8542,
    "similarityCount": 3,
    "repId": 101
  },
  {
    "id": 308,
    "isUnique": false,
    "similarity": 0.8234,
    "similarityCount": 3,
    "repId": 101
  },
  
  // 중복그룹 2 (대표항목 ID: 150)
  {
    "id": 150,
    "isUnique": true,
    "similarity": 1.0000,
    "similarityCount": 2,
    "repId": null
  },
  {
    "id": 267,
    "isUnique": false,
    "similarity": 0.8756,
    "similarityCount": 2,
    "repId": 150
  },
  
  // 고유항목들
  {
    "id": 89,
    "isUnique": true,
    "similarity": null,
    "similarityCount": null,
    "repId": null
  }
]
```

### 정렬 장점
- **가독성 향상**: 중복 그룹을 한눈에 파악 가능
- **검토 효율성**: 대표 항목과 중복 항목을 쉽게 비교
- **유사도 기반**: 가장 유사한 항목부터 순서대로 확인 가능
- **대표항목 추적**: `repId`로 어떤 항목이 대표인지 즉시 확인 가능## 
13. 결과 파일별 속성 차이

### category (전체 결과)
```json
{
  "id": 101,
  "question": "문제 내용",
  "answer": "답변 내용",
  "category1": "카테고리1",
  "category2": "카테고리2",
  "institution": "기관명",
  "year": "연도",
  "answerKind": "O",
  "isCorrect": true,
  "commentary": "해설",
  "isUnique": true,
  "similarity": 1.0000,
  "similarityCount": 3,
  "repId": null  // ✅ 포함
}
```

### category_deduplicated (중복제거 결과)
```json
{
  "id": 101,
  "question": "문제 내용",
  "answer": "답변 내용",
  "category1": "카테고리1",  // ❌ markdown에서는 제외
  "category2": "카테고리2",
  "institution": "기관명",
  "year": "연도",
  "answerKind": "O",
  "isCorrect": true,
  "commentary": "해설"
  // ❌ isUnique, similarity, similarityCount, repId 모두 제외
}
```

### 제외 이유
- **repId**: 중복제거 결과에는 대표항목만 있으므로 불필요
- **isUnique**: 모든 항목이 true이므로 의미없음
- **similarity**: 중복항목이 없으므로 불필요
- **similarityCount**: 중복 그룹 정보가 불필요