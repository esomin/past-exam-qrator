export interface AnswerSet {
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
  reviewType: "CONCEPT" | "NORMAL";
  hasSmartNote: boolean;
  titleType: "POSITIVE" | "NEGATIVE" | "ETC";
  solve: string;
  categoryTitle: string;
  answerSet: AnswerSet[];
  history: any;
}