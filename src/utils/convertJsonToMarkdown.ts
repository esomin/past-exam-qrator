import json2md from 'json2md'

// 마크다운 테이블용 텍스트 정리 함수
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

// 커스텀 JSON to Markdown 변환 함수
export const convertJsonToMarkdown = (jsonData: any, options?: { excludeColumns?: string[] }): string => {
  try {
    // 년도별 데이터 구조 확인 (예: {"2021": [...], "2022": [...]})
    if (typeof jsonData === 'object' && !Array.isArray(jsonData)) {
      let markdown = ''

      for (const [year, data] of Object.entries(jsonData)) {
        if (Array.isArray(data) && data.length > 0) {
          // 년도를 헤더로 추가
          markdown += `# ${year}\n\n`

          // 정의된 컬럼 순서 사용 (New Column Order Implementation)
          const orderedHeaders = [
            'id',           // Primary Information First
            'question',     // Main question content
            'answer',       // Answer/choice content
            'category1',    // Classification & Context
            'category2',    // Sub-category
            'institution',  // Exam institution
            'year',         // Exam year
            'answerKind',   // Answer Analysis
            'isCorrect',    // Correctness flag
            'commentary'    // Explanation (last for reference)
          ]

          // 제외할 컬럼들 처리
          const excludeColumns = options?.excludeColumns || []
          const filteredOrderedHeaders = orderedHeaders.filter(header => !excludeColumns.includes(header))

          // 실제 데이터에 존재하는 헤더만 필터링
          const availableHeaders = Object.keys(data[0])
          const headers = filteredOrderedHeaders.filter(header => availableHeaders.includes(header))

          // 정의된 순서에 없는 추가 헤더들도 포함 (뒤쪽에 추가) - 제외 컬럼은 빼고
          const extraHeaders = availableHeaders.filter(header =>
            !orderedHeaders.includes(header) && !excludeColumns.includes(header)
          )
          headers.push(...extraHeaders)

          // 테이블 헤더 생성 (헤더명도 정리)
          const cleanHeaders = headers.map(header => cleanTextForMarkdown(header))
          markdown += '|' + cleanHeaders.join('|') + '|\n'
          markdown += '|' + cleanHeaders.map(() => '---').join('|') + '|\n'

          // 테이블 데이터 생성
          data.forEach((item: any) => {
            const row = headers.map(header => {
              let value = item[header]

              // null 또는 undefined 처리
              if (value === null || value === undefined) {
                return '-'
              }

              // boolean 값을 대문자로 변환
              if (typeof value === 'boolean') {
                return value ? 'TRUE' : 'FALSE'
              }

              // 숫자 값 처리
              if (typeof value === 'number') {
                return value.toString()
              }

              // 문자열 값 정리
              if (typeof value === 'string') {
                return cleanTextForMarkdown(value)
              }

              // 객체나 배열인 경우 JSON 문자열로 변환 후 정리
              if (typeof value === 'object') {
                try {
                  const jsonString = JSON.stringify(value)
                  return cleanTextForMarkdown(jsonString)
                } catch (error) {
                  return '-'
                }
              }

              // 기타 타입은 문자열로 변환 후 정리
              return cleanTextForMarkdown(String(value))
            })
            markdown += '|' + row.join('|') + '|\n'
          })

          markdown += '\n'
        }
      }

      return markdown
    }

    // 기존 json2md 형식 처리
    return json2md(jsonData)
  } catch (error) {
    throw error
  }
}