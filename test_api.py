import requests
import json

def test_api():
    url = "http://127.0.0.1:8000/analyze"
    
    sample_doc = {
        "text": """
        RENTAL AGREEMENT
        
        This Rental Agreement is between John Doe (Tenant) and Jane Smith (Landlord).
        
        Property: 123 Main Street, Apartment 4B
        Rent: $1,500 per month
        Security Deposit: $1,500
        Lease Term: 12 months starting January 1, 2024
        
        Tenant agrees to pay rent on the 1st of each month.
        Landlord is responsible for major repairs.
        """
    }
    
    try:
        response = requests.post(url, json=sample_doc)
        if response.status_code == 200:
            results = response.json()
            print("✅ API Test Successful!")
            print(f"Document Type: {results['document_info']['type']}")
            print(f"Summary: {results['summary']}")
        else:
            print(f"❌ API Error: {response.status_code}")
    except Exception as e:
        print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    test_api()
