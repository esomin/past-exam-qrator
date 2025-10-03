import a from "./a.js";
import fs from "fs";

const stripPTag = (text) => (text || "").replace(/<\/?p[^>]*>/gi, "").trim();

function transform(qnaArray) {
  return qnaArray
    .filter(q => q.titleType !== "ETC")
    .flatMap(q => q.answerSet.map(answer => "[" + q.id+ "-" + answer.id + "] " + stripPTag(answer.title)));
}


const b = transform(a);
console.dir(b, { depth: null });

fs.writeFileSync("./python/data/answers.json", JSON.stringify(b, null, 2), "utf-8");