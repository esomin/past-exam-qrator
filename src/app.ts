import type { Question } from './types/index.js';
import { processAndSaveQuestions } from './processors/questions.js';
import { processAndSaveAnswers } from './processors/answers.js';
import { processAndSaveQnAPairs } from './processors/qna-pairs.js';

// 데이터 임포트 (기존 a.js 파일에서)
import rawData from '../a.js';

const main = async (): Promise<void> => {
  console.log('🚀 Starting Q&A Processing Pipeline');
  
  try {
    const qnaData = rawData as Question[];
    const outputDir = './data';
    
    // 각 프로세서 실행
    processAndSaveQuestions(qnaData, outputDir);
    processAndSaveAnswers(qnaData, outputDir);
    processAndSaveQnAPairs(qnaData, outputDir);
    
    console.log('✅ Pipeline completed successfully!');
    console.log('📁 Check output files in ./data directory');
    
  } catch (error) {
    console.error('❌ Pipeline failed:', error);
    process.exit(1);
  }
};

// 스크립트가 직접 실행될 때만 main 함수 호출
if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}