import fs from 'fs';

interface QuestionData {
  id: number;
  category1: string;
  category2: string;
  question: string;
  answer: string;
  isTrue: boolean;
  similarityCount: number;
  avgSimilarity: number;
}

interface NestedOutput {
  [category1: string]: {
    [category2: string]: QuestionData[];
  };
}

const inputData: QuestionData[] = JSON.parse(fs.readFileSync('./python/data/answers_similarity_unique.json', 'utf-8'));
const nestedOutput: NestedOutput = {};

inputData.forEach((item: QuestionData) => {
  const category1Key = item.category1;
  const category2Key = item.category2;
  
  if (!nestedOutput[category1Key]) {
    nestedOutput[category1Key] = {};
  }
  
  if (!nestedOutput[category1Key][category2Key]) {
    nestedOutput[category1Key][category2Key] = [];
  }
  
  nestedOutput[category1Key][category2Key].push(item);
});

fs.writeFileSync('./python/data/answers_nested_by_categories.json', JSON.stringify(nestedOutput, null, 2));

console.log('Successfully created nested JSON structure by category1 and category2');
console.log(`Total categories: ${Object.keys(nestedOutput).length}`);
Object.keys(nestedOutput).forEach(cat1 => {
  console.log(`${cat1}: ${Object.keys(nestedOutput[cat1]).length} subcategories`);
});