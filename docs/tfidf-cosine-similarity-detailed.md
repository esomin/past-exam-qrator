# TF-IDF + 코사인 유사도 상세 구현 가이드

## TF-IDF + 코사인 유사도 원리

### TF-IDF (Term Frequency-Inverse Document Frequency)
```python
# TF (단어 빈도): 문서에서 특정 단어가 얼마나 자주 나타나는가
# IDF (역문서 빈도): 전체 문서에서 특정 단어가 얼마나 희귀한가
# TF-IDF = TF × IDF (자주 나오지만 희귀한 단어일수록 높은 점수)
```

### 코사인 유사도
```python
# 두 벡터 간의 각도를 측정 (0~1 사이 값)
# 1에 가까울수록 유사, 0에 가까울수록 다름
# 문서 길이에 영향받지 않음 (정규화됨)
```

## 기출문제 답변옵션 적용 예시

### 예시 데이터
```python
answers = [
    "대한민국의 수도는 서울이다",
    "우리나라 수도는 서울입니다", 
    "한국의 수도는 부산이다",
    "서울은 대한민국의 수도이다",
    "파리는 프랑스의 수도이다"
]
```

### 처리 과정
```python
# 1단계: 전처리
"대한민국의 수도는 서울이다" → ["대한민국", "수도", "서울"]
"우리나라 수도는 서울입니다" → ["우리나라", "수도", "서울"]

# 2단계: TF-IDF 벡터화
# 각 답변을 숫자 벡터로 변환
# [대한민국, 우리나라, 수도, 서울, 부산, 파리, 프랑스, ...]
답변1: [0.5, 0.0, 0.3, 0.4, 0.0, 0.0, 0.0, ...]
답변2: [0.0, 0.5, 0.3, 0.4, 0.0, 0.0, 0.0, ...]

# 3단계: 코사인 유사도 계산
답변1 vs 답변2 = 0.85 (매우 유사)
답변1 vs 답변3 = 0.45 (보통)
답변1 vs 답변5 = 0.1 (다름)
```

## 구현 방법 옵션

### Option 1: scikit-learn 사용 (간단)
```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# 장점: 구현 간단, 검증된 라이브러리
# 단점: 외부 의존성, 한국어 처리 한계
```

### Option 2: 직접 구현 (커스터마이징)
```python
import math
from collections import Counter

# 장점: 한국어 특화 가능, 세밀한 제어
# 단점: 구현 복잡도 높음
```

## 한국어 특화 고려사항

### 형태소 분석
```python
# KoNLPy 사용 예시
"대한민국의 수도는 서울이다"
→ ["대한민국", "수도", "서울"] (명사만 추출)
→ 조사, 어미 제거로 핵심 의미 집중
```

### 동의어 처리
```python
# 기출문제에서 자주 나타나는 동의어들
synonyms = {
    "대한민국": ["한국", "우리나라"],
    "수도": ["중심지", "본부"],
    "이다": ["입니다", "임", "다"]
}
```

### 숫자/날짜 정규화
```python
# "2023년" → "YEAR"
# "50%" → "PERCENT" 
# "1번" → "NUMBER"
# 의미는 같지만 표현이 다른 경우 통일
```

## 임계값 설정 전략

### 단계별 임계값
```python
# 0.9 이상: 거의 동일 (확실한 중복)
# 0.8-0.9: 매우 유사 (중복 가능성 높음)
# 0.7-0.8: 유사 (수동 검토 필요)
# 0.7 미만: 다른 답변
```

### 적응적 임계값
```python
# 답변 길이에 따라 임계값 조정
# 짧은 답변: 높은 임계값 (0.85)
# 긴 답변: 낮은 임계값 (0.75)
```

## 성능 최적화

### 사전 필터링
```python
# 1. 길이 차이가 3배 이상이면 비교 제외
# 2. 공통 단어가 30% 미만이면 제외
# 3. 첫 글자가 다르면 제외 (선택적)
```

### 클러스터링 활용
```python
# 유사한 답변들을 그룹으로 묶어서
# 그룹 내에서만 상세 비교
# O(n²) → O(n log n) 성능 개선
```

## 구현 단계별 가이드

### 1단계: 기본 TF-IDF 구현
```python
def calculate_tf(text_tokens):
    """단어 빈도 계산"""
    tf_dict = {}
    total_words = len(text_tokens)
    for word in text_tokens:
        tf_dict[word] = tf_dict.get(word, 0) + 1
    # 정규화
    for word in tf_dict:
        tf_dict[word] = tf_dict[word] / total_words
    return tf_dict

def calculate_idf(documents):
    """역문서 빈도 계산"""
    import math
    N = len(documents)
    idf_dict = {}
    all_words = set(word for doc in documents for word in doc)
    
    for word in all_words:
        containing_docs = sum(1 for doc in documents if word in doc)
        idf_dict[word] = math.log(N / containing_docs)
    
    return idf_dict
```

### 2단계: 코사인 유사도 계산
```python
def cosine_similarity(vec1, vec2):
    """두 벡터 간의 코사인 유사도 계산"""
    import math
    
    dot_product = sum(vec1[i] * vec2[i] for i in range(len(vec1)))
    magnitude1 = math.sqrt(sum(vec1[i] ** 2 for i in range(len(vec1))))
    magnitude2 = math.sqrt(sum(vec2[i] ** 2 for i in range(len(vec2))))
    
    if magnitude1 == 0 or magnitude2 == 0:
        return 0
    
    return dot_product / (magnitude1 * magnitude2)
```

### 3단계: 전체 파이프라인 구성
```python
def find_similar_answers(answers, threshold=0.8):
    """유사한 답변들을 찾아서 그룹화"""
    # 1. 전처리
    processed_answers = [preprocess_text(answer) for answer in answers]
    
    # 2. TF-IDF 벡터화
    tfidf_vectors = create_tfidf_vectors(processed_answers)
    
    # 3. 유사도 계산 및 그룹화
    similar_groups = []
    processed_indices = set()
    
    for i in range(len(answers)):
        if i in processed_indices:
            continue
            
        current_group = [i]
        for j in range(i + 1, len(answers)):
            if j in processed_indices:
                continue
                
            similarity = cosine_similarity(tfidf_vectors[i], tfidf_vectors[j])
            if similarity >= threshold:
                current_group.append(j)
                processed_indices.add(j)
        
        similar_groups.append(current_group)
        processed_indices.add(i)
    
    return similar_groups
```

이런 방식으로 구현하면 기출문제 답변옵션의 의미적 중복을 효과적으로 제거할 수 있습니다.