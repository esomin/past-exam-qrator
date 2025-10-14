"""
Simple Flask app test
"""

from app import app
import json
import base64

def test_flask_app():
    """Test Flask app using test client"""
    
    # Create test client
    with app.test_client() as client:
        print("Testing Flask app with test client...")
        
        # Test health endpoint
        print("\n1. Testing health endpoint...")
        response = client.get('/api/health')
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Health check passed")
            print("Response:", response.get_json())
        else:
            print("❌ Health check failed")
            print("Response:", response.get_data(as_text=True))
        
        # Test process endpoint
        print("\n2. Testing process endpoint...")
        
        # Create test data
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
                    }
                ]
            }
        ]
        
        json_str = json.dumps(test_data, ensure_ascii=False)
        file_data = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
        
        payload = {
            "file_data": file_data,
            "filename": "test.json",
            "options": ["institution", "year"]
        }
        
        response = client.post('/api/process', 
                             json=payload,
                             content_type='application/json')
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.get_json()
            print("✅ Processing successful")
            print(f"Results: {len(result.get('results', []))} files generated")
            
            # Test download
            if result.get('results'):
                download_id = result['results'][0]['download_id']
                print(f"\n3. Testing download endpoint...")
                
                download_response = client.get(f'/api/download/{download_id}')
                print(f"Download status: {download_response.status_code}")
                
                if download_response.status_code == 200:
                    print("✅ Download successful")
                    print(f"Content length: {len(download_response.get_data())} bytes")
                else:
                    print("❌ Download failed")
                    print("Response:", download_response.get_data(as_text=True))
        else:
            print("❌ Processing failed")
            print("Response:", response.get_data(as_text=True))
        
        # Test error cases
        print("\n4. Testing error cases...")
        
        # Missing field
        invalid_payload = {"filename": "test.json"}
        response = client.post('/api/process', json=invalid_payload)
        if response.status_code == 400:
            print("✅ Missing field properly rejected")
        else:
            print(f"❌ Missing field not handled: {response.status_code}")
        
        # Invalid download ID
        response = client.get('/api/download/invalid-id')
        if response.status_code == 404:
            print("✅ Invalid download ID properly rejected")
        else:
            print(f"❌ Invalid download ID not handled: {response.status_code}")

if __name__ == "__main__":
    test_flask_app()