import fs from "fs";

// questions.json 파일 읽기
const questions = JSON.parse(fs.readFileSync("./python/data/questions.json", "utf-8"));

const categoryCount = {};

questions.forEach(q => {
  // 카테고리 타이틀 추출: [id] [카테고리] 질문
  const match = q.match(/\[(.*?)\] \[(.*?)\]/);
  if (match) {
    const category = match[2].replace(/\s+/g, " ").trim();
    categoryCount[category] = (categoryCount[category] || 0) + 1;
  }
});

fs.writeFileSync(
  "./python/data/category-title-count.json",
  JSON.stringify(categoryCount, null, 2),
  "utf-8"
);