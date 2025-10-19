// Test script for markdown conversion functionality
import { convertJsonToMarkdown } from './utils/convertJsonToMarkdown'

// Test data similar to what the backend would return (with problematic characters)
const testData = {
  "2021": [
    {
      "id": 76823,
      "question": "다음은 공무원 인사제도에\r\n대한 설명이다.\r\n\r\n옳은 지문은 몇 개인가?",
      "answer": "0개",
      "category1": "1) 인사행정의 기초",
      "category2": "공무원\r\n\r\n인사제도",
      "institution": "경찰간부",
      "year": "2021",
      "answerKind": "X",
      "isCorrect": false,
      "commentary": "설명 내용"
    },
    {
      "id": 76824,
      "question": "다음은 공무원 인사제도에 대한 설명이다. 옳은 지문은 몇 개인가?",
      "answer": "1개\r\n(정답)",
      "category1": "1) 인사행정의\n기초", 
      "category2": "공무원 인사제도",
      "institution": "경찰간부",
      "year": "2021",
      "answerKind": "O",
      "isCorrect": false,
      "commentary": "설명 내용 2"
    }
  ],
  "2022": [
    {
      "id": 76825,
      "question": "데이터베이스 관리에\r\n\r\n관한 다음 중\n틀린 것은?",
      "answer": "정규화는\r\n중요하다",
      "category1": "2) 데이터베이스",
      "category2": "데이터베이스\r\n관리",
      "institution": "정보처리기사",
      "year": "2022",
      "answerKind": "X",
      "isCorrect": true,
      "commentary": "정규화 설명"
    },
    {
      "id": 76826,
      "question": "SELECT * FROM table\r\nWHERE condition",
      "answer": "<p>HTML 태그가 포함된</p> 답변",
      "category1": "2) 데이터베이스",
      "category2": "SQL | 쿼리",
      "institution": "정보처리기사",
      "year": "2022",
      "answerKind": "O",
      "isCorrect": null,
      "commentary": "SQL 설명"
    }
  ]
}

// Test the conversion
try {
  // Test basic conversion
  const markdown = convertJsonToMarkdown(testData)
  console.log('Markdown conversion test successful!')
  console.log('Generated markdown:')
  console.log(markdown)
  
  // Test year-based conversion (exclude year column)
  const markdownYear = convertJsonToMarkdown(testData, { excludeColumns: ['year'] })
  console.log('\n--- Year-based conversion (year column excluded) ---')
  console.log(markdownYear)
  
  // Test institution-based conversion (exclude institution column)
  const markdownInstitution = convertJsonToMarkdown(testData, { excludeColumns: ['institution'] })
  console.log('\n--- Institution-based conversion (institution column excluded) ---')
  console.log(markdownInstitution)
  
  // Check if the markdown contains expected elements
  const hasHeaders = markdown.includes('# 2021') && markdown.includes('# 2022')
  const hasTables = markdown.includes('|id|') && markdown.includes('|---')
  const hasData = markdown.includes('76823') && markdown.includes('경찰간부')
  
  // Check column order - should start with id, question, answer
  const hasCorrectColumnOrder = markdown.includes('|id|question|answer|category1|category2|')
  
  // Check exclusion functionality
  const yearExcluded = !markdownYear.includes('|year|')
  const institutionExcluded = !markdownInstitution.includes('|institution|')
  
  // Check if problematic characters were cleaned
  const noDoubleNewlines = !markdown.includes('\r\n\r\n')
  const noSingleNewlines = !markdown.includes('\r\n') || markdown.split('\r\n').every(line => line.includes('|') || line.includes('#') || line.trim() === '')
  const noPipeInData = !markdown.includes('SQL | 쿼리') // Should be escaped
  const noHtmlTags = !markdown.includes('<p>') && !markdown.includes('</p>')
  
  console.log('\nValidation results:')
  console.log('- Has year headers:', hasHeaders)
  console.log('- Has table structure:', hasTables)
  console.log('- Has data content:', hasData)
  console.log('- Has correct column order:', hasCorrectColumnOrder)
  console.log('- No double newlines in data:', noDoubleNewlines)
  console.log('- Newlines properly handled:', noSingleNewlines)
  console.log('- Pipe characters escaped:', noPipeInData)
  console.log('- HTML tags removed:', noHtmlTags)
  
  // Check for specific cleaned content
  const hasCleanedCategory2 = markdown.includes('공무원 인사제도') // Should be cleaned from "공무원\r\n\r\n인사제도"
  const hasCleanedQuestion = markdown.includes('다음은 공무원 인사제도에 대한 설명이다. 옳은 지문은 몇 개인가?')
  
  console.log('- Category2 cleaned properly:', hasCleanedCategory2)
  console.log('- Question text cleaned properly:', hasCleanedQuestion)
  console.log('- Year column excluded in year-based conversion:', yearExcluded)
  console.log('- Institution column excluded in institution-based conversion:', institutionExcluded)
  
  const allChecks = hasHeaders && hasTables && hasData && hasCorrectColumnOrder && noDoubleNewlines && noHtmlTags && yearExcluded && institutionExcluded
  
  if (allChecks) {
    console.log('✅ All validation checks passed!')
  } else {
    console.log('❌ Some validation checks failed')
  }
  
} catch (error) {
  console.error('❌ Markdown conversion test failed:', error)
}

export { testData }