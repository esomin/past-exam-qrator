import type { Question } from '../types/index.js';
import { stripPTag } from '../utils/html.js';
import { saveJsonFile } from '../utils/file.js';

/**
 * 답변 데이터를 추출하고 HTML을 정리합니다
 */
export const processAnswers = (qnaArray: Question[]): Array<{ id: number, answer: string }> => {
  const answers: Array<{ id: number, answer: string }> = [];

  for (const q of qnaArray) {
    if (q.titleType !== "ETC") {
      for (const answer of q.answerSet) {
        answers.push({
          id: answer.id,
          answer: stripPTag(answer.title)
        });
      }
    }
  }

  return answers;
};

/**
 * 답변 처리 및 파일 저장
 */
export const processAndSaveAnswers = (qnaArray: Question[], outputDir: string = './data'): void => {
  console.log('💬 Processing answers...');

  const answers = processAnswers(qnaArray);
  saveJsonFile(answers, 'answers.json', outputDir);

  console.log(`✨ Processed ${answers.length} answer objects`);
};