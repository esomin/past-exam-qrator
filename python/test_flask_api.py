"""
Test script for Flask API endpoints
"""

import json
import base64
import requests
import time
from typing import Dict, Any


def create_test_data() -> str:
    """Create base64 encoded test data"""
    test_data = [
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
        }
    ]
    
    json_str = json.dumps(test_data, ensure_ascii=False)
    return base64.b64encode(json_str.encode('utf-8')).decode('utf-8')


def test_api_endpoints():
    """Test Flask API endpoints"""
    base_url = "http://localhost:5000"
    
    print("Testing Flask API endpoints...")
    
    # Test health check
    print("\n1. Testing health check endpoint...")
    try:
        response = requests.get(f"{base_url}/api/health")
        print(f"Health check status: {response.status_code}")
        if response.status_code == 200:
            print("Health check response:", response.json())
        else:
            print("Health check failed:", response.text)
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Flask server. Make sure it's running on port 5000")
        return False
    
    # Test file processing
    print("\n2. Testing file processing endpoint...")
    
    test_file_data = create_test_data()
    
    payload = {
        "file_data": test_file_data,
        "filename": "test_data.json",
        "options": ["category", "institution", "year"]
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/process",
            json=payload,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Process endpoint status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Processing successful!")
            print(f"Processed {result.get('processed_items')} items from {result.get('original_questions')} questions")
            print(f"Generated {len(result.get('results', []))} result files")
            
            # Test download endpoints
            print("\n3. Testing download endpoints...")
            for result_info in result.get('results', []):
                download_id = result_info['download_id']
                filename = result_info['filename']
                
                print(f"\nDownloading {filename} (ID: {download_id[:8]}...)")
                
                download_response = requests.get(f"{base_url}/api/download/{download_id}")
                
                if download_response.status_code == 200:
                    print(f"✅ Downloaded {filename} successfully")
                    print(f"Content length: {len(download_response.content)} bytes")
                    
                    # Try to parse the JSON to verify it's valid
                    try:
                        downloaded_data = download_response.json()
                        print(f"JSON structure: {len(downloaded_data)} top-level keys")
                    except:
                        print("Downloaded content is not valid JSON")
                else:
                    print(f"❌ Download failed: {download_response.status_code}")
                    print(download_response.text)
            
        else:
            print("❌ Processing failed:")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error testing API: {str(e)}")
        return False
    
    # Test error cases
    print("\n4. Testing error cases...")
    
    # Test invalid JSON
    invalid_payload = {
        "file_data": base64.b64encode(b"invalid json").decode('utf-8'),
        "filename": "invalid.json",
        "options": ["category"]
    }
    
    response = requests.post(f"{base_url}/api/process", json=invalid_payload)
    if response.status_code == 400:
        print("✅ Invalid JSON properly rejected")
    else:
        print(f"❌ Invalid JSON not properly handled: {response.status_code}")
    
    # Test missing options
    missing_options_payload = {
        "file_data": test_file_data,
        "filename": "test.json"
        # Missing options field
    }
    
    response = requests.post(f"{base_url}/api/process", json=missing_options_payload)
    if response.status_code == 400:
        print("✅ Missing options properly rejected")
    else:
        print(f"❌ Missing options not properly handled: {response.status_code}")
    
    # Test invalid download ID
    response = requests.get(f"{base_url}/api/download/invalid-id")
    if response.status_code == 404:
        print("✅ Invalid download ID properly rejected")
    else:
        print(f"❌ Invalid download ID not properly handled: {response.status_code}")
    
    print("\n✅ API testing completed!")
    return True


if __name__ == "__main__":
    print("Flask API Test Suite")
    print("=" * 50)
    print("Make sure the Flask server is running with: python app.py")
    print("=" * 50)
    
    # Wait a moment for user to start server if needed
    input("Press Enter when the Flask server is running...")
    
    test_api_endpoints()