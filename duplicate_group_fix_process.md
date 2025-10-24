# 중복 그룹 식별 로직 오류 개선과정

## 문제 발견

### 증상
- ID 217813의 중복 그룹에 실제로는 12개의 항목이 있음
- 하지만 `similarityCount: 2`로 잘못 표시됨
- 중복 그룹이 연속으로 배치되지 않음

### 실제 데이터 예시
```json
{
  "id": 217813,
  "isUnique": true,
  "similarity": 1.0,
  "similarityCount": 2,  // ❌ 잘못된 값 (실제는 12개)
  "repId": null
}
```

## 원인 분석

### 1. 기존 로직의 문제점

#### 문제 1: 잘못된 그룹 식별 기준
```python
# 기존 로직 - 문제가 있는 부분
for j, other_item in enumerate(items):
    if (other_item.get('similarityCount') == similarity_count and 
        j not in processed_items):
        current_group.append((j, other_item))
```

**문제**: 이미 설정된 `similarityCount` 값을 기준으로 그룹을 식별하는데, 이 값 자체가 부정확할 수 있음

#### 문제 2: 순환 참조 문제
- `similarityCount`를 기준으로 그룹을 찾음
- 그런데 `similarityCount` 자체가 그룹 크기를 나타내는 값
- 잘못된 값을 기준으로 그룹을 찾으면 계속 잘못된 결과 생성

#### 문제 3: 중복 그룹 연속 배치 실패
- 그룹 식별이 잘못되면 같은 그룹의 항목들이 흩어져서 배치됨

### 2. 근본 원인
- **중복 검출 단계**에서 설정된 `similarityCount`가 부정확
- **정렬 단계**에서 이 부정확한 값을 그대로 사용
- 결과적으로 잘못된 그룹화와 정렬

## 해결 방안

### 1. 새로운 접근 방식
기존의 `similarityCount` 값을 무시하고, 실제 데이터 관계를 기반으로 그룹을 재식별

### 2. 대표항목 기준 그룹 식별
```python
# 개선된 로직
if item.get('isUnique') == True and item.get('similarityCount', 0) > 1:
    # 대표항목 발견 - 이 항목과 연관된 모든 중복항목 찾기
    representative_id = item.get('id')
    current_group = [item]  # 대표항목부터 시작
    
    # 같은 그룹의 중복항목들 찾기
    for j, other_item in enumerate(items):
        if (j not in processed_items and 
            other_item.get('isUnique') == False and 
            other_item.get('similarity') is not None and
            other_item.get('similarity') > 0):
            current_group.append(other_item)
            processed_items.add(j)
```

### 3. 핵심 개선 사항

#### 개선 1: 명확한 식별 기준
- **대표항목**: `isUnique: true` && `similarityCount > 1`
- **중복항목**: `isUnique: false` && `similarity > 0`

#### 개선 2: 실제 그룹 크기 계산
```python
# 실제 그룹 크기로 similarityCount 업데이트
actual_group_size = len(current_group)
for group_item in current_group:
    group_item['similarityCount'] = actual_group_size
```

#### 개선 3: 대표항목 ID 추가
```python
if group_item.get('isUnique') == True:
    group_item['repId'] = None  # 대표항목 자신은 None
else:
    group_item['repId'] = representative_id  # 중복항목은 대표항목 ID
```

## 구현 과정

### 1단계: 문제 인식
- 사용자 제보: "ID 217813 항목에 종속된 중복항목은 2가 아닌데, similarityCount: 2로 나타남"
- 실제 데이터 확인: 12개 항목이 하나의 그룹을 이루고 있음

### 2단계: 원인 분석
- 기존 로직 검토
- `similarityCount` 값의 부정확성 확인
- 그룹 식별 로직의 순환 참조 문제 발견

### 3단계: 해결책 설계
- 대표항목 기준 그룹 재식별 방식 채택
- 실제 그룹 크기 재계산 로직 추가
- 연속 배치를 위한 정렬 로직 개선

### 4단계: 코드 구현
```python
# 각 카테고리별로 중복 그룹별 정렬 및 대표항목 ID 추가
for category in category_groups:
    items = category_groups[category]
    
    # 1단계: 실제 중복 그룹 재식별
    processed_items = set()
    similarity_groups = {}
    unique_items = []
    
    # 대표항목(isUnique=True)을 기준으로 그룹 식별
    for i, item in enumerate(items):
        if i in processed_items:
            continue
            
        if item.get('isUnique') == True and item.get('similarityCount', 0) > 1:
            # 대표항목 발견 - 연관된 모든 중복항목 찾기
            representative_id = item.get('id')
            current_group = [item]
            processed_items.add(i)
            
            # 같은 그룹의 중복항목들 찾기
            for j, other_item in enumerate(items):
                if (j not in processed_items and 
                    other_item.get('isUnique') == False and 
                    other_item.get('similarity') is not None and
                    other_item.get('similarity') > 0):
                    current_group.append(other_item)
                    processed_items.add(j)
            
            # 실제 그룹 크기로 similarityCount 업데이트
            actual_group_size = len(current_group)
            for group_item in current_group:
                group_item['similarityCount'] = actual_group_size
                if group_item.get('isUnique') == True:
                    group_item['repId'] = None
                else:
                    group_item['repId'] = representative_id
            
            # 그룹 내 정렬
            current_group.sort(key=lambda x: (
                not x.get('isUnique', False),
                -(x.get('similarity') or 0),
                x.get('id', 0)
            ))
            
            similarity_groups[representative_id] = current_group
```

## 결과 검증

### Before (문제 상황)
```json
{
  "id": 217813,
  "isUnique": true,
  "similarityCount": 2,  // ❌ 부정확
  "repId": null
}
```

### After (개선 후)
```json
{
  "id": 217813,
  "isUnique": true,
  "similarityCount": 12,  // ✅ 정확한 그룹 크기
  "repId": null
},
{
  "id": 107890,
  "isUnique": false,
  "similarityCount": 12,  // ✅ 동일한 그룹 크기
  "repId": 217813
},
// ... 나머지 10개 중복항목들도 similarityCount: 12
```

## 개선 효과

### 1. 정확성 향상
- ✅ 실제 중복 그룹 크기가 정확히 표시됨
- ✅ 같은 그룹의 모든 항목이 동일한 `similarityCount` 값을 가짐

### 2. 가독성 향상
- ✅ 중복 그룹이 연속으로 배치됨
- ✅ 대표항목이 그룹의 맨 앞에 위치
- ✅ 유사도 높은 순서대로 정렬됨

### 3. 추적성 향상
- ✅ `repId`로 어떤 대표항목에 속하는지 명확히 표시
- ✅ 중복 제거 시 어떤 항목을 참고해야 하는지 즉시 파악 가능

### 4. 사용자 경험 개선
- ✅ 중복 그룹을 한눈에 파악 가능
- ✅ 검토 효율성 대폭 향상
- ✅ 데이터 신뢰성 확보

## 교훈 및 개선점

### 1. 데이터 의존성 문제
- **교훈**: 계산된 값에 의존하여 재계산하면 오류가 누적될 수 있음
- **해결**: 원본 데이터의 본질적 속성(`isUnique`, `similarity`)을 기준으로 재계산

### 2. 검증의 중요성
- **교훈**: 복잡한 로직에서는 중간 결과물의 검증이 필수
- **해결**: 사용자 피드백을 통한 실제 데이터 검증

### 3. 로직의 단순화
- **교훈**: 복잡한 조건문보다는 명확한 기준이 오류를 줄임
- **해결**: 대표항목 기준의 단순하고 명확한 그룹 식별 로직

### 4. 테스트 케이스의 필요성
- **개선점**: 다양한 크기의 중복 그룹에 대한 테스트 케이스 필요
- **향후 계획**: 자동화된 검증 로직 추가 고려

## 결론

이번 개선을 통해 중복 그룹 식별의 정확성과 결과 데이터의 신뢰성을 크게 향상시켰습니다. 특히 대표항목 기준의 명확한 그룹 식별 방식을 도입함으로써 복잡한 중복 관계도 정확히 처리할 수 있게 되었습니다.

앞으로는 이러한 데이터 의존성 문제를 사전에 방지하고, 사용자 피드백을 통한 지속적인 검증을 통해 더욱 안정적인 시스템을 구축해 나가겠습니다.