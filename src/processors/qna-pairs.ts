import type { Question, QnAPair } from '../types/index.js';
import { saveJsonFile } from '../utils/file.js';

/**
 * Q&A 쌍 데이터를 생성합니다 (extractQna.ts의 transform 함수와 동일한 형태)
 */
export const processQnAPairs = (qnaArray: Question[]): QnAPair[] => {
  return qnaArray
    .filter(q => q.titleType !== "ETC")
    .sort((q1, q2) => q1.categoryTitle.localeCompare(q2.categoryTitle))
    .map(q => ({
      id: q.id,
      category1: q.categoryTitle,
      question: q.title,
      answers: q.answerSet.map(answer => ({
        id: answer.id,
        answer: answer.title,
        isCorrect: answer.answerKind === "O",
        isTrue: q.titleType === "POSITIVE" ? answer.answerKind === "O" : answer.answerKind === "X"
      }))
    }));
};

/**
 * Q&A 쌍 처리 및 파일 저장
 */
export const processAndSaveQnAPairs = (qnaArray: Question[], outputDir: string = './data'): void => {
  console.log('🔄 Processing Q&A pairs...');
  
  const qnaPairs = processQnAPairs(qnaArray);
  saveJsonFile(qnaPairs, 'qna_pairs.json', outputDir);
  
  console.log(`✨ Processed ${qnaPairs.length} Q&A pairs`);
};