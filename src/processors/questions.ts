import type { Question } from '../types/index.js';
import { saveJsonFile } from '../utils/file.js';

/**
 * 질문 데이터를 추출하고 필터링합니다
 */
export const processQuestions = (qnaArray: Question[]): string[] => {
  return qnaArray
    .filter(q => q.titleType !== "ETC")
    .map(q => q.title);
};

/**
 * 질문 처리 및 파일 저장
 */
export const processAndSaveQuestions = (qnaArray: Question[], outputDir: string = './data'): void => {
  console.log('📊 Processing questions...');
  
  const questions = processQuestions(qnaArray);
  saveJsonFile(questions, 'questions.json', outputDir);
  
  console.log(`✨ Processed ${questions.length} questions`);
};