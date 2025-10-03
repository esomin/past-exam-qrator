import type { Question, QnAPair } from '../types/index.js';
import { saveJsonFile } from '../utils/file.js';

/**
 * 유니코드 정규화
 */
const normalizeText = (text: string): string => {
  return text.normalize("NFKC").trim();
};

/**
 * 문제 번호 및 불필요한 접두사 제거
 */
const cleanPrefix = (text: string): string => {
  text = normalizeText(text);
  // 1. [숫자] 문제번호 제거
  text = text.replace(/^\[\d+\]\s*/, "");
  // 2. "다음", "다음 중" 제거 (맨 앞 또는 카테고리 뒤)
  text = text.replace(/(^|\]\s*)다음\s*중\s*/g, "$1");
  text = text.replace(/(^|\]\s*)다음\s*/g, "$1");
  return text.trim();
};

/**
 * 질문에서 핵심 키워드 추출
 */
const extractKeyword = (questionText: string): string => {
  const keywordPattern = /(.+?)(?=에\s+(대한|관한)|[과와]\s*관련(된|한|하여)|의\s*내용\s*중|에\s*해당(하는|하지)|로만\s*묶은|으로)/;
  const normalizedText = normalizeText(questionText);
  const match = normalizedText.match(keywordPattern);
  const subject = match ? match[1].trim() : normalizedText;
  return cleanPrefix(subject);
};

/**
 * Q&A 쌍 데이터를 생성합니다 (extractQna.ts의 transform 함수와 동일한 형태 + 키워드 추출)
 */
export const processQnAPairs = (qnaArray: Question[]): QnAPair[] => {
  return qnaArray
    .filter(q => q.titleType !== "ETC")
    .sort((q1, q2) => q1.categoryTitle.localeCompare(q2.categoryTitle))
    .map(q => ({
      id: q.id,
      category1: q.categoryTitle,
      category2: extractKeyword(q.title), // 키워드 추출하여 category2에 저장
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