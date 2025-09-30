import spacy
import torch
from transformers import T5Tokenizer, T5ForConditionalGeneration

def download_dependencies():
    print("Downloading required models...")
    
    # Download spaCy model
    try:
        spacy.cli.download("en_core_web_sm")
        print("✅ SpaCy model downloaded successfully")
    except Exception as e:
        print(f"❌ Error downloading spaCy model: {str(e)}")
    
    # Download T5 model
    try:
        tokenizer = T5Tokenizer.from_pretrained('t5-small')
        model = T5ForConditionalGeneration.from_pretrained('t5-small')
        print("✅ T5 model downloaded successfully")
    except Exception as e:
        print(f"❌ Error downloading T5 model: {str(e)}")

if __name__ == "__main__":
    download_dependencies()