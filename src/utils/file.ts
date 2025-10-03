import { writeFileSync } from 'fs';
import { join } from 'path';

/**
 * JSON 데이터를 파일로 저장합니다
 */
export const saveJsonFile = (data: unknown, filename: string, outputDir: string = './data'): void => {
  const filepath = join(outputDir, filename);
  writeFileSync(filepath, JSON.stringify(data, null, 2), 'utf-8');
  console.log(`✅ Saved: ${filepath}`);
};