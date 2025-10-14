"""
Test script for ClassificationEngine with multiple simultaneous classifications
"""

import json
from processors.classifier import ClassificationEngine, ClassificationResult
from main import convert_input_to_answers
from remove_similarity_duplicates import SimilarityDeduplicator


def create_test_data():
    """Create comprehensive test data"""
    return [
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
        },
        {
            "id": 52192,
            "title": "단체자치와 주민자치에 대한 설명으로 옳은 것은?",
            "solve": "지방직 7급 / 2020",
            "categoryTitle": "1) 지방행정과 지방자치",
            "answerSet": [
                {
                    "id": 191541,
                    "title": "단체자치는 영국을 중심으로 발전하였으며, 정치적 의미의 자치라고 불린다.",
                    "answerKind": "X"
                },
                {
                    "id": 191542,
                    "title": "주민자치 개념이 발달한 국가에서는 주로 개별적 수권방식을 채택하였다.",
                    "answerKind": "O"
                }
            ]
        }
    ]


def test_classification_engine():
    """Test the ClassificationEngine with multiple simultaneous classifications"""
    
    print("Testing ClassificationEngine...")
    print("=" * 50)
    
    # Create test data
    test_data = create_test_data()
    print(f"Test data: {len(test_data)} questions")
    
    # Convert to answers format
    answers = convert_input_to_answers(test_data)
    print(f"Generated {len(answers)} answer items")
    
    # Create classification engine
    engine = ClassificationEngine()
    
    # Test 1: Single classification
    print("\n1. Testing single classification (institution only)...")
    results = engine.process_multiple_classifications(
        data=answers,
        options=['institution']
    )
    
    print(f"Generated {len(results)} result files")
    for result in results:
        print(f"  - {result.type}: {result.filename} (ID: {result.id[:8]}...)")
        print(f"    Data keys: {list(result.data.keys())}")
    
    # Test 2: Multiple classifications
    print("\n2. Testing multiple simultaneous classifications...")
    results = engine.process_multiple_classifications(
        data=answers,
        options=['institution', 'year']
    )
    
    print(f"Generated {len(results)} result files")
    for result in results:
        print(f"  - {result.type}: {result.filename} (ID: {result.id[:8]}...)")
        print(f"    Data keys: {list(result.data.keys())}")
        
        # Show sample data structure
        if result.data:
            first_key = list(result.data.keys())[0]
            sample_items = result.data[first_key]
            print(f"    Sample group '{first_key}': {len(sample_items)} items")
    
    # Test 3: All classifications including category
    print("\n3. Testing all classification types...")
    
    # Create similarity processor for category classification
    similarity_processor = SimilarityDeduplicator(
        input_file=None,
        output_dir="data",
        threshold=0.8
    )
    
    results = engine.process_multiple_classifications(
        data=answers,
        options=['category', 'institution', 'year'],
        similarity_processor=similarity_processor
    )
    
    print(f"Generated {len(results)} result files")
    for result in results:
        print(f"  - {result.type}: {result.filename} (ID: {result.id[:8]}...)")
        
        if result.type == 'category':
            # Category results are nested
            print(f"    Categories: {list(result.data.keys())}")
            for cat1, cat2_dict in result.data.items():
                print(f"      {cat1}: {list(cat2_dict.keys())}")
        else:
            print(f"    Groups: {list(result.data.keys())}")
    
    # Test 4: Engine management features
    print("\n4. Testing engine management features...")
    
    # Get stats
    stats = engine.get_stats()
    print(f"Engine stats: {stats}")
    
    # Test result retrieval
    if results:
        test_id = results[0].id
        retrieved_result = engine.get_result(test_id)
        if retrieved_result:
            print(f"✅ Successfully retrieved result: {retrieved_result.type}")
        else:
            print("❌ Failed to retrieve result")
        
        # Test result removal
        removed = engine.remove_result(test_id)
        if removed:
            print(f"✅ Successfully removed result: {test_id[:8]}...")
        else:
            print("❌ Failed to remove result")
        
        # Verify removal
        retrieved_after_removal = engine.get_result(test_id)
        if retrieved_after_removal is None:
            print("✅ Result properly removed from engine")
        else:
            print("❌ Result still exists after removal")
    
    # Test 5: Verify data integrity
    print("\n5. Testing data integrity...")
    
    # Process institution classification and verify data
    institution_results = engine.process_multiple_classifications(
        data=answers,
        options=['institution']
    )
    
    if institution_results:
        institution_result = institution_results[0]
        total_items_in_result = sum(len(items) for items in institution_result.data.values())
        
        print(f"Original answers: {len(answers)}")
        print(f"Items in institution classification: {total_items_in_result}")
        
        if total_items_in_result == len(answers):
            print("✅ Data integrity verified - no items lost")
        else:
            print("❌ Data integrity issue - item count mismatch")
        
        # Verify institution extraction
        expected_institutions = set()
        for answer in answers:
            expected_institutions.add(answer.get('institution', 'Unknown'))
        
        actual_institutions = set(institution_result.data.keys())
        
        if expected_institutions == actual_institutions:
            print("✅ Institution extraction verified")
            print(f"Institutions found: {sorted(actual_institutions)}")
        else:
            print("❌ Institution extraction mismatch")
            print(f"Expected: {sorted(expected_institutions)}")
            print(f"Actual: {sorted(actual_institutions)}")
    
    print("\n✅ ClassificationEngine testing completed!")


if __name__ == "__main__":
    test_classification_engine()