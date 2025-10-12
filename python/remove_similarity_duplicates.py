#!/usr/bin/env python3
"""
TF-IDF + 코사인 유사도 기반 중복 제거 모듈
answers.json 파일에서 의미없는 답변을 필터링한 후 의미적으로 유사한 답변들을 제거합니다.
"""

import json
import os
import re
import math
import sys
import time
from datetime import datetime
from typing import List, Dict, Any, Tuple
from pathlib import Path
from collections import Counter
from remove_meaningless_ans import AnswerFilter


class LogCapture:
    """로그를 캡처하고 파일로 저장하는 클래스"""
    
    def __init__(self, log_file: str):
        self.log_file = log_file
        self.final_stats = []
        self.original_stdout = sys.stdout
        self.capturing_stats = False
        
    def write(self, text: str):
        """stdout에 쓰여지는 내용을 캡처"""
        # 이모지 제거
        clean_text = self.remove_emojis(text)
        self.original_stdout.write(clean_text)
        
        # final statistics 부분만 캡처
        if "=== FINAL STATISTICS ===" in text:
            self.capturing_stats = True
        
        if self.capturing_stats:
            self.final_stats.append(clean_text)
            
        # Total Runtime까지 캡처하면 종료
        if "Total Runtime:" in text:
            self.capturing_stats = False
        
    def flush(self):
        """flush 메서드"""
        self.original_stdout.flush()
    
    def remove_emojis(self, text: str) -> str:
        """텍스트에서 이모지 제거"""
        emoji_map = {
            '🚀': '',
            '📋': '',
            '📁': '',
            '❌': '',
            '✅': '',
            '🔄': '',
            '✨': '',
            '📊': '',
            '🔍': '',
            '⏱️': '',
            '📚': '',
            '🔗': '',
            '🏁': '',
            '📝': ''
        }
        
        for emoji, replacement in emoji_map.items():
            text = text.replace(emoji, replacement)
        
        return text
        
    def save_logs(self):
        """final statistics만 파일로 저장"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_file, 'w', encoding='utf-8') as f:
            f.write(f"=== Similarity Deduplication Final Statistics - {timestamp} ===\n\n")
            f.write(''.join(self.final_stats))
        print(f"Log saved: {self.log_file}")


class SimilarityDeduplicator:
    """TF-IDF + 코사인 유사도 기반 중복 제거 클래스"""
    
    def __init__(self, input_file: str = "data/answers.json", output_dir: str = "data", threshold: float = 0.8):
        self.input_file = input_file
        self.output_dir = output_dir
        self.threshold = threshold
        self.ensure_output_dir()
        
        # 로그 캡처 설정
        self.log_capture = LogCapture(os.path.join(output_dir, 'similarity_deduplication.log'))
        
        # 답변 필터링 인스턴스 생성
        self.answer_filter = AnswerFilter(input_file=input_file, output_dir=output_dir)
    
    def ensure_output_dir(self) -> None:
        """출력 디렉토리가 존재하는지 확인하고 없으면 생성"""
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
    
    def load_answers(self) -> List[Dict[str, Any]]:
        """answers.json 파일에서 데이터 로드"""
        try:
            with open(self.input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"Loaded {len(data)} answers from {self.input_file}")
            return data
        except FileNotFoundError:
            print(f"File not found: {self.input_file}")
            raise
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            raise
    
    def save_json_file(self, data: Any, filename: str) -> None:
        """JSON 데이터를 파일로 저장"""
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Saved: {filepath}")
    
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
        start_time = time.time()
        print(f"Finding similar answers with threshold {self.threshold}...")
        
        # 전처리
        preprocess_start = time.time()
        answer_texts = [answer.get('answer', '') for answer in answers]
        processed_texts = [self.preprocess_text(text) for text in answer_texts]
        preprocess_time = time.time() - preprocess_start
        print(f"Text preprocessing completed in {preprocess_time:.2f} seconds")
        
        # 빈 텍스트 필터링
        valid_indices = [i for i, tokens in enumerate(processed_texts) if tokens]
        valid_answers = [answers[i] for i in valid_indices]
        valid_processed = [processed_texts[i] for i in valid_indices]
        
        if len(valid_answers) <= 1:
            return valid_answers, []
        
        print(f"Processing {len(valid_answers)} valid answers...")
        
        # TF-IDF 계산
        tfidf_start = time.time()
        print("Calculating TF-IDF vectors...")
        idf_dict = self.calculate_idf(valid_processed)
        vocabulary = sorted(idf_dict.keys())
        print(f"Vocabulary size: {len(vocabulary)}")
        
        # 각 답변의 TF-IDF 벡터 생성
        tfidf_vectors = []
        for i, tokens in enumerate(valid_processed):
            if i % 500 == 0:
                print(f"   Vectorizing... {i}/{len(valid_processed)}")
            tf_dict = self.calculate_tf(tokens)
            vector = self.create_tfidf_vector(tf_dict, idf_dict, vocabulary)
            tfidf_vectors.append(vector)
        
        tfidf_time = time.time() - tfidf_start
        print(f"TF-IDF vectorization completed in {tfidf_time:.2f} seconds")
        
        # 유사도 계산 및 그룹화
        similarity_start = time.time()
        print("Grouping similar answers...")
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
                
                # 제거된 답변들 정보 (question 속성 포함)
                removed_answers = []
                for idx in current_group:
                    if idx != representative_idx:
                        removed_answer = valid_answers[idx].copy()
                        # question 속성이 없으면 빈 문자열로 설정
                        if 'question' not in removed_answer:
                            removed_answer['question'] = ''
                        removed_answers.append(removed_answer)
                
                similar_groups.append({
                    'representativeId': representative.get('id'),
                    'category1': representative.get('category1', ''),
                    'category2': representative.get('category2', ''),
                    'question': representative.get('question', ''),
                    'representativeAnswer': representative.get('answer', ''),
                    'similarityCount': len(current_group),
                    'avgSimilarity': representative['avgSimilarity'],
                    'removedAnswers': removed_answers
                })
            
            # question 속성이 없으면 빈 문자열로 설정
            if 'question' not in representative:
                representative['question'] = ''
            
            unique_answers.append(representative)
            processed_indices.add(i)
        
        # similarityCount 순서로 category1 우선순위를 결정한 후, category1별로 그룹핑하여 정렬
        # 1. similarityCount 내림차순으로 정렬하여 category1 우선순위 결정
        temp_sorted = sorted(unique_answers, key=lambda x: -x.get('similarityCount', 0))
        
        # 2. category1 우선순위 순서 결정 (이미 처리된 category1은 제외)
        category1_order = []
        seen_categories = set()
        for answer in temp_sorted:
            cat1 = answer.get('category1', '')
            if cat1 and cat1 not in seen_categories:
                category1_order.append(cat1)
                seen_categories.add(cat1)
        
        # 3. category1 우선순위 -> category2 -> similarityCount 내림차순 순으로 정렬
        def sort_key(x):
            cat1 = x.get('category1', '')
            cat1_priority = category1_order.index(cat1) if cat1 in category1_order else len(category1_order)
            return (
                cat1_priority,                    # category1 우선순위 (similarityCount 순서 기준)
                x.get('category2', ''),           # category2 오름차순
                -x.get('similarityCount', 0)      # 같은 category 내에서 similarityCount 내림차순
            )
        
        unique_answers.sort(key=sort_key)
        
        similarity_time = time.time() - similarity_start
        total_time = time.time() - start_time
        
        print(f"Total comparisons made: {total_comparisons:,}")
        print(f"Similarity grouping completed in {similarity_time:.2f} seconds")
        print(f"Total similarity detection time: {total_time:.2f} seconds")
        
        return unique_answers, similar_groups
    
    def process_and_save(self) -> None:
        """답변 필터링 후 유사도 기반 중복 제거 처리 및 파일 저장"""
        total_start_time = time.time()
        print('Starting answer filtering and similarity-based deduplication...')
        
        # 1단계: 답변 필터링 (자모 나열, 숫자개 등 제거)
        print('Step 1: Filtering meaningless answers...')
        filtered_answers, removed_answers = self.answer_filter.run()
        
        print(f'Filtered out {len(removed_answers)} meaningless answers')
        print(f'Proceeding with {len(filtered_answers)} valid answers')
        
        # 2단계: 유사도 기반 중복 제거
        print('Step 2: Removing similar duplicates...')
        unique_answers, similar_groups = self.find_similar_groups(filtered_answers)
        
        # similar_groups도 동일한 기준으로 정렬
        # unique_answers에서 사용한 category1_order를 재사용
        temp_sorted_groups = sorted(similar_groups, key=lambda x: -x.get('similarityCount', 0))
        
        # category1 우선순위 순서 결정 (similar_groups용)
        category1_order_groups = []
        seen_categories_groups = set()
        for group in temp_sorted_groups:
            cat1 = group.get('category1', '')
            if cat1 and cat1 not in seen_categories_groups:
                category1_order_groups.append(cat1)
                seen_categories_groups.add(cat1)
        
        def sort_key_groups(x):
            cat1 = x.get('category1', '')
            cat1_priority = category1_order_groups.index(cat1) if cat1 in category1_order_groups else len(category1_order_groups)
            return (
                cat1_priority,                    # category1 우선순위 (similarityCount 순서 기준)
                x.get('category2', ''),           # category2 오름차순
                -x.get('similarityCount', 0)      # 같은 category 내에서 similarityCount 내림차순
            )
        
        similar_groups.sort(key=sort_key_groups)
        
        # 결과 저장
        self.save_json_file(unique_answers, 'answers_similarity_unique.json')
        self.save_json_file(similar_groups, 'answers_similarity_removed.json')
        
        # 통계 출력
        original_count = len(self.load_answers())  # 원본 데이터 개수
        filtered_count = len(filtered_answers)
        meaningless_removed = len(removed_answers)
        similarity_removed = sum(len(group['removedAnswers']) for group in similar_groups)
        final_count = len(unique_answers)
        
        total_removal_rate = ((meaningless_removed + similarity_removed) / original_count) * 100 if original_count > 0 else 0
        meaningless_removal_rate = (meaningless_removed / original_count) * 100 if original_count > 0 else 0
        similarity_removal_rate = (similarity_removed / filtered_count) * 100 if filtered_count > 0 else 0
        similarity_group_rate = (len(similar_groups) / len(unique_answers)) * 100 if len(unique_answers) > 0 else 0
        
        print(f'\n=== FINAL STATISTICS ===')
        print(f'Original answers: {original_count}')
        print(f'Meaningless answers removed: {meaningless_removed} ({meaningless_removal_rate:.2f}%)')
        print(f'Filtered answers: {filtered_count}')
        print(f'Similar answers removed: {similarity_removed} ({similarity_removal_rate:.2f}%)')
        print(f'Final unique answers: {final_count}')
        print(f'Similarity groups: {len(similar_groups)}')
        print(f'Total removal rate: {total_removal_rate:.2f}%')
        print(f'Similarity group rate: {similarity_group_rate:.2f}%')
        print(f'Math check: {original_count} - {meaningless_removed} - {similarity_removed} = {original_count - meaningless_removed - similarity_removed} (should equal {final_count})')
        
        # 임계값별 통계
        if similar_groups:
            avg_similarity = sum(group['avgSimilarity'] for group in similar_groups) / len(similar_groups)
            print(f'Average similarity in groups: {avg_similarity:.3f}')
        
        # 전체 처리시간
        total_time = time.time() - total_start_time
        print(f'\nTotal Processing Time: {total_time:.2f} seconds ({total_time/60:.2f} minutes)')
    
    def run(self) -> None:
        """답변 필터링 및 유사도 기반 중복 제거 실행"""
        # 로그 캡처 시작
        sys.stdout = self.log_capture
        
        try:
            start_time = time.time()
            start_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f'Starting Answer Filtering and Similarity-based Duplicate Removal at {start_datetime}')
            
            self.process_and_save()
            
            end_time = time.time()
            end_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            total_runtime = end_time - start_time
            
            print(f'Answer filtering and similarity-based deduplication completed successfully!')
            print(f'Process finished at {end_datetime}')
            print(f'Total Runtime: {total_runtime:.2f} seconds ({total_runtime/60:.2f} minutes)')
            
        except Exception as error:
            error_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f'Answer filtering and similarity-based deduplication failed at {error_time}: {error}')
            raise
        finally:
            # 로그 캡처 종료 및 저장
            sys.stdout = self.log_capture.original_stdout
            self.log_capture.save_logs()


def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='답변 필터링 + TF-IDF + 코사인 유사도 기반 중복 제거')
    parser.add_argument('--input', '-i', default='data/answers.json', help='입력 파일 경로')
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