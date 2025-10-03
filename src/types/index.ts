export interface Answer {
  questionId: number;
  id: number;
  order: number;
  title: string;
  commentary: string;
  answerKind: "O" | "X";
  bookmarkCount: number;
  bookmarkRate: number;
  history: any;
}

export interface Question {
  answerRate: number;
  id: number;
  order: number;
  title: string;
  text: string;
  textCommentary: string | null;
  fullCommentary: string;
  reviewType: string;
  hasSmartNote: boolean;
  titleType: 'POSITIVE' | 'NEGATIVE' | 'ETC';
  solve: string;
  categoryTitle: string;
  answerSet: Answer[];
  history: any;
}

export interface QnAPair {
  id: number;
  category1: string;
  question: string;
  answers: {
    id: number;
    answer: string;
    isCorrect: boolean;
    isTrue: boolean;
  }[];
}

export interface ProcessorConfig {
  filterEtc: boolean;
  stripHtml: boolean;
  outputDir: string;
}