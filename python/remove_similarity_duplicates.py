#!/usr/bin/env python3
"""
TF-IDF + 코사인 유사도 기반 중복 제거 모듈
answers_unique.json 파일에서 의미적으로 유사한 답변들을 제거합니다.
"""

import json
import os
import re
import math
from typing import List, Dict, Any, Tuple
from pathlib import Path
from collections import Counter


class SimilarityDeduplicator:
    """TF-IDF + 코사인 유사도 기반 중복 제거 클래스"""
    
    def __init__(self, input_file: str = "data/answers.json", output_dir: str = "data", threshold: float = 0.8):
        self.input_file = input_file
        self.output_dir = output_dir
        self.threshold = threshold
        self.ensure_output_dir()
    
    def ensure_output_dir(self) -> None:
        """출력 디렉토리가 존재하는지 확인하고 없으면 생성"""
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
    
    def load_answers(self) -> List[Dict[str, Any]]:
        """answers_unique.json 파일에서 데이터 로드"""
        try:
            with open(self.input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"📁 Loaded {len(data)} answers from {self.input_file}")
            return data
        except FileNotFoundError:
            print(f"❌ File not found: {self.input_file}")
            raise
        except json.JSONDecodeError as e:
            print(f"❌ JSON decode error: {e}")
            raise
    
    def save_json_file(self, data: Any, filename: str) -> None:
        """JSON 데이터를 파일로 저장"""
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ Saved: {filepath}")
    
    def preprocess_text(self, text: str) -> List[str]:
        """텍스트 전처리 및 토큰화"""
        if not text:
            return []
        
        # HTML 태그 제거
        text = re.sub(r'<[^>]+>', '', text)
        
        # 숫자 정규화
        text = re.sub(r'\d{4}년', 'YEAR년', text)
        text = re.sub(r'\d+%', 'PERCENT', text)
        text = re.sub(r'\d+번', 'NUMBER번', text)
        text = re.sub(r'\d+\.', 'NUMBER.', text)
        
        # 특수문자 및 공백 정규화
        text = re.sub(r'[^\w\s가-힣]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        
        # 조사, 어미 간소화 (기본적인 것들만)
        text = re.sub(r'입니다$', '이다', text)
        text = re.sub(r'습니다$', '다', text)
        text = re.sub(r'에서$', '에', text)
        
        # 토큰화 (공백 기준)
        tokens = text.strip().split()
        
        # 길이가 1인 토큰 제거 (조사 등)
        tokens = [token for token in tokens if len(token) > 1]
        
        return tokens
    
    def calculate_tf(self, tokens: List[str]) -> Dict[str, float]:
        """단어 빈도(TF) 계산"""
        if not tokens:
            return {}
        
        tf_dict = Counter(tokens)
        total_words = len(tokens)
        
        # 정규화
        for word in tf_dict:
            tf_dict[word] = tf_dict[word] / total_words
        
        return dict(tf_dict)
    
    def calculate_idf(self, documents: List[List[str]]) -> Dict[str, float]:
        """역문서 빈도(IDF) 계산"""
        if not documents:
            return {}
        
        N = len(documents)
        all_words = set(word for doc in documents for word in doc)
        idf_dict = {}
        
        for word in all_words:
            containing_docs = sum(1 for doc in documents if word in doc)
            if containing_docs > 0:
                idf_dict[word] = math.log(N / containing_docs)
            else:
                idf_dict[word] = 0
        
        return idf_dict
    
    def create_tfidf_vector(self, tf_dict: Dict[str, float], idf_dict: Dict[str, float], vocabulary: List[str]) -> List[float]:
        """TF-IDF 벡터 생성"""
        vector = []
        for word in vocabulary:
            tf = tf_dict.get(word, 0)
            idf = idf_dict.get(word, 0)
            vector.append(tf * idf)
        return vector
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """두 벡터 간의 코사인 유사도 계산"""
        if len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    def should_skip_comparison(self, answer1: str, answer2: str, tokens1: List[str], tokens2: List[str]) -> bool:
        """비교를 건너뛸지 결정하는 사전 필터링"""
        # 길이 차이가 3배 이상이면 건너뛰기
        len1, len2 = len(answer1), len(answer2)
        if len1 == 0 or len2 == 0:
            return True
        
        ratio = max(len1, len2) / min(len1, len2)
        if ratio > 3.0:
            return True
        
        # 토큰 수 차이가 너무 크면 건너뛰기
        token_len1, token_len2 = len(tokens1), len(tokens2)
        if token_len1 == 0 or token_len2 == 0:
            return True
        
        token_ratio = max(token_len1, token_len2) / min(token_len1, token_len2)
        if token_ratio > 2.5:
            return True
        
        # 공통 토큰이 30% 미만이면 건너뛰기
        common_tokens = set(tokens1) & set(tokens2)
        total_unique_tokens = len(set(tokens1) | set(tokens2))
        if total_unique_tokens > 0:
            common_ratio = len(common_tokens) / total_unique_tokens
            if common_ratio < 0.3:
                return True
        
        return False
    
    def find_similar_groups(self, answers: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """유사한 답변들을 찾아서 그룹화"""
        print(f"🔍 Finding similar answers with threshold {self.threshold}...")
        
        # 전처리
        answer_texts = [answer.get('answer', '') for answer in answers]
        processed_texts = [self.preprocess_text(text) for text in answer_texts]
        
        # 빈 텍스트 필터링
        valid_indices = [i for i, tokens in enumerate(processed_texts) if tokens]
        valid_answers = [answers[i] for i in valid_indices]
        valid_processed = [processed_texts[i] for i in valid_indices]
        
        if len(valid_answers) <= 1:
            return valid_answers, []
        
        print(f"📊 Processing {len(valid_answers)} valid answers...")
        
        # TF-IDF 계산
        print("📊 Calculating TF-IDF vectors...")
        idf_dict = self.calculate_idf(valid_processed)
        vocabulary = sorted(idf_dict.keys())
        print(f"📚 Vocabulary size: {len(vocabulary)}")
        
        # 각 답변의 TF-IDF 벡터 생성
        tfidf_vectors = []
        for i, tokens in enumerate(valid_processed):
            if i % 500 == 0:
                print(f"   Vectorizing... {i}/{len(valid_processed)}")
            tf_dict = self.calculate_tf(tokens)
            vector = self.create_tfidf_vector(tf_dict, idf_dict, vocabulary)
            tfidf_vectors.append(vector)
        
        # 유사도 계산 및 그룹화
        print("🔗 Grouping similar answers...")
        processed_indices = set()
        unique_answers = []
        similar_groups = []
        total_comparisons = 0
        
        for i in range(len(valid_answers)):
            if i in processed_indices:
                continue
            
            if i % 100 == 0:
                print(f"   Processing... {i}/{len(valid_answers)} ({len(unique_answers)} groups found)")
            
            current_group = [i]
            current_similarities = []
            
            for j in range(i + 1, len(valid_answers)):
                if j in processed_indices:
                    continue
                
                # 사전 필터링
                if self.should_skip_comparison(
                    answer_texts[valid_indices[i]], 
                    answer_texts[valid_indices[j]],
                    valid_processed[i],
                    valid_processed[j]
                ):
                    continue
                
                total_comparisons += 1
                similarity = self.cosine_similarity(tfidf_vectors[i], tfidf_vectors[j])
                
                if similarity >= self.threshold:
                    current_group.append(j)
                    current_similarities.append(similarity)
                    processed_indices.add(j)
            
            # 대표 답변 선택 (가장 긴 답변을 선택)
            representative_idx = max(current_group, key=lambda idx: len(valid_answers[idx].get('answer', '')))
            representative = valid_answers[representative_idx].copy()
            
            if len(current_group) > 1:
                # 유사한 답변이 있는 경우
                representative['similarityCount'] = len(current_group)
                representative['avgSimilarity'] = sum(current_similarities) / len(current_similarities) if current_similarities else 0
                
                # 제거된 답변들 정보
                removed_answers = [valid_answers[idx] for idx in current_group if idx != representative_idx]
                similar_groups.append({
                    'representativeId': representative.get('id'),
                    'representativeAnswer': representative.get('answer', ''),
                    'similarityCount': len(current_group),
                    'avgSimilarity': representative['avgSimilarity'],
                    'removedAnswers': removed_answers
                })
            
            unique_answers.append(representative)
            processed_indices.add(i)
        
        # similarityCount 큰 순으로 정렬
        unique_answers.sort(key=lambda x: x.get('similarityCount', 0), reverse=True)
        
        print(f"📊 Total comparisons made: {total_comparisons:,}")
        return unique_answers, similar_groups
    
    def process_and_save(self) -> None:
        """유사도 기반 중복 제거 처리 및 파일 저장"""
        print('🚀 Starting similarity-based deduplication...')
        
        # 데이터 로드
        answers = self.load_answers()
        
        # 유사도 기반 중복 제거
        unique_answers, similar_groups = self.find_similar_groups(answers)
        
        # 결과 저장
        self.save_json_file(unique_answers, 'answers_similarity_unique.json')
        self.save_json_file(similar_groups, 'answers_similarity_removed.json')
        
        # 통계 출력
        total_removed = sum(len(group['removedAnswers']) for group in similar_groups)
        removal_rate = (total_removed / len(answers)) * 100 if len(answers) > 0 else 0
        similarity_group_rate = (len(similar_groups) / len(unique_answers)) * 100 if len(unique_answers) > 0 else 0
        
        print(f'✨ Original answers: {len(answers)}')
        print(f'✨ Similarity-unique answers: {len(unique_answers)}')
        print(f'✨ Removed by similarity: {total_removed}')
        print(f'✨ Similarity groups: {len(similar_groups)}')
        print(f'📊 Similarity removal rate: {removal_rate:.2f}%')
        print(f'📊 Similarity group rate: {similarity_group_rate:.2f}%')
        
        # 임계값별 통계
        if similar_groups:
            avg_similarity = sum(group['avgSimilarity'] for group in similar_groups) / len(similar_groups)
            print(f'📊 Average similarity in groups: {avg_similarity:.3f}')
    
    def run(self) -> None:
        """유사도 기반 중복 제거 실행"""
        print('🚀 Starting Similarity-based Duplicate Removal')
        
        try:
            self.process_and_save()
            print('✅ Similarity-based deduplication completed successfully!')
            
        except Exception as error:
            print(f'❌ Similarity-based deduplication failed: {error}')
            raise


def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='TF-IDF + 코사인 유사도 기반 중복 제거')
    parser.add_argument('--input', '-i', default='data/answers_unique.json', help='입력 파일 경로')
    parser.add_argument('--output', '-o', default='data', help='출력 디렉토리')
    parser.add_argument('--threshold', '-t', type=float, default=0.8, help='유사도 임계값 (0.0-1.0)')
    
    args = parser.parse_args()
    
    deduplicator = SimilarityDeduplicator(
        input_file=args.input,
        output_dir=args.output,
        threshold=args.threshold
    )
    deduplicator.run()


if __name__ == "__main__":
    main()