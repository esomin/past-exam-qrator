export interface Answer {
  questionId: number;
  id: number;
  order: number;
  title: string;
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
}

export interface QnAPair {
  question: string;
  answers: string[];
}

export interface ProcessorConfig {
  filterEtc: boolean;
  stripHtml: boolean;
  outputDir: string;
}