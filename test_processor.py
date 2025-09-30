from legal_document_processor import LegalDocumentProcessor

def main():
    # Sample legal document
    sample_text = """
    SOFTWARE LICENSE AGREEMENT
    
    This Software License Agreement ("Agreement") is entered into between 
    TechCorp Inc. ("Licensor") and the end user ("Licensee").
    
    1. GRANT OF LICENSE: Licensor grants Licensee a non-exclusive license to use the software.
    
    2. RESTRICTIONS: Licensee may not distribute, modify, or reverse engineer the software.
    
    3. TERM: This license is effective from January 1, 2024 to December 31, 2024.
    
    4. PAYMENT: Licensee agrees to pay $5,000 annually for this license.
    
    5. GOVERNING LAW: This Agreement shall be governed by California state law.
    """
    
    print("🚀 Initializing Legal Document AI...")
    processor = LegalDocumentProcessor()
    
    print("\n📄 Processing sample document...")
    results = processor.analyze_document(sample_text)
    
    print("\n" + "="*60)
    print("📊 LEGAL DOCUMENT ANALYSIS RESULTS")
    print("="*60)
    
    # Document Info
    doc_info = results['document_info']
    print(f"\n📋 Document Information:")
    print(f"   Type: {doc_info['type']}")
    print(f"   Confidence: {doc_info['confidence']:.2f}")
    print(f"   Length: {doc_info['length']} words")
    
    # Entities
    print(f"\n🏷️ Legal Entities Found:")
    for entity_type, entities in results['entities'].items():
        if entities:
            print(f"   {entity_type}: {', '.join(entities[:3])}")
    
    # Key Clauses
    print(f"\n📄 Key Clauses Extracted:")
    for clause_name, clause_info in results['key_clauses'].items():
        if isinstance(clause_info, dict):
            print(f"   {clause_name}: {clause_info['text']}")
        else:
            print(f"   {clause_name}: {clause_info}")
    
    # Summary
    print(f"\n📝 Document Summary:")
    print(f"   {results['summary']}")
    
    # Classification Scores
    print(f"\n🎯 Classification Scores:")
    for doc_type, score in results['classification_scores'].items():
        print(f"   {doc_type}: {score:.2f}")

if __name__ == "__main__":
    main()
