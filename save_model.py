import pickle
import sys
import os
import traceback
from legal_document_processor import LegalDocumentProcessor

def save_model():
    try:
        print("🔧 Initializing Legal Document Processor...")
        processor = LegalDocumentProcessor()
        
        print("💾 Saving model to disk...")
        output_path = 'legal_processor.pkl'
        with open(output_path, 'wb') as f:
            pickle.dump(processor, f)
        
        print(f"✅ Model saved successfully to {os.path.abspath(output_path)}!")
        return True
        
    except ModuleNotFoundError as e:
        print(f"❌ Error: Missing required module - {e}")
        print("Please ensure all required packages are installed:")
        print("pip install torch transformers spacy pandas python-dotenv")
        print("python -m spacy download en_core_web_sm")
        return False
        
    except Exception as e:
        print(f"❌ Error while saving model: {str(e)}")
        print("\nDetailed error information:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = save_model()
    sys.exit(0 if success else 1)