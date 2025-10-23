#!/usr/bin/env python3
"""
Category classification with duplicate detection test
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/python')

from app import classify_by_category
import json

# Test data with similar answers
test_data = [
    {
        "id": 1,
        "question": "What is 2+2?",
        "answer": "The answer is 4. This is basic arithmetic.",
        "category1": "Math",
        "category2": "Arithmetic"
    },
    {
        "id": 2,
        "question": "What is two plus two?",
        "answer": "The answer is 4.",
        "category1": "Math", 
        "category2": "Arithmetic"
    },
    {
        "id": 3,
        "question": "What is the capital of France?",
        "answer": "The capital of France is Paris.",
        "category1": "Geography",
        "category2": "Europe"
    }
]

print("Testing category classification with duplicate detection...")
result = classify_by_category(test_data)

print("\nResult:")
print(json.dumps(result, indent=2, ensure_ascii=False))

# Check if similarityCount and similarity are present
for category, items in result.items():
    print(f"\nCategory: {category}")
    for item in items:
        print(f"  ID: {item['id']}")
        print(f"  isUnique: {item.get('isUnique')}")
        if 'similarityCount' in item:
            print(f"  similarityCount: {item['similarityCount']}")
        if 'similarity' in item:
            print(f"  similarity: {item['similarity']}")
        print()