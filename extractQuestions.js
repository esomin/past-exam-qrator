import a from "./a.js";
import fs from "fs";

function transform(qnaArray) {
  return qnaArray
    .filter(q => q.titleType !== "ETC")
    .sort((q1, q2) => q1.categoryTitle.localeCompare(q2.categoryTitle))
    .map(q => "[" + q.id + "] [" +
      q.categoryTitle + "] " +
      q.title);
}

const b = transform(a);
console.dir(b, { depth: null });

fs.writeFileSync("./python/data/questions.json", JSON.stringify(b, null, 2), "utf-8");