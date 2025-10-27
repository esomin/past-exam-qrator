# 파일 업로드 에러 처리 개선

## 문제점
5MB 이상의 파일을 업로드하면 API 요청이 실패하지만 아무 응답이 오지 않아 사용자가 원인을 파악하기 어려웠습니다.

## 개선 사항

### 1. 프론트엔드 (src/services/api.ts)

#### 파일 크기 제한 증가
- 기존: 10MB → 변경: 50MB
- 대용량 파일 처리를 위한 제한 완화

#### 타임아웃 설정 개선
- 기본 타임아웃: 30초 → 120초
- 10MB 이상 파일: 120초 → 300초 (5분)
- 파일 크기에 따라 동적으로 타임아웃 조정

#### 상세한 에러 로깅 추가
```typescript
// 에러 발생 시 다음 정보를 콘솔에 출력:
- 에러 메시지 및 코드
- HTTP 상태 코드
- 요청 URL 및 메서드
- 요청 데이터 크기
- 타임아웃 설정
```

#### 파일 처리 진행 상황 로깅
```typescript
// 각 단계별 로그 출력:
1. 파일 검증: "File validation: filename.json, Size: 15.23MB"
2. Base64 변환: "Starting file conversion: filename.json (15.23MB)"
3. 변환 완료: "File converted to base64: 20.31MB"
4. 요청 전송: "Sending request to server: 20.31MB"
5. 업로드 진행률: "Upload progress: 45%"
6. 응답 수신: "Server response received successfully"
```

#### 에러 메시지 개선
- `ECONNABORTED`: "Request timeout. The file may be too large..."
- `ERR_NETWORK`: "Network error. Unable to reach the server..."
- `timeout`: "Request timeout. The operation took too long..."
- 각 에러 타입별로 구체적인 원인과 해결 방법 제시

#### 대용량 파일 처리 최적화
- 10MB 이상 파일은 재시도 비활성화 (타임아웃 방지)
- 업로드 진행률 표시 추가
- 파일 크기에 따른 경고 메시지 출력

### 2. 프론트엔드 (src/pages/FileProcessorPage.tsx)

#### 파일 처리 전 검증 강화
```typescript
// 처리 시작 전 파일 크기 확인 및 경고
- 전체 파일 크기 계산
- 10MB 이상 파일 감지 및 경고 로그
- 대용량 파일 처리 시 사용자에게 안내 메시지 표시
```

#### 에러 처리 개선
```typescript
// 에러 타입별 맞춤 메시지:
- TIMEOUT_ERROR: "Processing timeout - file may be too large"
- NETWORK_ERROR: "Network error - unable to reach server"
- FILE_TOO_LARGE: "File too large"
- 각 에러에 대한 구체적인 해결 방법 제시
```

### 3. 백엔드 (python/app.py)

#### Flask 설정 추가
```python
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB 최대 요청 크기
app.config['JSON_AS_ASCII'] = False  # 한글 처리 개선
```

#### 요청 로깅 강화
```python
# 각 API 엔드포인트에서 다음 정보 로깅:
- 요청 크기 (MB)
- 클라이언트 IP
- Base64 데이터 크기
- 디코딩된 JSON 크기
- 파싱된 항목 수
```

#### 에러 처리 개선
```python
# 단계별 에러 처리:
1. Base64 디코딩 실패 → "Failed to decode base64 data"
2. JSON 파싱 실패 → "Invalid JSON format"
3. 파일 크기 초과 → "File too large: X.XMB (max: 100MB)"
4. 메모리 부족 → "File too large to process - insufficient memory"
```

#### 새로운 에러 핸들러 추가
```python
@app.errorhandler(413)
def request_entity_too_large(error):
    # 요청 크기 초과 시 명확한 에러 메시지 반환
```

#### 상세한 에러 로깅
```python
# 모든 에러에 대해 스택 트레이스 포함:
app.logger.error(f"Error message", exc_info=True)
```

## 사용자 경험 개선

### 이전
- 5MB 이상 파일 업로드 시 무응답
- 에러 원인 파악 불가
- 브라우저 콘솔에 정보 없음

### 개선 후
- 파일 크기 및 처리 진행 상황 실시간 표시
- 구체적인 에러 메시지 및 해결 방법 제시
- 브라우저 콘솔에서 상세한 디버깅 정보 확인 가능
- 대용량 파일 처리 시 적절한 타임아웃 설정
- 네트워크 에러, 타임아웃, 파일 크기 초과 등 각 상황별 맞춤 안내

## 디버깅 방법

### 브라우저 콘솔 확인
1. 개발자 도구 열기 (F12)
2. Console 탭 선택
3. 파일 업로드 시 다음 로그 확인:
   - 파일 검증 정보
   - Base64 변환 진행 상황
   - 요청 크기 및 설정
   - 업로드 진행률
   - 에러 상세 정보

### 서버 로그 확인
```bash
# Python 백엔드 로그 확인
# 다음 정보가 출력됨:
- 요청 수신 정보 (크기, IP)
- 파일 처리 단계별 진행 상황
- 에러 발생 시 스택 트레이스
```

## 테스트 권장 사항

1. **소형 파일 (< 5MB)**: 정상 동작 확인
2. **중형 파일 (5-10MB)**: 처리 시간 및 진행 상황 표시 확인
3. **대형 파일 (10-50MB)**: 타임아웃 설정 및 에러 처리 확인
4. **초대형 파일 (> 50MB)**: 적절한 에러 메시지 표시 확인
5. **네트워크 불안정**: 재시도 로직 및 에러 복구 확인

## 향후 개선 가능 사항

1. 파일 청크 업로드 (대용량 파일을 여러 조각으로 나누어 전송)
2. 업로드 진행률 UI 표시
3. 백그라운드 처리 및 알림 기능
4. 파일 압축 전송
5. 서버 측 스트리밍 처리
