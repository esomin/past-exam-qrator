import type { Question, QnAPair } from '../types/index.js';
import { saveJsonFile } from '../utils/file.js';

/**
 * Q&A 쌍 데이터를 생성합니다
 */
export const processQnAPairs = (qnaArray: Question[]): QnAPair[] => {
  return qnaArray.map(q => ({
    question: q.title,
    answers: q.answerSet.map(answer => answer.title)
  }));
};

/**
 * Q&A 쌍 처리 및 파일 저장
 */
export const processAndSaveQnAPairs = (qnaArray: Question[], outputDir: string = './data'): void => {
  console.log('🔄 Processing Q&A pairs...');
  
  const qnaPairs = processQnAPairs(qnaArray);
  saveJsonFile(qnaPairs, 'qna-pairs.json', outputDir);
  
  console.log(`✨ Processed ${qnaPairs.length} Q&A pairs`);
};