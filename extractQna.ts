import a from "./a.js";
import fs from "fs";

type Question = typeof a[0];
type AnswerSet = Question['answerSet'][0];

function transform(qnaArray: Question[]) {
  return qnaArray
    .filter(q => q.titleType !== "ETC")
    .sort((q1, q2) => q1.categoryTitle.localeCompare(q2.categoryTitle))
    .map(q => ({
      id: q.id,
      category1: q.categoryTitle,
      question: q.title,
      answers: q.answerSet.map((answer: AnswerSet) => ({
        id: answer.id,
        answer: answer.title,
        isCorrect: answer.answerKind === "O",
        isTrue: q.titleType === "POSITIVE" ? answer.answerKind === "O" : answer.answerKind === "X"
      }))
    }));
}

const b = transform(a);
console.dir(b, {depth: null});

fs.writeFileSync("./python/data/output.json", JSON.stringify(b, null, 2), "utf-8");