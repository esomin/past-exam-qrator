import a from "./a.js";
import fs from "fs";

function transform(qnaArray) {
  return qnaArray.map(q => ({
    question: q.title,
    answers: q.answerSet.map(answer => answer.title)
  }));
}



const b = transform(a);
console.dir(b, { depth: null });

fs.writeFileSync("./data/output.json", JSON.stringify(b, null, 2), "utf-8");