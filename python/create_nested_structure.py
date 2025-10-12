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