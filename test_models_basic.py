# test_models_basic.py
"""
Basic test to check if models.py imports correctly and has no syntax errors
"""

def test_models_import():
    """Test if models can be imported without errors"""
    try:
        print("🧪 Testing models import...")
        from models import (
            Base, User, Document, DocumentAnalysis, 
            ExtractedEntity, ExtractedClause, RiskAssessment,
            DocumentStatus, DocumentType, APIKey, SystemLog
        )
        print("✅ All models imported successfully!")
        return True
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return False

def test_enum_values():
    """Test if enum values are accessible"""
    try:
        print("\n🧪 Testing enum values...")
        from models import DocumentStatus, DocumentType
        
        print(f"   DocumentStatus values: {[status.value for status in DocumentStatus]}")
        print(f"   DocumentType values: {[doc_type.value for doc_type in DocumentType]}")
        print("✅ Enum values accessible!")
        return True
    except Exception as e:
        print(f"❌ Enum Error: {e}")
        return False

def test_model_creation():
    """Test if models can be instantiated"""
    try:
        print("\n🧪 Testing model creation...")
        from models import User, Document, DocumentStatus
        
        # Test User model creation (without database)
        user = User(
            email="test@example.com",
            full_name="Test User",
            hashed_password="fake_hash"
        )
        print(f"   User created: {user.email}")
        
        # Test Document model creation
        document = Document(
            user_id=1,
            original_filename="test.pdf",
            file_type="PDF",
            file_size=1024,
            file_hash="fake_hash",
            status=DocumentStatus.UPLOADED
        )
        print(f"   Document created: {document.original_filename}")
        
        print("✅ Models can be created!")
        return True
    except Exception as e:
        print(f"❌ Model Creation Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Running Basic Models Test\n")
    
    success_count = 0
    total_tests = 3
    
    if test_models_import():
        success_count += 1
    
    if test_enum_values():
        success_count += 1
    
    if test_model_creation():
        success_count += 1
    
    print(f"\n📊 Results: {success_count}/{total_tests} tests passed")
    
    if success_count == total_tests:
        print("🎉 All basic tests passed! Your models.py is syntactically correct.")
    else:
        print("⚠️ Some tests failed. Check the errors above.")
