"""
Test script for enhanced main.py functionality
"""

import json
import os
import sys
from main import convert_input_to_answers, classify_by_institution, classify_by_year

def test_enhanced_functionality():
    """Test the enhanced main.py functionality with sample data"""
    
    # Create sample test data based on input1.json structure
    sample_data = [
        {
            "id": 51596,
            "title": "지방자치권의 제도적 보장설에 대한 설명으로 옳은 것은?",
            "solve": "지방직 7급 / 2022",
            "categoryTitle": "1) 지방행정과 지방자치권",
            "answerSet": [
                {
                    "id": 189210,
                    "title": "지방자치단체는 국가의 성립 이전에 형성된 것으로 본다.",
                    "answerKind": "X"
                },
                {
                    "id": 189212,
                    "title": "지방자치를 헌법으로 보장함으로써 법률에 의해서 지방자치 제도를 폐지할 수 없다고 본다.",
                    "answerKind": "O"
                }
            ]
        },
        {
            "id": 52052,
            "title": "우리나라의 지방자치에 대한 설명으로 가장 옳지 않은 것은?",
            "solve": "서울시 7급 / 2022",
            "categoryTitle": "2) 지방자치의 변천",
            "answerSet": [
                {
                    "id": 190981,
                    "title": "우리나라의 『지방자치법』은 1949년 7월 4일 처음으로 제정되었다.",
                    "answerKind": "X"
                },
                {
                    "id": 190982,
                    "title": "1992년 노태우 대통령 당시, 광역의원과 지방자치단체장이 선출되었다.",
                    "answerKind": "O"
                }
            ]
        },
        {
            "id": 52103,
            "title": "자치제도의 특례에 대한 설명으로 옳지 않은 것은?",
            "solve": "지방직 7급 / 2021",
            "categoryTitle": "1) 지방행정과 지방자치",
            "answerSet": [
                {
                    "id": 191185,
                    "title": "인구 500만 이상의 시·도는 부시장이나 부지사의 수를 최대 4명 이하로 할 수 있는 특례를 두고 있다.",
                    "answerKind": "O"
                }
            ]
        }
    ]
    
    print("Testing enhanced main.py functionality...")
    print(f"Sample data: {len(sample_data)} questions")
    
    # Test convert_input_to_answers with enhanced fields
    print("\n1. Testing convert_input_to_answers with enhanced fields...")
    answers = convert_input_to_answers(sample_data)
    
    print(f"Generated {len(answers)} answer items")
    
    # Check if enhanced fields are present
    if answers:
        sample_answer = answers[0]
        print("Sample answer fields:", list(sample_answer.keys()))
        print("Institution:", sample_answer.get('institution'))
        print("Year:", sample_answer.get('year'))
        print("Solve:", sample_answer.get('solve'))
    
    # Test institution classification
    print("\n2. Testing institution classification...")
    institution_result = classify_by_institution(answers)
    print("Institution groups:", list(institution_result.keys()))
    for inst, items in institution_result.items():
        print(f"  {inst}: {len(items)} items")
    
    # Test year classification
    print("\n3. Testing year classification...")
    year_result = classify_by_year(answers)
    print("Year groups:", list(year_result.keys()))
    for year, items in year_result.items():
        print(f"  {year}: {len(items)} items")
    
    print("\nTest completed successfully!")
    
    # Cleanup test files
    test_files = [
        "data/institution_classification.json",
        "data/year_classification.json"
    ]
    
    for file_path in test_files:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Cleaned up: {file_path}")

if __name__ == "__main__":
    test_enhanced_functionality()