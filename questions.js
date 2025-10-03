import a from "./a.js";
import fs from "fs";

function transform(qnaArray) {
  return qnaArray
    .filter(q => q.titleType !== "ETC")
    .map(q => q.title);
}



const b = transform(a);
console.dir(b, { depth: null });

fs.writeFileSync("./data/questions.json", JSON.stringify(b, null, 2), "utf-8");