"""
Flask API server for React File Processor
Provides endpoints for file processing and downloads
"""

import os
import json
import uuid
import base64
import tempfile
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import defaultdict, OrderedDict
from flask import Flask, request, jsonify, send_file, abort
from flask_cors import CORS
from werkzeug.exceptions import BadRequest


from processors.classifier import ClassificationEngine
from optimize_file_cleanup import ResourceManager


app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)  # Enable CORS for React frontend communication

# Configure Flask for large file uploads
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max request size
app.config['JSON_AS_ASCII'] = False

# Global classification engine for managing results
classification_engine = ClassificationEngine()

# Global resource manager for memory and file optimization
resource_manager = ResourceManager(max_memory_mb=1000)  # 1GB memory limit


class ProcessingError(Exception):
    """Custom exception for processing errors"""
    pass


def reorder_item_fields(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    항목의 필드를 요구사항에 맞는 순서로 재정렬
    순서: id, question, year, institution, category1, category2, answer, answerKind, isCorrect, commentary
    """
    preferred_order = [
        'id', 'question', 'year', 'institution', 'category1', 'category2',
        'answer', 'answerKind', 'isCorrect', 'commentary',
        # 중복 제거 관련 필드들
        'isUnique', 'similarity', 'similarityCount', 'repId'
    ]
    
    # OrderedDict를 사용하여 순서 유지
    ordered_item = OrderedDict()
    
    # 선호 순서대로 필드 추가
    for key in preferred_order:
        if key in item:
            ordered_item[key] = item[key]
    
    # 나머지 필드들을 알파벳 순으로 추가
    remaining_keys = sorted([k for k in item.keys() if k not in preferred_order])
    for key in remaining_keys:
        ordered_item[key] = item[key]
    
    return dict(ordered_item)


def extract_institution_from_solve(solve: str) -> str:
    """solve 필드에서 기관명 추출"""
    if not solve:
        return "Unknown"
    
    # 일반적인 패턴: "기관명 / 연도" 또는 "기관명"
    parts = solve.split('/')
    if parts:
        return parts[0].strip()
    return solve.strip()


def extract_year_from_solve(solve: str) -> str:
    """solve 필드에서 연도 추출"""
    if not solve:
        return "Unknown"
    
    # 4자리 숫자 패턴 찾기
    year_match = re.search(r'\b(20\d{2}|19\d{2})\b', solve)
    if year_match:
        return year_match.group(1)
    return "Unknown"


def convert_json_to_markdown(data: Any, exclude_columns: List[str] = None) -> str:
    """Convert JSON data to Markdown format"""
    if exclude_columns is None:
        exclude_columns = []
    
    if not data:
        return "# No Data Available\n\nThe provided data is empty."
    
    # Handle different data structures
    if isinstance(data, dict):
        # If it's a dictionary (grouped data), process each group
        markdown_content = []
        
        for group_name, items in data.items():
            markdown_content.append(f"# {group_name}\n")
            
            if isinstance(items, list) and items:
                # Create table from list of items
                table_md = create_markdown_table(items, exclude_columns)
                markdown_content.append(table_md)
            else:
                markdown_content.append("No items in this group.\n")
            
            markdown_content.append("\n---\n")
        
        return "\n".join(markdown_content)
    
    elif isinstance(data, list):
        # If it's a list, create a single table
        if not data:
            return "# No Data Available\n\nThe provided list is empty."
        
        markdown_content = ["# Data\n"]
        table_md = create_markdown_table(data, exclude_columns)
        markdown_content.append(table_md)
        
        return "\n".join(markdown_content)
    
    else:
        return f"# Data\n\n```json\n{json.dumps(data, ensure_ascii=False, indent=2)}\n```"


def create_markdown_table(items: List[Dict], exclude_columns: List[str] = None) -> str:
    """Create a markdown table from a list of dictionaries"""
    if exclude_columns is None:
        exclude_columns = []
    
    if not items:
        return "No data available.\n"
    
    # Get all unique keys from all items, excluding specified columns
    all_keys = set()
    for item in items:
        if isinstance(item, dict):
            all_keys.update(item.keys())
    
    # Remove excluded columns
    columns = [key for key in all_keys if key not in exclude_columns]
    
    if not columns:
        return "No columns to display after filtering.\n"
    
    # 요구사항에 맞는 컬럼 순서 정의
    preferred_order = ['id', 'question', 'year', 'institution', 'category1', 'category2', 
                      'answer', 'answerKind', 'isCorrect', 'commentary']
    
    # 선호 순서에 있는 컬럼들을 먼저 배치
    ordered_columns = [col for col in preferred_order if col in columns]
    
    # 선호 순서에 없는 나머지 컬럼들을 알파벳 순으로 추가
    remaining_columns = sorted([col for col in columns if col not in preferred_order])
    
    columns = ordered_columns + remaining_columns
    
    # Create table header
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"
    
    # Create table rows
    rows = []
    for item in items:
        if isinstance(item, dict):
            row_values = []
            for col in columns:
                value = item.get(col, "")
                
                # Special handling for isUnique column
                if col == 'isUnique':
                    if value is True:
                        value = "O"
                    elif value is False:
                        value = ""
                    else:
                        value = ""
                # Clean up the value for markdown
                elif value is None:
                    value = ""
                else:
                    value = str(value).replace("|", "\\|").replace("\n", " ").replace("\r", "")
                    # Limit cell content length
                    if len(value) > 100:
                        value = value[:97] + "..."
                row_values.append(value)
            
            row = "| " + " | ".join(row_values) + " |"
            rows.append(row)
    
    # Combine all parts
    table_parts = [header, separator] + rows
    return "\n".join(table_parts) + "\n"


def determine_is_correct(title_type: str, answer_kind: str) -> Optional[bool]:
    """titleType과 answerKind를 기반으로 isCorrect 값 결정"""
    if title_type == "NEGATIVE" and answer_kind == "X":
        return True
    elif title_type == "POSITIVE" and answer_kind == "O":
        return True
    elif title_type == "NEGATIVE" and answer_kind == "O":
        return False
    elif title_type == "POSITIVE" and answer_kind == "X":
        return False
    else:
        # titleType이 NEGATIVE도 POSITIVE도 아닌 경우
        return None


def flatten_original_data(input_data: List[Dict[str, Any]], filter_options: Dict[str, Any] = None) -> tuple[List[Dict[str, Any]], Dict[str, int]]:
    """원본 데이터를 플래튼하여 필요한 속성만 추출하고 통계 정보 반환
    
    Args:
        input_data: 원본 데이터
        filter_options: 필터 옵션 (처리 전 적용)
    """
    from add_category2_to_qn import add_category2_to_data
    
    # category2 추가
    data_with_category2 = add_category2_to_data(input_data)
    
    # 처리 전 필터링 적용
    filtered_questions = []
    
    for question in data_with_category2:
        should_include = True
        
        # 카테고리 필터 적용
        if filter_options and filter_options.get('category_filter', {}).get('enabled', False):
            keyword = filter_options['category_filter'].get('keyword', '').strip().lower()
            if keyword:
                category_title = (question.get('categoryTitle') or '').lower()
                title = (question.get('title') or '').lower()
                text = (question.get('text') or '').lower()
                
                if not (keyword in category_title or keyword in title or keyword in text):
                    should_include = False
        
        # 연도 필터 적용 (solve 속성에서 검색)
        if should_include and filter_options and filter_options.get('year_filter', {}).get('enabled', False):
            years = filter_options['year_filter'].get('years', [])
            if years:
                solve = question.get('solve', '')
                year_strings = [str(year).strip() for year in years if str(year).strip()]
                # solve 속성에 해당 연도가 포함되어 있는지 확인
                year_found = any(year_str in solve for year_str in year_strings)
                if not year_found:
                    should_include = False
        
        # 기관 필터 적용 (solve 속성에서 검색)
        if should_include and filter_options and filter_options.get('institution_filter', {}).get('enabled', False):
            keyword = filter_options['institution_filter'].get('keyword', '').strip()
            if keyword:
                solve = question.get('solve', '')
                # solve 속성에 해당 기관명이 포함되어 있는지 확인
                if keyword not in solve:
                    should_include = False
        
        if should_include:
            filtered_questions.append(question)
    
    data_with_category2 = filtered_questions
    
    flattened_data = []
    seen_ids = set()  # ID 중복 체크용
    seen_questions = set()  # 문제 중복 체크용
    
    # 통계 정보
    original_questions = len(data_with_category2)
    original_answers = 0
    removed_duplicate_answers = 0  # 제거된 중복 선택지 수
    
    for question in data_with_category2:
        # question 레벨 속성 추출
        question_data = {
            "title": question.get("title"),
            "text": question.get("text"),
            "titleType": question.get("titleType"),
            "solve": question.get("solve"),
            "categoryTitle": question.get("categoryTitle"),
            "category2": question.get("category2")  # category2 추가
        }
        
        # solve에서 기관과 연도 추출
        institution = extract_institution_from_solve(question_data["solve"] or "")
        year = extract_year_from_solve(question_data["solve"] or "")
        
        # answerSet의 각 항목 처리
        answer_set = question.get("answerSet", [])
        original_answers += len(answer_set)
        
        for answer in answer_set:
            # ID 중복 체크 (선택지 중복)
            answer_id = answer.get("id")
            if answer_id in seen_ids:
                removed_duplicate_answers += 1
                continue  # 중복된 ID는 건너뛰기
            seen_ids.add(answer_id)
            
            # answerSet 항목 속성 추출
            answer_data = {
                "id": answer_id,
                "title": answer.get("title"),
                "commentary": answer.get("commentary"),
                "answerKind": answer.get("answerKind")
            }
            
            # isCorrect 결정
            is_correct = determine_is_correct(
                question_data["titleType"], 
                answer_data["answerKind"]
            )
            
            # 최종 플래튼 항목 생성 - 요구사항에 맞는 컬럼 순서
            # question 필드에 title과 text 합치기
            question_title = question_data["title"] or ""
            question_text = question_data["text"] or ""
            combined_question = f"{question_title} {question_text}".strip()
            
            # 순서를 보장하기 위해 OrderedDict 사용
            flattened_item = OrderedDict([
                ("id", answer_data["id"]),
                ("question", combined_question),
                ("year", year),
                ("institution", institution),
                ("category1", question_data["categoryTitle"]),
                ("category2", question_data["category2"]),
                ("answer", answer_data["title"]),
                ("answerKind", answer_data["answerKind"]),
                ("isCorrect", is_correct),
                ("commentary", answer_data["commentary"])
            ])
            
            flattened_data.append(dict(flattened_item))
            
            # 문제 제목 추가 (중복 문제 계산용)
            seen_questions.add(question_data["title"])
    
    # category1로 정렬
    flattened_data.sort(key=lambda x: (x.get('category1', ''), x.get('id', 0)))
    
    # 결과 문제 수 계산 (고유한 question_title 개수)
    unique_questions = len(seen_questions)
    
    # 제거된 동일 문제 수 계산
    removed_duplicate_questions = original_questions - unique_questions
    
    stats = {
        'original_questions': original_questions,
        'original_answers': original_answers,
        'result_questions': unique_questions,
        'result_answers': len(flattened_data),
        'duplicate_count': removed_duplicate_questions,  # 제거된 동일 문제 수
        'removed_duplicate_answers': removed_duplicate_answers  # 제거된 동일 선택지 수
    }
    
    return flattened_data, stats


def classify_by_institution(data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """플래튼된 데이터를 기관별로 분류"""
    institution_groups = defaultdict(list)
    
    for item in data:
        institution = item.get('institution', 'Unknown')
        # 필드 순서 재정렬
        ordered_item = reorder_item_fields(item)
        institution_groups[institution].append(ordered_item)
    
    # 각 기관별로 연도별(내림차순) → category1 → category2 순 정렬
    for institution in institution_groups:
        institution_groups[institution].sort(key=lambda x: (
            x.get('year', 'Unknown') if x.get('year', 'Unknown') == 'Unknown' else f"Z{x.get('year', 'Unknown')}",  # Unknown을 맨 뒤로
            x.get('category1', ''),      # 2차 정렬: category1
            x.get('category2', ''),      # 3차 정렬: category2
            x.get('id', 0)               # 4차 정렬: id
        ), reverse=False)
        # 연도만 내림차순으로 재정렬
        institution_groups[institution].sort(key=lambda x: (
            '0' if x.get('year', 'Unknown') == 'Unknown' else x.get('year', 'Unknown')
        ), reverse=True)
    
    return dict(institution_groups)


def classify_by_year(data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """플래튼된 데이터를 연도별로 분류"""
    year_groups = defaultdict(list)
    
    for item in data:
        year = item.get('year', 'Unknown')
        # 필드 순서 재정렬
        ordered_item = reorder_item_fields(item)
        year_groups[year].append(ordered_item)
    
    # 각 연도별로 기관별 → category1 → category2 순 정렬
    for year in year_groups:
        year_groups[year].sort(key=lambda x: (
            x.get('institution', 'Unknown'),  # 1차 정렬: institution
            x.get('category1', ''),           # 2차 정렬: category1
            x.get('category2', ''),           # 3차 정렬: category2
            x.get('id', 0)                    # 4차 정렬: id
        ))
    
    # 연도순으로 정렬된 결과 생성 (내림차순)
    sorted_years = sorted(year_groups.keys(), key=lambda x: x if x != 'Unknown' else '0000', reverse=True)
    result = {year: year_groups[year] for year in sorted_years}
    
    return result


def classify_by_category(data: List[Dict[str, Any]], similarity_threshold: float = 0.8) -> tuple[Dict[str, List[Dict[str, Any]]], Dict[str, Any]]:
    """플래튼된 데이터를 category1별로 분류하고 중복 검출"""
    import re
    import math
    from collections import Counter
    
    def preprocess_text(text: str) -> List[str]:
        """텍스트 전처리 및 토큰화 (SimilarityDeduplicator 핵심 로직)"""
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
        
        # 조사, 어미 간소화
        text = re.sub(r'입니다', '이다', text)
        text = re.sub(r'습니다', '다', text)
        text = re.sub(r'에서', '에', text)
        
        # 토큰화 (공백 기준)
        tokens = text.strip().split()
        
        # 길이가 1인 토큰 제거 (조사 등)
        tokens = [token for token in tokens if len(token) > 1]
        
        return tokens
    
    def calculate_tf(tokens: List[str]) -> Dict[str, float]:
        """단어 빈도(TF) 계산"""
        if not tokens:
            return {}
        
        tf_dict = Counter(tokens)
        total_words = len(tokens)
        
        # 정규화
        for word in tf_dict:
            tf_dict[word] = tf_dict[word] / total_words
        
        return dict(tf_dict)
    
    def calculate_idf(documents: List[List[str]]) -> Dict[str, float]:
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
    
    def create_tfidf_vector(tf_dict: Dict[str, float], idf_dict: Dict[str, float], vocabulary: List[str]) -> List[float]:
        """TF-IDF 벡터 생성"""
        vector = []
        for word in vocabulary:
            tf = tf_dict.get(word, 0)
            idf = idf_dict.get(word, 0)
            vector.append(tf * idf)
        return vector
    
    def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """두 벡터 간의 코사인 유사도 계산"""
        if len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    def should_skip_comparison(answer1: str, answer2: str, tokens1: List[str], tokens2: List[str]) -> bool:
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
    
    # 카테고리별로 그룹화
    category_groups = defaultdict(list)
    
    for item in data:
        category1 = item.get('category1', 'Unknown')
        category_groups[category1].append(item)
    
    # 각 카테고리 내에서 중복 검출 및 처리
    threshold = similarity_threshold  # 유사도 임계값 (사용자 설정 가능)
    
    for category, items in category_groups.items():
        if len(items) <= 1:
            # 항목이 1개 이하면 중복 검출 불필요
            for item in items:
                item['isUnique'] = True
                item['similarityCount'] = None
                item['similarity'] = None
            continue
        
        # 텍스트 전처리
        answer_texts = [item.get('answer', '') for item in items]
        processed_texts = [preprocess_text(text) for text in answer_texts]
        
        # 빈 텍스트 필터링
        valid_indices = [i for i, tokens in enumerate(processed_texts) if tokens]
        
        if len(valid_indices) <= 1:
            # 유효한 텍스트가 1개 이하면 모두 중복 아님
            for item in items:
                item['isUnique'] = True
                item['similarityCount'] = None
                item['similarity'] = None
            continue
        
        # TF-IDF 계산
        valid_processed = [processed_texts[i] for i in valid_indices]
        idf_dict = calculate_idf(valid_processed)
        vocabulary = sorted(idf_dict.keys())
        
        # 각 답변의 TF-IDF 벡터 생성
        tfidf_vectors = []
        for tokens in valid_processed:
            tf_dict = calculate_tf(tokens)
            vector = create_tfidf_vector(tf_dict, idf_dict, vocabulary)
            tfidf_vectors.append(vector)
        
        # 유사도 계산 및 중복 마킹
        processed_indices = set()
        
        for i in range(len(valid_indices)):
            original_idx = valid_indices[i]
            
            if i in processed_indices:
                continue
            
            current_group = [i]
            similarities = []
            
            for j in range(i + 1, len(valid_indices)):
                if j in processed_indices:
                    continue
                
                j_original_idx = valid_indices[j]
                
                # 사전 필터링
                if should_skip_comparison(
                    answer_texts[original_idx], 
                    answer_texts[j_original_idx],
                    processed_texts[original_idx],
                    processed_texts[j_original_idx]
                ):
                    continue
                
                similarity = cosine_similarity(tfidf_vectors[i], tfidf_vectors[j])
                
                if similarity >= threshold:
                    current_group.append(j)
                    similarities.append(similarity)
                    processed_indices.add(j)
            
            # 대표 항목 선정 (가장 긴 답변을 선택)
            if len(current_group) > 1:
                # 중복 그룹이 있는 경우
                representative_idx = max(current_group, key=lambda idx: len(items[valid_indices[idx]].get('answer', '')))
                representative_original_idx = valid_indices[representative_idx]
                similarity_count = len(current_group)
                
                # 모든 그룹 멤버에 대해 속성 설정
                for group_idx in current_group:
                    group_original_idx = valid_indices[group_idx]
                    
                    # 공통 속성
                    items[group_original_idx]['similarityCount'] = similarity_count
                    
                    if group_idx == representative_idx:
                        # 대표 항목
                        items[group_original_idx]['isUnique'] = True
                        items[group_original_idx]['similarity'] = 1.0000  # 자기 자신과의 유사도는 1.0000
                    else:
                        # 중복 항목
                        items[group_original_idx]['isUnique'] = False
                        
                        # 해당 항목과 대표 항목 간의 유사도 계산
                        similarity_value = cosine_similarity(
                            tfidf_vectors[representative_idx], 
                            tfidf_vectors[group_idx]
                        )
                        items[group_original_idx]['similarity'] = round(similarity_value, 4)
                    
                    # 필드 순서 재정렬
                    items[group_original_idx] = reorder_item_fields(items[group_original_idx])
            else:
                # 중복 그룹이 없는 유일한 항목
                items[original_idx]['isUnique'] = True
                items[original_idx]['similarityCount'] = None
                items[original_idx]['similarity'] = None
            
            processed_indices.add(i)
        
        # 처리되지 않은 항목들 (빈 텍스트 등)
        for i, item in enumerate(items):
            if 'isUnique' not in item:
                item['isUnique'] = True
                item['similarityCount'] = None
                item['similarity'] = None
                # 필드 순서 재정렬
                items[i] = reorder_item_fields(item)
    
    # 각 카테고리별로 중복 그룹별 정렬 및 대표항목 ID 추가
    for category in category_groups:
        items = category_groups[category]
        
        # 1단계: 실제 중복 그룹 재식별 (기존 similarityCount는 무시하고 새로 계산)
        processed_items = set()
        similarity_groups = {}
        unique_items = []
        
        # 대표항목(isUnique=True)을 기준으로 그룹 식별
        for i, item in enumerate(items):
            if i in processed_items:
                continue
                
            similarity_count = item.get('similarityCount', 0)
            if (item.get('isUnique') == True and 
                similarity_count is not None and
                isinstance(similarity_count, (int, float)) and
                similarity_count > 1):
                # 대표항목 발견 - 이 항목과 연관된 모든 중복항목 찾기
                representative_id = item.get('id')
                current_group = [item]  # 대표항목부터 시작
                processed_items.add(i)
                
                # 같은 그룹의 중복항목들 찾기 (similarity 값이 있는 항목들)
                for j, other_item in enumerate(items):
                    similarity_val = other_item.get('similarity')
                    if (j not in processed_items and 
                        other_item.get('isUnique') == False and 
                        similarity_val is not None and
                        isinstance(similarity_val, (int, float)) and
                        similarity_val > 0):
                        current_group.append(other_item)
                        processed_items.add(j)
                
                # 실제 그룹 크기로 similarityCount 업데이트
                actual_group_size = len(current_group)
                for group_item in current_group:
                    group_item['similarityCount'] = actual_group_size
                    if group_item.get('isUnique') == True:
                        group_item['repId'] = None  # 대표항목 자신은 None
                    else:
                        group_item['repId'] = representative_id  # 중복항목은 대표항목 ID
                    # 필드 순서 재정렬 (repId 포함)
                    reordered = reorder_item_fields(group_item)
                    group_item.clear()
                    group_item.update(reordered)
                
                # 그룹 내 정렬: isUnique=True 먼저, 그 다음 유사도 높은 순
                current_group.sort(key=lambda x: (
                    not x.get('isUnique', False),    # isUnique=True가 먼저
                    -(x.get('similarity') or 0),     # 유사도 높은 순
                    x.get('id', 0)                   # ID 순
                ))
                
                similarity_groups[representative_id] = current_group
            
            else:
                similarity_count = item.get('similarityCount')
                if (similarity_count is None or 
                    (isinstance(similarity_count, (int, float)) and similarity_count <= 1)):
                    # 고유 항목
                    item['repId'] = None
                    item['similarityCount'] = None
                    # 필드 순서 재정렬
                    reordered = reorder_item_fields(item)
                    unique_items.append(reordered)
                    processed_items.add(i)
        
        # 2단계: 중복 그룹들을 대표항목 ID 순으로 정렬
        sorted_group_keys = sorted(similarity_groups.keys())
        
        # 3단계: 고유 항목들 정렬
        unique_items.sort(key=lambda x: (
            x.get('category2', ''),              # category2 오름차순
            x.get('id', 0)                       # id 오름차순
        ))
        
        # 4단계: 최종 결과 조합 (중복 그룹들 먼저, 그 다음 고유 항목들)
        final_items = []
        for group_key in sorted_group_keys:
            final_items.extend(similarity_groups[group_key])
        final_items.extend(unique_items)
        
        category_groups[category] = final_items
    
    # 카테고리명순으로 정렬된 결과 생성
    sorted_categories = sorted(category_groups.keys(), key=lambda x: x if x != 'Unknown' else 'ZZZ_Unknown')
    result = {category: category_groups[category] for category in sorted_categories}
    
    # 중복 제거 통계 계산
    total_items = len(data)
    duplicate_items = sum(1 for category_items in result.values() 
                         for item in category_items 
                         if item.get('isUnique') == False)
    unique_items = total_items - duplicate_items
    
    duplicate_percentage = (duplicate_items / total_items * 100) if total_items > 0 else 0
    unique_percentage = (unique_items / total_items * 100) if total_items > 0 else 0
    
    category_stats = {
        'total_items': total_items,
        'duplicate_items': duplicate_items,
        'unique_items': unique_items,
        'duplicate_percentage': round(duplicate_percentage, 1),
        'unique_percentage': round(unique_percentage, 1)
    }
    
    return result, category_stats


def convert_input_to_answers(input_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """기존 호환성을 위한 래퍼 함수 - 플래튼된 데이터 반환"""
    flattened_data, _ = flatten_original_data(input_data)
    return flattened_data


def validate_json_data(data: Any) -> List[Dict[str, Any]]:
    """
    Validate that the input data is a valid JSON array of question objects
    
    Args:
        data: The data to validate
        
    Returns:
        List of validated question objects
        
    Raises:
        ProcessingError: If data is invalid
    """
    if not isinstance(data, list):
        raise ProcessingError("Input data must be a JSON array")
    
    if not data:
        raise ProcessingError("Input data cannot be empty")
    
    # Basic validation of question structure
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            raise ProcessingError(f"Item {i} must be an object")
        
        required_fields = ['id', 'title']
        for field in required_fields:
            if field not in item:
                raise ProcessingError(f"Item {i} missing required field: {field}")
    
    return data


def apply_filters(data: List[Dict[str, Any]], filter_options: Dict[str, Any]) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Apply filters to the processed data (모든 필터는 처리 전에 적용되므로 이 함수는 통계만 반환)
    
    Args:
        data: List of processed data items
        filter_options: Dictionary containing filter configurations
        
    Returns:
        Tuple of (filtered_data, filter_statistics)
    """
    original_count = len(data)
    filtered_data = data.copy()
    
    # 모든 필터는 처리 전(flatten_original_data)에 적용되므로
    # 여기서는 데이터를 그대로 반환하고 통계만 생성
    
    filtered_count = len(filtered_data)
    filter_percentage = round((filtered_count / original_count * 100) if original_count > 0 else 0, 1)
    
    filter_stats = {
        'original_items': original_count,
        'filtered_items': filtered_count,
        'filter_percentage': filter_percentage
    }
    
    return filtered_data, filter_stats


def process_file_data(file_data: str, filename: str, options: List[str], similarity_threshold: float = 0.8, filter_options: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Process uploaded file data with selected classification options
    Memory-optimized version with resource management
    
    Args:
        file_data: Base64 encoded JSON file content
        filename: Original filename
        options: List of classification options ['category', 'institution', 'year']
        
    Returns:
        Dictionary with processing results
        
    Raises:
        ProcessingError: If processing fails
    """
    try:
        # Check file size before processing
        file_data_size_mb = len(file_data) / (1024 * 1024)  # Base64 size
        file_size_mb = len(file_data) * 3 / 4 / 1024 / 1024  # Estimate decoded size
        app.logger.info(f"Processing file: {filename} (base64: {file_data_size_mb:.1f}MB, decoded: ~{file_size_mb:.1f}MB)")
        
        # Implement file size limits
        max_file_size_mb = 100  # 100MB limit
        if file_size_mb > max_file_size_mb:
            error_msg = f"File too large: {file_size_mb:.1f}MB (max: {max_file_size_mb}MB)"
            app.logger.error(error_msg)
            raise ProcessingError(error_msg)
        
        # Decode base64 data
        try:
            app.logger.info(f"Decoding base64 data...")
            json_content = base64.b64decode(file_data).decode('utf-8')
            app.logger.info(f"Decoded content size: {len(json_content) / (1024 * 1024):.1f}MB")
        except Exception as e:
            error_msg = f"Failed to decode base64 data: {str(e)}"
            app.logger.error(error_msg)
            raise ProcessingError(error_msg)
        
        try:
            app.logger.info(f"Parsing JSON content...")
            input_data = json.loads(json_content)
            app.logger.info(f"JSON parsed successfully: {len(input_data)} items")
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON format: {str(e)}"
            app.logger.error(error_msg)
            raise ProcessingError(error_msg)
        
        # Validate input data
        validated_data = validate_json_data(input_data)
        
        # Check data size limits
        max_questions = 100000  # 100K questions limit
        if len(validated_data) > max_questions:
            raise ProcessingError(f"Too many questions: {len(validated_data)} (max: {max_questions})")
        
        # Memory-optimized conversion using resource manager
        def convert_chunk(chunk):
            flattened_data, _ = flatten_original_data(chunk, filter_options)
            return flattened_data
        
        # Process in chunks if dataset is large
        if len(validated_data) > 5000:
            app.logger.info(f"Large dataset detected ({len(validated_data)} questions), processing in chunks")
            flattened_data = resource_manager.process_large_dataset(validated_data, convert_chunk)
            # 청크 처리 시 통계는 별도 계산
            original_answers = sum(len(q.get("answerSet", [])) for q in validated_data)
            unique_questions = len(set(item.get('question', '') for item in flattened_data))
            removed_duplicate_answers = original_answers - len(flattened_data)
            removed_duplicate_questions = len(validated_data) - unique_questions
            stats = {
                'original_questions': len(validated_data),
                'original_answers': original_answers,
                'result_questions': unique_questions,
                'result_answers': len(flattened_data),
                'duplicate_count': removed_duplicate_questions,
                'removed_duplicate_answers': removed_duplicate_answers
            }
        else:
            flattened_data, stats = flatten_original_data(validated_data, filter_options)
        
        # 분류 옵션에 따라 다른 처리
        results_data = {}
        
        if 'flatten' in options:
            # flatten 데이터도 필드 순서 재정렬
            results_data['flatten'] = [reorder_item_fields(item) for item in flattened_data]
        
        if 'institution' in options:
            results_data['institution'] = classify_by_institution(flattened_data)
        
        if 'year' in options:
            results_data['year'] = classify_by_year(flattened_data)
        
        category_stats = None
        if 'category' in options:
            results_data['category'], category_stats = classify_by_category(flattened_data, similarity_threshold)
            
            # 중복 제거된 결과 생성 (isUnique: true인 항목만)
            category_deduplicated = {}
            for category_name, items in results_data['category'].items():
                unique_items = []
                for item in items:
                    if item.get('isUnique') == True:
                        # repId 제거한 복사본 생성
                        clean_item = {k: v for k, v in item.items() if k != 'repId'}
                        # 필드 순서 재정렬
                        clean_item = reorder_item_fields(clean_item)
                        unique_items.append(clean_item)
                if unique_items:
                    category_deduplicated[category_name] = unique_items
            
            results_data['category_deduplicated'] = category_deduplicated
        
        # Apply filters if provided
        filter_stats = None
        if filter_options:
            # Apply filters to all result types
            for result_type, result_data in results_data.items():
                if isinstance(result_data, dict):
                    # For grouped data (category, institution, year)
                    filtered_groups = {}
                    total_original = 0
                    total_filtered = 0
                    
                    for group_name, group_items in result_data.items():
                        if isinstance(group_items, list):
                            filtered_items, group_filter_stats = apply_filters(group_items, filter_options)
                            if filtered_items:  # Only include groups with remaining items
                                filtered_groups[group_name] = filtered_items
                            total_original += group_filter_stats['original_items']
                            total_filtered += group_filter_stats['filtered_items']
                    
                    results_data[result_type] = filtered_groups
                    
                    # Calculate overall filter statistics
                    if not filter_stats and total_original > 0:
                        filter_percentage = round((total_filtered / total_original * 100), 1)
                        filter_stats = {
                            'original_items': total_original,
                            'filtered_items': total_filtered,
                            'filter_percentage': filter_percentage
                        }
                        
                elif isinstance(result_data, list):
                    # For flat data (flatten)
                    filtered_items, filter_stats = apply_filters(result_data, filter_options)
                    results_data[result_type] = filtered_items
        
        # 새로운 분류 결과를 API 형식으로 변환
        api_results = []
        
        # 처리할 결과 타입 목록 (원본 옵션 + 추가 생성된 결과)
        result_types = list(options)
        if 'category' in options and 'category_deduplicated' in results_data:
            result_types.append('category_deduplicated')
        
        for option in result_types:
            if option in results_data:
                # 각 분류 결과를 저장하고 다운로드 ID 생성
                download_id = str(uuid.uuid4())
                
                # 파일명 생성 - 한국어 접미사 사용
                base_filename = os.path.splitext(filename)[0]
                if option == 'institution':
                    result_filename = f"{base_filename}_기관별.json"
                elif option == 'year':
                    result_filename = f"{base_filename}_연도별.json"
                elif option == 'category':
                    result_filename = f"{base_filename}_카테고리별.json"
                elif option == 'category_deduplicated':
                    result_filename = f"{base_filename}_카테고리별_중복제거.json"
                else:
                    result_filename = f"{base_filename}_{option}.json"
                
                # 분류 엔진에 결과 저장 (임시)
                from dataclasses import dataclass
                from datetime import datetime
                
                @dataclass
                class ClassificationResult:
                    id: str
                    type: str
                    filename: str
                    data: Any
                    created_at: datetime
                    
                    def to_dict(self):
                        return {
                            'type': self.type,
                            'filename': self.filename,
                            'download_id': self.id
                        }
                
                result = ClassificationResult(
                    id=download_id,
                    type=option,
                    filename=result_filename,
                    data=results_data[option],
                    created_at=datetime.now()
                )
                
                # 결과 저장 (classification_engine 대신 간단한 저장소 사용)
                if not hasattr(app, 'stored_results'):
                    app.stored_results = {}
                app.stored_results[download_id] = result
                
                api_results.append(result.to_dict())
        
        results = api_results
        
        # Log processing statistics
        app.logger.info(f"Processing completed: {len(validated_data)} questions -> {len(flattened_data)} flattened items")
        app.logger.info(f"Classifications generated: {len(results)}")
        
        response_data = {
            'success': True,
            'results': results,
            'processed_items': len(flattened_data),
            'original_questions': len(validated_data),
            'file_size_mb': file_size_mb,
            'statistics': stats
        }
        
        # 카테고리 분류 시 중복 제거 통계 추가
        if category_stats:
            response_data['category_statistics'] = category_stats
        
        # 필터 통계 추가
        if filter_stats:
            response_data['filter_statistics'] = filter_stats
        
        return response_data
        
    except json.JSONDecodeError as e:
        raise ProcessingError(f"Invalid JSON format: {str(e)}")
    except MemoryError:
        raise ProcessingError("File too large to process - insufficient memory")
    except Exception as e:
        app.logger.error(f"Processing error: {str(e)}")
        raise ProcessingError(f"Processing failed: {str(e)}")



@app.route('/api/process-merged', methods=['POST'])
def process_merged_files():
    """
    Process multiple uploaded files as a single merged dataset
    
    Expected JSON payload:
    {
        "files": [
            {
                "file_data": "base64_encoded_json_content",
                "filename": "file1.json"
            },
            {
                "file_data": "base64_encoded_json_content", 
                "filename": "file2.json"
            }
        ],
        "options": ["category", "institution", "year"],
        "similarity_threshold": 0.8  // Optional: 0.0-1.0, default 0.8
    }
    
    Returns:
    {
        "success": true,
        "results": [
            {
                "type": "category",
                "filename": "merged_category_classification.json",
                "download_id": "uuid"
            }
        ],
        "processed_items": 1234,
        "original_questions": 567
    }
    """
    try:
        # Log request information
        content_length = request.content_length
        if content_length:
            content_length_mb = content_length / (1024 * 1024)
            app.logger.info(f"Received process-merged request: {content_length_mb:.2f}MB from {request.remote_addr}")
        else:
            app.logger.info(f"Received process-merged request from {request.remote_addr}")
        # Validate request
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_REQUEST',
                    'message': 'Request must be JSON',
                    'details': 'Content-Type must be application/json'
                }
            }), 400
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['files', 'options']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'MISSING_FIELD',
                        'message': f'Missing required field: {field}',
                        'details': f'The field "{field}" is required in the request body'
                    }
                }), 400
        
        # Validate files array
        files = data['files']
        if not isinstance(files, list) or not files:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_FILES',
                    'message': 'Files must be a non-empty array',
                    'details': 'Provide at least one file to process'
                }
            }), 400
        
        # Validate each file in the array
        for i, file_info in enumerate(files):
            if not isinstance(file_info, dict):
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'INVALID_FILE_FORMAT',
                        'message': f'File {i+1} must be an object',
                        'details': 'Each file must have file_data and filename fields'
                    }
                }), 400
            
            if 'file_data' not in file_info or 'filename' not in file_info:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'MISSING_FILE_FIELDS',
                        'message': f'File {i+1} missing required fields',
                        'details': 'Each file must have file_data and filename fields'
                    }
                }), 400
        
        # Validate options
        valid_options = {'category', 'institution', 'year', 'flatten'}
        options = data['options']
        
        if not isinstance(options, list) or not options:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_OPTIONS',
                    'message': 'At least one processing option must be selected',
                    'details': f'Valid options are: {", ".join(valid_options)}'
                }
            }), 400
        
        invalid_options = set(options) - valid_options
        if invalid_options:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_OPTIONS',
                    'message': f'Invalid processing options: {", ".join(invalid_options)}',
                    'details': f'Valid options are: {", ".join(valid_options)}'
                }
            }), 400
        
        # Get similarity threshold from request (default: 0.8)
        similarity_threshold = data.get('similarity_threshold', 0.8)
        
        # Validate similarity threshold
        if not isinstance(similarity_threshold, (int, float)) or not (0.0 <= similarity_threshold <= 1.0):
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_SIMILARITY_THRESHOLD',
                    'message': 'Similarity threshold must be a number between 0.0 and 1.0',
                    'details': f'Received: {similarity_threshold}'
                }
            }), 400
        
        # Get filter options from request (optional)
        filter_options = data.get('filter_options', None)
        
        # Merge all files into a single dataset
        merged_data = []
        total_file_size_mb = 0
        filenames = []
        
        for file_info in files:
            try:
                # Decode base64 data
                json_content = base64.b64decode(file_info['file_data']).decode('utf-8')
                file_data = json.loads(json_content)
                
                # Validate individual file data
                validated_data = validate_json_data(file_data)
                merged_data.extend(validated_data)
                
                # Track file info
                file_size_mb = len(file_info['file_data']) * 3 / 4 / 1024 / 1024
                total_file_size_mb += file_size_mb
                filenames.append(file_info['filename'])
                
                app.logger.info(f"Merged file: {file_info['filename']} (~{file_size_mb:.1f}MB, {len(validated_data)} questions)")
                
            except json.JSONDecodeError as e:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'INVALID_JSON',
                        'message': f'Invalid JSON in file {file_info["filename"]}: {str(e)}',
                        'details': 'Please ensure all files contain valid JSON data'
                    }
                }), 400
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'FILE_PROCESSING_ERROR',
                        'message': f'Error processing file {file_info["filename"]}: {str(e)}',
                        'details': 'Please check the file format and try again'
                    }
                }), 400
        
        # Check merged data size limits
        max_questions = 100000  # 100K questions limit
        if len(merged_data) > max_questions:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'DATASET_TOO_LARGE',
                    'message': f'Merged dataset too large: {len(merged_data)} questions (max: {max_questions})',
                    'details': 'Please reduce the number of files or questions per file'
                }
            }), 400
        
        # Generate merged filename
        if len(filenames) == 1:
            merged_filename = filenames[0]
        else:
            # Create a descriptive merged filename
            base_names = [os.path.splitext(name)[0] for name in filenames[:3]]  # Use first 3 filenames
            if len(filenames) > 3:
                merged_filename = f"merged_{'+'.join(base_names)}_and_{len(filenames)-3}_more.json"
            else:
                merged_filename = f"merged_{'+'.join(base_names)}.json"
        
        app.logger.info(f"Processing merged dataset: {len(merged_data)} questions from {len(files)} files (~{total_file_size_mb:.1f}MB total)")
        
        # Process the merged dataset using existing logic
        result = process_file_data(
            file_data=base64.b64encode(json.dumps(merged_data).encode('utf-8')).decode('utf-8'),
            filename=merged_filename,
            options=options,
            similarity_threshold=similarity_threshold,
            filter_options=filter_options
        )
        
        # Add merge information to the response
        result['merge_info'] = {
            'source_files': filenames,
            'total_files': len(files),
            'total_size_mb': round(total_file_size_mb, 2)
        }
        
        return jsonify(result)
        
    except ProcessingError as e:
        app.logger.error(f"Processing error in merged files: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'PROCESSING_ERROR',
                'message': str(e),
                'details': 'Merged file processing failed'
            }
        }), 400
    
    except BadRequest as e:
        app.logger.error(f"Bad request error in merged files: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'BAD_REQUEST',
                'message': 'Invalid request format or size',
                'details': str(e)
            }
        }), 413 if 'too large' in str(e).lower() else 400
        
    except Exception as e:
        app.logger.error(f"Unexpected error in process_merged_files: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An unexpected error occurred during merged processing',
                'details': str(e)
            }
        }), 500


@app.route('/api/process', methods=['POST'])
def process_file():
    """
    Process uploaded file with selected classification options
    
    Expected JSON payload:
    {
        "file_data": "base64_encoded_json_content",
        "filename": "original_filename.json",
        "options": ["category", "institution", "year"],
        "similarity_threshold": 0.8  // Optional: 0.0-1.0, default 0.8
    }
    
    Returns:
    {
        "success": true,
        "results": [
            {
                "type": "category",
                "filename": "category_classification.json",
                "download_id": "uuid"
            }
        ],
        "processed_items": 1234,
        "original_questions": 567
    }
    """
    try:
        # Log request information
        content_length = request.content_length
        if content_length:
            content_length_mb = content_length / (1024 * 1024)
            app.logger.info(f"Received process request: {content_length_mb:.2f}MB from {request.remote_addr}")
        else:
            app.logger.info(f"Received process request from {request.remote_addr}")
        # Validate request
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_REQUEST',
                    'message': 'Request must be JSON',
                    'details': 'Content-Type must be application/json'
                }
            }), 400
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['file_data', 'filename', 'options']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'MISSING_FIELD',
                        'message': f'Missing required field: {field}',
                        'details': f'The field "{field}" is required in the request body'
                    }
                }), 400
        
        # Validate options
        valid_options = {'category', 'institution', 'year', 'flatten'}
        options = data['options']
        
        if not isinstance(options, list) or not options:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_OPTIONS',
                    'message': 'At least one processing option must be selected',
                    'details': f'Valid options are: {", ".join(valid_options)}'
                }
            }), 400
        
        invalid_options = set(options) - valid_options
        if invalid_options:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_OPTIONS',
                    'message': f'Invalid processing options: {", ".join(invalid_options)}',
                    'details': f'Valid options are: {", ".join(valid_options)}'
                }
            }), 400
        
        # Get similarity threshold from request (default: 0.8)
        similarity_threshold = data.get('similarity_threshold', 0.8)
        
        # Validate similarity threshold
        if not isinstance(similarity_threshold, (int, float)) or not (0.0 <= similarity_threshold <= 1.0):
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_SIMILARITY_THRESHOLD',
                    'message': 'Similarity threshold must be a number between 0.0 and 1.0',
                    'details': f'Received: {similarity_threshold}'
                }
            }), 400
        
        # Get filter options from request (optional)
        filter_options = data.get('filter_options', None)
        
        # Process the file
        result = process_file_data(
            file_data=data['file_data'],
            filename=data['filename'],
            options=options,
            similarity_threshold=similarity_threshold,
            filter_options=filter_options
        )
        
        return jsonify(result)
        
    except ProcessingError as e:
        app.logger.error(f"Processing error: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'PROCESSING_ERROR',
                'message': str(e),
                'details': 'File processing failed'
            }
        }), 400
    
    except BadRequest as e:
        app.logger.error(f"Bad request error: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'BAD_REQUEST',
                'message': 'Invalid request format or size',
                'details': str(e)
            }
        }), 413 if 'too large' in str(e).lower() else 400
        
    except Exception as e:
        app.logger.error(f"Unexpected error in process_file: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An unexpected error occurred',
                'details': str(e)
            }
        }), 500


@app.route('/api/data/<download_id>', methods=['GET'])
def get_data(download_id: str):
    """
    Get processed data by ID (for markdown conversion)
    
    Args:
        download_id: UUID of the processed file
        
    Returns:
        JSON data or error response
    """
    try:
        # Check if download ID exists in stored results
        if not hasattr(app, 'stored_results') or download_id not in app.stored_results:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'FILE_NOT_FOUND',
                    'message': 'Download ID not found',
                    'details': 'The requested file may have expired or does not exist'
                }
            }), 404
        
        result = app.stored_results[download_id]
        
        # Return the data directly as JSON
        return jsonify(result.data)
            
    except Exception as e:
        app.logger.error(f"Data fetch error: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'DATA_FETCH_ERROR',
                'message': 'Failed to fetch data',
                'details': str(e)
            }
        }), 500

@app.route('/api/download-multiple', methods=['POST'])
def download_multiple_files():
    """
    Download multiple processed files as a ZIP archive
    
    Expected JSON payload:
    {
        "result_ids": ["uuid1", "uuid2", "uuid3"],
        "archive_name": "processed_files.zip"
    }
    
    Returns:
        ZIP file download or error response
    """
    try:
        app.logger.info(f"Received download-multiple request from {request.remote_addr}")
        app.logger.info(f"Request method: {request.method}")
        app.logger.info(f"Request content type: {request.content_type}")
        
        # Validate request
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_REQUEST',
                    'message': 'Request must be JSON',
                    'details': 'Content-Type must be application/json'
                }
            }), 400
        
        data = request.get_json()
        
        # Validate required fields
        if 'result_ids' not in data:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'MISSING_FIELD',
                    'message': 'Missing required field: result_ids',
                    'details': 'The field "result_ids" is required in the request body'
                }
            }), 400
        
        result_ids = data['result_ids']
        archive_name = data.get('archive_name', 'processed_files.zip')
        
        # Validate result_ids
        if not isinstance(result_ids, list) or not result_ids:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_RESULT_IDS',
                    'message': 'result_ids must be a non-empty array',
                    'details': 'Provide at least one result ID to download'
                }
            }), 400
        
        # Check if all result IDs exist
        if not hasattr(app, 'stored_results'):
            return jsonify({
                'success': False,
                'error': {
                    'code': 'NO_RESULTS',
                    'message': 'No processed results available',
                    'details': 'No files have been processed yet'
                }
            }), 404
        
        missing_ids = []
        valid_result_ids = []
        
        for result_id in result_ids:
            # Check if this is a markdown request (result_id ends with '_md')
            if result_id.endswith('_md'):
                # For markdown requests, check if the original ID exists
                original_id = result_id[:-3]  # Remove '_md' suffix
                if original_id in app.stored_results:
                    valid_result_ids.append(result_id)
                else:
                    missing_ids.append(result_id)
            else:
                # For regular requests, check if the ID exists directly
                if result_id in app.stored_results:
                    valid_result_ids.append(result_id)
                else:
                    missing_ids.append(result_id)
        
        if missing_ids:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'FILES_NOT_FOUND',
                    'message': f'Some files not found: {len(missing_ids)} missing',
                    'details': f'Missing IDs: {", ".join(missing_ids[:5])}{"..." if len(missing_ids) > 5 else ""}'
                }
            }), 404
        
        if not valid_result_ids:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'NO_VALID_FILES',
                    'message': 'No valid files to download',
                    'details': 'All requested files are invalid or expired'
                }
            }), 404
        
        # Create ZIP archive
        import zipfile
        import io
        
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for result_id in valid_result_ids:
                
                try:
                    # Check if this is a markdown request (result_id ends with '_md')
                    if result_id.endswith('_md'):
                        # This is a markdown conversion request
                        original_id = result_id[:-3]  # Remove '_md' suffix
                        if original_id in app.stored_results:
                            original_result = app.stored_results[original_id]
                            
                            # Determine exclude columns based on result type
                            exclude_columns = []
                            if original_result.type == 'category':
                                exclude_columns = ['category1']  # category2는 유지
                            elif original_result.type == 'category_deduplicated':
                                exclude_columns = ['category1', 'isUnique', 'similarity', 'similarityCount', 'repId']  # category2는 유지
                            
                            # Convert to markdown
                            markdown_content = convert_json_to_markdown(original_result.data, exclude_columns)
                            markdown_filename = original_result.filename.replace('.json', '.md')
                            
                            # Add markdown file to ZIP
                            zip_file.writestr(markdown_filename, markdown_content.encode('utf-8'))
                        else:
                            app.logger.warning(f"Original result not found for markdown conversion: {original_id}")
                    else:
                        # Regular JSON file
                        if result_id in app.stored_results:
                            result = app.stored_results[result_id]
                            json_content = json.dumps(result.data, ensure_ascii=False, indent=2)
                            zip_file.writestr(result.filename, json_content.encode('utf-8'))
                        else:
                            app.logger.warning(f"Result not found: {result_id}")
                    
                except Exception as e:
                    app.logger.warning(f"Failed to add file {result_id} to ZIP: {str(e)}")
                    continue
        
        zip_buffer.seek(0)
        
        # Validate ZIP content
        if zip_buffer.getvalue() == b'':
            return jsonify({
                'success': False,
                'error': {
                    'code': 'EMPTY_ARCHIVE',
                    'message': 'Failed to create archive',
                    'details': 'No files could be added to the archive'
                }
            }), 500
        
        # Create response with ZIP file
        response = send_file(
            io.BytesIO(zip_buffer.getvalue()),
            as_attachment=True,
            download_name=archive_name,
            mimetype='application/zip'
        )
        
        # Clean up downloaded results after successful bulk download
        @response.call_on_close
        def cleanup():
            try:
                for result_id in result_ids:
                    # For markdown requests, don't delete the original result
                    if result_id.endswith('_md'):
                        continue
                    # Only delete actual stored results
                    if hasattr(app, 'stored_results') and result_id in app.stored_results:
                        del app.stored_results[result_id]
            except Exception as e:
                app.logger.error(f"Cleanup error after bulk download: {str(e)}")
        
        app.logger.info(f"Bulk download completed: {len(valid_result_ids)} files in {archive_name}")
        return response
        
    except Exception as e:
        app.logger.error(f"Bulk download error: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'BULK_DOWNLOAD_ERROR',
                'message': 'Failed to create bulk download',
                'details': str(e)
            }
        }), 500


@app.route('/api/convert-to-markdown/<download_id>', methods=['GET'])
def convert_to_markdown(download_id: str):
    """
    Convert processed JSON data to Markdown format
    
    Args:
        download_id: UUID of the processed file
        
    Returns:
        Markdown file download or error response
    """
    try:
        # Check if download ID exists in stored results
        if not hasattr(app, 'stored_results') or download_id not in app.stored_results:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'FILE_NOT_FOUND',
                    'message': 'Download ID not found',
                    'details': 'The requested file may have expired or does not exist'
                }
            }), 404
        
        result = app.stored_results[download_id]
        
        # Automatically exclude columns based on classification type
        exclude_columns = []
        if result.type == 'category':
            exclude_columns.extend(['category1'])  # category2는 유지
        elif result.type == 'category_deduplicated':
            exclude_columns.extend(['category1', 'isUnique', 'similarity', 'similarityCount', 'repId'])  # category2는 유지
        
        # Convert to markdown
        markdown_content = convert_json_to_markdown(result.data, exclude_columns)
        
        # Generate markdown filename
        markdown_filename = result.filename.replace('.json', '.md')
        
        # Create temporary file for download
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as temp_file:
            temp_file.write(markdown_content)
            temp_file_path = temp_file.name
        
        try:
            # Send file and clean up
            response = send_file(
                temp_file_path,
                as_attachment=True,
                download_name=markdown_filename,
                mimetype='text/markdown'
            )
            
            # Clean up temporary file after sending
            @response.call_on_close
            def cleanup():
                try:
                    os.unlink(temp_file_path)
                except Exception as e:
                    app.logger.error(f"Cleanup error: {str(e)}")
            
            return response
            
        except Exception as e:
            # Clean up temp file if send_file fails
            try:
                os.unlink(temp_file_path)
            except:
                pass
            raise e
            
    except Exception as e:
        app.logger.error(f"Markdown conversion error: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'MARKDOWN_CONVERSION_ERROR',
                'message': 'Failed to convert to markdown',
                'details': str(e)
            }
        }), 500


@app.route('/api/download/<download_id>', methods=['GET'])
def download_file(download_id: str):
    """
    Download processed file by ID
    
    Args:
        download_id: UUID of the processed file
        
    Returns:
        JSON file download or error response
    """
    try:
        # Check if download ID exists in stored results
        if not hasattr(app, 'stored_results') or download_id not in app.stored_results:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'FILE_NOT_FOUND',
                    'message': 'Download ID not found',
                    'details': 'The requested file may have expired or does not exist'
                }
            }), 404
        
        result = app.stored_results[download_id]
        
        # Create temporary file for download
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as temp_file:
            json.dump(result.data, temp_file, ensure_ascii=False, indent=2)
            temp_file_path = temp_file.name
        
        try:
            # Send file and clean up
            response = send_file(
                temp_file_path,
                as_attachment=True,
                download_name=result.filename,
                mimetype='application/json'
            )
            
            # Clean up temporary file after sending
            @response.call_on_close
            def cleanup():
                try:
                    os.unlink(temp_file_path)
                    # Remove from stored results after successful download
                    if hasattr(app, 'stored_results') and download_id in app.stored_results:
                        del app.stored_results[download_id]
                except Exception as e:
                    app.logger.error(f"Cleanup error: {str(e)}")
            
            return response
            
        except Exception as e:
            # Clean up temp file if send_file fails
            try:
                os.unlink(temp_file_path)
            except:
                pass
            raise e
            
    except Exception as e:
        app.logger.error(f"Download error: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'DOWNLOAD_ERROR',
                'message': 'Failed to download file',
                'details': str(e)
            }
        }), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint with resource statistics"""
    try:
        resource_stats = resource_manager.cleanup_and_get_stats()
        stored_results_count = len(getattr(app, 'stored_results', {}))
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'stored_results_count': stored_results_count,
            'resource_stats': {
                'current_memory_mb': resource_stats['current_memory_mb'],
                'registered_temp_files': resource_stats['file_stats']['registered_files'],
                'processing_stats': resource_stats['processing_stats']
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'stored_results_count': len(getattr(app, 'stored_results', {})),
            'note': 'Resource manager not available'
        })


@app.route('/api/cleanup', methods=['POST'])
def cleanup_resources():
    """Manual cleanup endpoint for maintenance"""
    try:
        # Clean up expired stored results (older than 1 hour)
        expired_count = 0
        if hasattr(app, 'stored_results'):
            current_time = datetime.now()
            expired_ids = []
            
            for result_id, result in app.stored_results.items():
                if hasattr(result, 'created_at'):
                    age_hours = (current_time - result.created_at).total_seconds() / 3600
                    if age_hours > 1:
                        expired_ids.append(result_id)
            
            for result_id in expired_ids:
                del app.stored_results[result_id]
                expired_count += 1
        
        # Clean up resource manager
        try:
            resource_stats = resource_manager.cleanup_and_get_stats()
            cleanup_stats = {
                'expired_results_cleaned': expired_count,
                'files_cleaned': resource_stats['cleanup_stats']['cleaned_files'],
                'memory_freed': resource_stats['memory_stats']['objects_freed'],
                'current_memory_mb': resource_stats['current_memory_mb']
            }
        except:
            cleanup_stats = {
                'expired_results_cleaned': expired_count,
                'note': 'Resource manager cleanup not available'
            }
        
        return jsonify({
            'success': True,
            'cleanup_stats': cleanup_stats
        })
        
    except Exception as e:
        app.logger.error(f"Cleanup error: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'CLEANUP_ERROR',
                'message': 'Failed to cleanup resources',
                'details': str(e)
            }
        }), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'success': False,
        'error': {
            'code': 'NOT_FOUND',
            'message': 'Endpoint not found',
            'details': 'The requested API endpoint does not exist'
        }
    }), 404


@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle 413 errors (request too large)"""
    app.logger.error(f"Request too large: {error}")
    return jsonify({
        'success': False,
        'error': {
            'code': 'REQUEST_TOO_LARGE',
            'message': 'Request entity too large',
            'details': f'The uploaded file exceeds the maximum allowed size of {app.config["MAX_CONTENT_LENGTH"] / (1024 * 1024):.0f}MB'
        }
    }), 413


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    app.logger.error(f"Internal server error: {error}", exc_info=True)
    return jsonify({
        'success': False,
        'error': {
            'code': 'INTERNAL_ERROR',
            'message': 'Internal server error',
            'details': 'An unexpected error occurred on the server'
        }
    }), 500


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    """Serve React frontend for all non-API routes"""
    if path.startswith('api/'):
        # API routes should return 404 if not found
        abort(404)
    
    # Try to serve static file first
    if path and os.path.exists(os.path.join(app.static_folder, path)):
        return app.send_static_file(path)
    
    # Fallback to index.html for React routing
    return app.send_static_file('index.html')


if __name__ == '__main__':
    # Development server
    app.run(debug=True, host='0.0.0.0', port=5001)