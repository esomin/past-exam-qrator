import type { Question } from '../types/index.js';
import { stripPTag } from '../utils/html.js';
import { saveJsonFile } from '../utils/file.js';

/**
 * 답변 데이터를 추출하고 HTML을 정리합니다
 */
export const processAnswers = (qnaArray: Question[]): string[] => {
  return qnaArray
    .filter(q => q.titleType !== "ETC")
    .flatMap(q => q.answerSet.map(answer => stripPTag(answer.title)));
};

/**
 * 답변 처리 및 파일 저장
 */
export const processAndSaveAnswers = (qnaArray: Question[], outputDir: string = './data'): void => {
  console.log('💬 Processing answers...');
  
  const answers = processAnswers(qnaArray);
  saveJsonFile(answers, 'answers.json', outputDir);
  
  console.log(`✨ Processed ${answers.length} answers`);
};