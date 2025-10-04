import fs from 'fs';

interface QuestionData {
  id: number;
  category1: string;
  category2: string;
  category3?: string;
  question: string;
  answer: string;
  isTrue: boolean;
  similarityCount: number;
  avgSimilarity: number;
  topic: string;
}

interface NestedOutput {
  [category3: string]: QuestionData[];
}

const inputData: QuestionData[] = JSON.parse(fs.readFileSync('./python/data/answers_with_topics_sorted.json', 'utf-8'));
const nestedOutput: NestedOutput = {};

inputData.forEach((item: QuestionData) => {
  const category3Key = item.category3 || 'uncategorized';
  if (!nestedOutput[category3Key]) {
    nestedOutput[category3Key] = [];
  }
  nestedOutput[category3Key].push(item);  
});

fs.writeFileSync('./python/data/answers_nested_by_category3.json', JSON.stringify(nestedOutput, null, 2));