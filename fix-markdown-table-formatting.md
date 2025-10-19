# 마크다운 테이블 형태 문제 해결

## 문제 상황
원본 데이터에 `\r\n\r\n` (Windows 더블 줄바꿈) 등의 줄바꿈 문자가 포함되어 있어서, 마크다운으로 변환할 때 테이블 형태가 제대로 표시되지 않는 문제가 발생했습니다.

## 문제 원인
1. **줄바꿈 문자**: `\r\n\r\n`, `\r\n`, `\n`, `\r` 등이 데이터에 포함
2. **HTML 태그**: `<p>`, `</p>` 등의 HTML 태그가 포함된 경우
3. **마크다운 특수문자**: `|`, `*`, `` ` ``, `~` 등이 이스케이프되지 않음
4. **연속 공백**: 여러 개의 공백이 연속으로 나타나는 경우

## 해결 방법

### 1. 텍스트 정리 함수 추가
`src/utils/convertJsonToMarkdown.ts`에 `cleanTextForMarkdown()` 함수를 추가:

```typescript
const cleanTextForMarkdown = (text: string): string => {
  if (!text || typeof text !== 'string') {
    return ''
  }
  
  return text
    // 다양한 줄바꿈 문자들을 공백으로 변환
    .replace(/\r\n\r\n/g, ' ')  // Windows 더블 줄바꿈
    .replace(/\r\n/g, ' ')      // Windows 줄바꿈
    .replace(/\n\n/g, ' ')      // Unix 더블 줄바꿈
    .replace(/\r/g, ' ')        // Mac 줄바꿈
    .replace(/\n/g, ' ')        // Unix 줄바꿈
    // 탭 문자를 공백으로 변환
    .replace(/\t/g, ' ')
    // HTML 태그 제거
    .replace(/<[^>]*>/g, '')
    // HTML 엔티티 디코딩
    .replace(/&nbsp;/g, ' ')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&amp;/g, '&')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    // 연속된 공백을 하나로 정리
    .replace(/\s+/g, ' ')
    // 앞뒤 공백 제거
    .trim()
    // 마크다운 특수 문자 이스케이프
    .replace(/\|/g, '\\|')      // 파이프 문자
    .replace(/\*/g, '\\*')      // 별표
    .replace(/`/g, '\\`')       // 백틱
    .replace(/~/g, '\\~')       // 틸드
    // 빈 문자열이면 대시로 표시
    || '-'
}
```

### 2. 데이터 타입별 처리 개선
- **null/undefined**: `-`로 표시
- **boolean**: `TRUE`/`FALSE`로 변환
- **number**: 문자열로 변환
- **string**: `cleanTextForMarkdown()` 함수로 정리
- **object/array**: JSON 문자열로 변환 후 정리

### 3. 헤더명도 정리
테이블 헤더에도 동일한 정리 함수를 적용하여 일관성 유지

## 처리되는 문제들

### Before (문제 상황)
```
|category2|question_title|
|---|---|
|공무원\r\n\r\n인사제도|다음은 공무원 인사제도에\r\n대한 설명이다.\r\n\r\n옳은 지문은 몇 개인가?|
```

### After (해결 후)
```
|category2|question_title|
|---|---|
|공무원 인사제도|다음은 공무원 인사제도에 대한 설명이다. 옳은 지문은 몇 개인가?|
```

## 테스트 케이스
`src/test-markdown-conversion.ts`에 다음과 같은 문제 상황들을 포함한 테스트 데이터 추가:
- `\r\n\r\n` 더블 줄바꿈
- `\r\n` 단일 줄바꿈
- `\n` Unix 줄바꿈
- HTML 태그 (`<p>`, `</p>`)
- 파이프 문자 (`|`)
- null 값

## 검증 항목
1. ✅ 년도별 헤더 생성
2. ✅ 테이블 구조 유지
3. ✅ 데이터 내용 보존
4. ✅ 더블 줄바꿈 제거
5. ✅ HTML 태그 제거
6. ✅ 파이프 문자 이스케이프
7. ✅ 텍스트 정리 및 정규화

## 결과
- 마크다운 테이블이 올바른 형태로 생성됨
- 줄바꿈 문자로 인한 테이블 구조 깨짐 현상 해결
- HTML 태그 및 특수문자 처리로 깔끔한 마크다운 생성
- 다양한 데이터 타입에 대한 안정적인 처리