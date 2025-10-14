import json
from typing import Dict, List, Any
from collections import defaultdict

def create_nested_structure(input_file: str, output_file: str) -> Dict[str, Dict[str, List[Dict]]]:
    """
    Create nested structure by category1 and category2 from input JSON file
    
    Args:
        input_file: Path to input JSON file
        output_file: Path to output JSON file
    
    Returns:
        Nested dictionary structure
    """
    # Read input data
    with open(input_file, 'r', encoding='utf-8') as f:
        input_data = json.load(f)
    
    # Create nested structure
    nested_output = defaultdict(lambda: defaultdict(list))
    
    for item in input_data:
        category1_key = item['category1']
        category2_key = item['category2']
        nested_output[category1_key][category2_key].append(item)
    
    # Convert defaultdict to regular dict for JSON serialization
    result = {
        cat1: dict(cat2_dict) 
        for cat1, cat2_dict in nested_output.items()
    }
    
    # Write output file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    # Print statistics
    print(f'Successfully created nested JSON structure: {output_file}')
    print(f'Total categories: {len(result)}')
    for cat1 in result:
        print(f'{cat1}: {len(result[cat1])} subcategories')
    
    return result

def create_nested_from_data(unique_answers: List[Dict], similar_groups: List[Dict]):
    """Create nested structures directly from data (without reading files)"""
    
    print("Creating nested structure for unique answers...")
    unique_nested = defaultdict(lambda: defaultdict(list))
    
    for item in unique_answers:
        category1_key = item['category1']
        category2_key = item['category2']
        unique_nested[category1_key][category2_key].append(item)
    
    # Convert to regular dict
    unique_result = {
        cat1: dict(cat2_dict) 
        for cat1, cat2_dict in unique_nested.items()
    }
    
    # Write unique nested file
    with open('data/answers_similarity_unique_nested.json', 'w', encoding='utf-8') as f:
        json.dump(unique_result, f, ensure_ascii=False, indent=2)
    
    print(f'Successfully created nested JSON structure: data/answers_similarity_unique_nested.json')
    print(f'Total categories: {len(unique_result)}')
    for cat1 in unique_result:
        print(f'{cat1}: {len(unique_result[cat1])} subcategories')
    
    print("\nCreating nested structure for similar groups...")
    groups_nested = defaultdict(lambda: defaultdict(list))
    
    for item in similar_groups:
        category1_key = item['category1']
        category2_key = item['category2']
        groups_nested[category1_key][category2_key].append(item)
    
    # Convert to regular dict
    groups_result = {
        cat1: dict(cat2_dict) 
        for cat1, cat2_dict in groups_nested.items()
    }
    
    # Write groups nested file
    with open('data/answers_similarity_removed_nested.json', 'w', encoding='utf-8') as f:
        json.dump(groups_result, f, ensure_ascii=False, indent=2)
    
    print(f'Successfully created nested JSON structure: data/answers_similarity_removed_nested.json')
    print(f'Total categories: {len(groups_result)}')
    for cat1 in groups_result:
        print(f'{cat1}: {len(groups_result[cat1])} subcategories')
    
    print("\nBoth nested structures created successfully!")

def process_both_files():
    """Process both similarity files and create nested structures"""
    
    # Process answers_similarity_removed.json
    print("Processing answers_similarity_removed.json...")
    create_nested_structure(
        'data/answers_similarity_removed.json',
        'data/answers_similarity_removed_nested.json'
    )
    
    print("\nProcessing answers_similarity_unique.json...")
    create_nested_structure(
        'data/answers_similarity_unique.json', 
        'data/answers_similarity_unique_nested.json'
    )
    
    print("\nBoth nested structures created successfully!")

if __name__ == "__main__":
    process_both_files()