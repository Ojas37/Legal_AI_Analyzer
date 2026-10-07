import torch
import spacy
import re
from transformers import (
    AutoTokenizer, AutoModel,
    T5Tokenizer, T5ForConditionalGeneration,
    pipeline
)
from typing import List, Dict, Any
import pandas as pd
from datetime import datetime
import logging
import warnings
warnings.filterwarnings('ignore')

class LegalDocumentProcessor:
    """Advanced AI system for legal document analysis and summarization"""
    
    def __init__(self):
        self.setup_logging()
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f"🔧 Using device: {self.device}")
        
        self.load_models()
        self.setup_nlp_pipeline()
        
    def setup_logging(self):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def load_models(self):
        """Load all required models"""
        print("📥 Loading Legal-BERT model...")
        try:
            self.legal_tokenizer = AutoTokenizer.from_pretrained(
                'nlpaueb/legal-bert-base-uncased'
            )
            self.legal_model = AutoModel.from_pretrained(
                'nlpaueb/legal-bert-base-uncased'
            )
            print("✅ Legal-BERT loaded successfully!")
        except Exception as e:
            print(f"⚠️ Legal-BERT failed, using BERT-base: {e}")
            self.legal_tokenizer = AutoTokenizer.from_pretrained('bert-base-uncased')
            self.legal_model = AutoModel.from_pretrained('bert-base-uncased')
        
        print("📥 Loading T5 summarization model...")
        self.t5_tokenizer = T5Tokenizer.from_pretrained('t5-small')
        self.t5_model = T5ForConditionalGeneration.from_pretrained('t5-small')
        
        print("📥 Loading QA pipeline...")
        self.qa_pipeline = pipeline(
            "question-answering",
            model="distilbert-base-cased-distilled-squad"
        )
        
        print("✅ All models loaded successfully!")
    
    def setup_nlp_pipeline(self):
        """Setup SpaCy NLP pipeline"""
        print("📥 Loading SpaCy model...")
        try:
            self.nlp = spacy.load("en_core_web_sm")
            print("✅ SpaCy loaded successfully!")
        except OSError:
            print("❌ SpaCy model not found. Run: python -m spacy download en_core_web_sm")
            raise
    
    def preprocess_text(self, text: str) -> str:
        """Preprocess legal text"""
        text = re.sub(r'\s+', ' ', text.strip())
        text = re.sub(r'\n+', ' ', text)
        text = re.sub(r'\t+', ' ', text)
        return text
    
    def classify_document_type(self, text: str) -> Dict[str, Any]:
        """Classify the type of legal document"""
        doc_indicators = {
            'contract': ['agreement', 'party', 'whereas', 'covenant'],
            'license': ['license', 'licensor', 'licensee', 'grant'],
            'lease': ['lease', 'lessor', 'lessee', 'rent', 'premises'],
            'employment': ['employee', 'employer', 'employment', 'salary'],
            'nda': ['confidential', 'non-disclosure', 'proprietary']
        }
        
        text_lower = text.lower()
        scores = {}
        
        for doc_type, indicators in doc_indicators.items():
            score = sum(1 for indicator in indicators if indicator in text_lower)
            scores[doc_type] = score / len(indicators)
        
        predicted_type = max(scores, key=scores.get)
        confidence = scores[predicted_type]
        
        return {
            'document_type': predicted_type,
            'confidence': confidence,
            'all_scores': scores
        }
    
    def clean_name(self, name: str) -> str:
        cleaned = re.sub(r'^(?:Name|Title|Date|Signature|By|For|The|Mr\.?|Ms\.?|Mrs\.?|Dr\.?)\s*[:\-]?\s*', '', name, flags=re.IGNORECASE)
        cleaned = re.sub(r'\s+(?:Title|Date|Signature|Name)\s*:?.*$', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'[_\(\)\[\]\{\}\"\':;,]', ' ', cleaned)
        return re.sub(r'\s+', ' ', cleaned).strip()

    def clean_org(self, org: str) -> str:
        cleaned = re.sub(r'^[“"\'\(\[\{]+|[”"\'\)\]\}]+$', '', org)
        cleaned = re.sub(r'^(?:For|The|By|To|From|This|That|Signatures?)\s+(?:the\s+)?', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\s+[\'’]s\b', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\s+s\b', '', cleaned)
        cleaned = re.sub(r'[_\(\)\[\]\{\}\"\':;]', ' ', cleaned)
        return re.sub(r'\s+', ' ', cleaned).strip()

    def is_valid_person(self, name: str) -> bool:
        if not name or len(name) < 3 or len(name) > 45:
            return False
        lower = name.lower()
        stopwords = {
            'company', 'employee', 'employer', 'party', 'parties', 'landlord', 'tenant',
            'licensor', 'licensee', 'lessor', 'lessee', 'buyer', 'seller', 'borrower',
            'lender', 'contractor', 'client', 'customer', 'witness', 'director',
            'officer', 'title', 'name', 'date', 'signature', 'signatures', 'agreement',
            'confidential information', 'terms', 'term', 'section', 'schedule', 'exhibit',
            'security', 'termination', 'jurisdiction', 'entire', 'severability',
            'governing law', 'working hours', 'compensation', 'non-solicitation',
            'intellectual property', 'data protection', 'notice', 'communication',
            'position', 'duties', 'formal', 'effective date', 'synthetic legal document',
            'human resources', 'machine learning', 'machine learning engineer',
            'senior machine learning engineer', 'director human resources', 'effective',
            'page', 'recitals', 'preamble', 'whereas', 'witnesseth', 'definitions',
            'arbitration', 'indemnification', 'waiver', 'amendment', 'counterparts',
            'disclosing party', 'receiving party', 'discloser', 'recipient', 'purpose', 'exclusions'
        }
        if lower in stopwords:
            return False
        words = lower.split()
        if len(words) < 2 or len(words) > 4:
            return False
        invalid_words = {
            'agreement', 'company', 'section', 'party', 'parties', 'learning',
            'resources', 'engineer', 'developer', 'manager', 'director',
            'analytics', 'technologies', 'solutions', 'corporation', 'limited', 'private',
            'clause', 'schedule', 'document', 'information', 'signatures', 'signature',
            'effective', 'date', 'disclosing', 'receiving', 'exclusions', 'purpose'
        }
        if any(w in invalid_words for w in words):
            return False
        if not re.match(r"^[A-Za-z\s\.\-']+$", name):
            return False
        if name.isupper() and len(words) > 1:
            return False
        return True

    def is_valid_org(self, org: str) -> bool:
        if not org or len(org) < 3 or len(org) > 80:
            return False
        lower = org.lower().strip()
        legal_role_terms = {
            'company', 'employee', 'employer', 'party', 'parties', 'landlord', 'tenant',
            'licensor', 'licensee', 'lessor', 'lessee', 'buyer', 'seller', 'borrower',
            'lender', 'contractor', 'client', 'customer', 'witness', 'director',
            'officer', 'title', 'name', 'date', 'signature', 'signatures', 'agreement',
            'confidential information', 'terms', 'term', 'section', 'schedule', 'exhibit',
            'security', 'termination', 'jurisdiction', 'entire', 'severability',
            'governing law', 'working hours', 'compensation', 'non-solicitation',
            'intellectual property', 'data protection', 'notice', 'communication',
            'position', 'duties', 'formal', 'effective date', 'synthetic legal document',
            'human resources', 'machine learning', 'human resources title',
            'signatures for the company', 'for the company',
            'nlp', 'ai', 'ml', 'pdf', 'api', 'url', 'hr', 'it', 'faq', 'nda',
            'test', 'synthetic', 'test document', 'legal nlp', 'legal nlp test document',
            'disclosing party', 'receiving party', 'discloser', 'recipient',
            'disclosing party receiving party', 'exclusions', 'exclusions confidential information',
            'purpose', 'non-disclosure agreement', 'this non-disclosure agreement',
            'employment agreement', 'rental agreement', 'lease agreement',
            'terms of service', 'privacy policy', 'remedies', 'miscellaneous', 'obligations'
        }
        if lower in legal_role_terms:
            return False
        words = lower.split()
        if len(words) == 1 and lower in {'company', 'employee', 'party', 'parties', 'security', 'formal', 'entire', 'notice', 'signatures', 'nlp', 'ai', 'ml', 'pdf', 'synthetic', 'purpose', 'exclusions', 'disclosing', 'receiving'}:
            return False
        if all(w in legal_role_terms for w in words):
            return False
        if any(bad_phrase in lower for bad_phrase in [
            'disclosing party', 'receiving party', 'non-disclosure agreement',
            'confidential information', 'exclusions', 'entire agreement',
            'employment agreement', 'rental agreement', 'lease agreement',
            'terms of service', 'privacy policy', 'suggested nlp targets'
        ]):
            return False
        if org.isupper() and len(words) > 1 and any(w in ['party', 'parties', 'exclusions', 'agreement', 'section', 'purpose', 'confidential'] for w in words):
            return False
        if lower.endswith(' title') or lower.startswith('termination') or lower.startswith('security') or lower.startswith('signatures') or lower.startswith('for '):
            return False
        return True

    def extract_legal_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract legal entities with precise filtering, regex patterns, and substring deduplication"""
        doc = self.nlp(text)
        
        persons = set()
        orgs = set()
        dates = set()
        monies = set()
        gpes = set()

        # 1. Structural pattern extraction for Persons in signature blocks & recitals
        name_matches = re.findall(r'Name\s*:\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)', text)
        for name in name_matches:
            cleaned = self.clean_name(name)
            if self.is_valid_person(cleaned):
                persons.add(cleaned)

        preamble_persons = re.findall(
            r'(?:and|between)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s*\(\s*(?:the\s*)?[\"“]?(?:Employee|Consultant|Executive|Advisor|Contractor|Tenant|Landlord)[\"”]?',
            text
        )
        for name in preamble_persons:
            cleaned = self.clean_name(name)
            if self.is_valid_person(cleaned):
                persons.add(cleaned)

        # Company preamble patterns (e.g. VertexAI Solutions Private Limited)
        preamble_orgs = re.findall(
            r'(?:and|between)\s+([A-Z][A-Za-z0-9\s,\.\-&]+?(?:Private Limited|Pvt\.?\s*Ltd\.?|Limited|Ltd\.?|LLC|Inc\.?|Corp\.?|Corporation|LLP))\s*[,(]',
            text
        )
        for org in preamble_orgs:
            cleaned = self.clean_org(org)
            if self.is_valid_org(cleaned):
                orgs.add(cleaned)

        # 2. SpaCy NER with filtration
        for ent in doc.ents:
            raw_text = ent.text.strip()
            
            if ent.label_ == 'PERSON':
                cleaned = self.clean_name(raw_text)
                if self.is_valid_person(cleaned):
                    persons.add(cleaned)
            elif ent.label_ == 'ORG':
                cleaned = self.clean_org(raw_text)
                if self.is_valid_org(cleaned) and not self.is_valid_person(cleaned):
                    orgs.add(cleaned)
            elif ent.label_ in ('GPE', 'LOC', 'FAC'):
                cleaned = self.clean_org(raw_text)
                invalid_gpe = {'effective', 'effective date', 'section', 'agreement', 'date', 'page', 'employee', 'company', 'party', 'disclosing party', 'receiving party'}
                if len(cleaned) > 2 and cleaned.lower() not in invalid_gpe and not self.is_valid_person(cleaned) and not self.is_valid_org(cleaned):
                    gpes.add(cleaned)
            elif ent.label_ == 'DATE':
                date_clean = re.sub(r'[\(\)\[\]\"]', '', raw_text).strip()
                date_clean = re.sub(r'\s+Date$', '', date_clean, flags=re.IGNORECASE)
                if (any(m in date_clean.lower() for m in ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']) or re.search(r'\b20\d{2}\b', date_clean)):
                    if len(date_clean) > 3:
                        dates.add(date_clean)
            elif ent.label_ == 'MONEY':
                cleaned_money = raw_text.replace('■', '₹').strip()
                if cleaned_money:
                    monies.add(cleaned_money)

        # 3. Currency and monetary patterns ($, ₹, Rs, INR, €, £, Lakh, Crore)
        currency_patterns = [
            r'(?:[\$€£₹■]|Rs\.?|INR)\s*[\d,]+(?:\.\d{2})?(?:\s*(?:Lakh|Crore|Million|Billion))?',
            r'\b[\d,]+(?:\.\d{2})?\s*(?:Indian Rupees|Rupees|USD|EUR|GBP|Lakh|Crore)\b'
        ]
        for pattern in currency_patterns:
            matches = re.findall(pattern, text, flags=re.IGNORECASE)
            for m in matches:
                cleaned_m = m.replace('■', '₹').strip()
                if cleaned_m:
                    monies.add(cleaned_m)

        # 4. Remove partial/subsumed substring organizations
        filtered_orgs = []
        for o in orgs:
            if not any(o != other and o in other for other in orgs):
                filtered_orgs.append(o)

        return {
            'PERSON': sorted(list(persons)),
            'ORG': sorted(filtered_orgs),
            'DATE': sorted(list(dates)),
            'MONEY': sorted(list(monies)),
            'GPE': sorted(list(gpes))
        }

    def find_focused_context(self, question: str, text: str) -> str:
        """Find the most relevant section/paragraphs for a specific clause question to accelerate QA"""
        paragraphs = [p.strip() for p in text.split('\n\n') if len(p.strip()) > 20]
        if not paragraphs or len(paragraphs) <= 2:
            return text[:2500]
        
        q_lower = question.lower()
        if 'effective date' in q_lower or 'entered into' in q_lower:
            keywords = ['effective date', 'entered into', 'agreement', 'preamble', 'dated']
        elif 'salary' in q_lower or 'compensation' in q_lower:
            keywords = ['salary', 'compensation', 'payable', 'bonus', 'gross annual', 'installments']
        elif 'job title' in q_lower or 'position' in q_lower:
            keywords = ['position', 'duties', 'employs', 'title', 'engineer', 'role']
        elif 'duration' in q_lower or 'term' in q_lower or 'confidentiality' in q_lower:
            keywords = ['term', 'duration', 'confidentiality', 'continue until', 'years', 'survival']
        elif 'disclosing' in q_lower or 'receiving' in q_lower:
            keywords = ['disclosing party', 'receiving party', 'preamble', 'entered into', 'between']
        elif 'purpose' in q_lower:
            keywords = ['purpose', 'evaluating', 'business', 'transaction', 'disclosed solely']
        elif 'terminate' in q_lower or 'notice' in q_lower:
            keywords = ['termination', 'written notice', 'terminate without cause', 'notice period']
        elif 'law' in q_lower or 'governing' in q_lower:
            keywords = ['governing law', 'laws of', 'jurisdiction']
        elif 'jurisdiction' in q_lower or 'courts' in q_lower:
            keywords = ['jurisdiction', 'courts located', 'governing law', 'disputes']
        elif 'rent' in q_lower:
            keywords = ['rent', 'monthly rent', 'per month', 'payment']
        elif 'security deposit' in q_lower:
            keywords = ['security deposit', 'deposit']
        else:
            keywords = [w for w in q_lower.split() if len(w) > 3]

        scored = []
        for p in paragraphs:
            p_lower = p.lower()
            score = sum(3 if kw in p_lower else 0 for kw in keywords)
            scored.append((score, p))
            
        scored.sort(key=lambda x: x[0], reverse=True)
        best_pars = [p for score, p in scored if score > 0][:2]
        if best_pars:
            return "\n\n".join(best_pars)
        return text[:2500]

    def extract_key_clauses(self, text: str, document_type: str = None) -> Dict[str, str]:
        """Extract key clauses using fast targeted Question-Answering"""
        
        if document_type == 'contract':
            clause_queries = [
                ("Effective Date", "What is the date the agreement is entered into as of?"),
                ("Parties Involved", "Who are the parties involved in the agreement?"),
                ("Payment Terms", "What are the payment terms?"),
                ("Governing Law", "What law governs this agreement?"),
                ("Jurisdiction", "Which courts have jurisdiction?"),
                ("Termination Notice", "How many days written notice is required to terminate?")
            ]
        elif document_type == 'nda':
            clause_queries = [
                ("Disclosing Party", "Who is the disclosing party?"),
                ("Receiving Party", "Who is the receiving party?"),
                ("Effective Date", "What is the date the agreement is entered into as of?"),
                ("Confidentiality Term", "What is the duration or term of the confidentiality obligations?"),
                ("Purpose of Disclosure", "What is the purpose of the disclosure or agreement?"),
                ("Governing Law", "What law governs this agreement?"),
                ("Jurisdiction", "Which courts have jurisdiction?")
            ]
        elif document_type == 'employment':
            clause_queries = [
                ("Salary", "What is the salary or compensation?"),
                ("Job Title", "What is the job title or position?"),
                ("Effective Date", "What is the date the agreement is entered into as of?"),
                ("Term of Employment", "What is the duration of the initial employment term until what date?"),
                ("Termination Notice", "How many days written notice is required to terminate?"),
                ("Governing Law", "What law governs this agreement?"),
                ("Jurisdiction", "Which courts have jurisdiction?")
            ]
        elif document_type == 'lease':
            clause_queries = [
                ("Rent Amount", "What is the rent amount?"),
                ("Lease Term", "What is the lease term?"),
                ("Tenant", "Who is the tenant?"),
                ("Landlord", "Who is the landlord?"),
                ("Security Deposit", "What is the security deposit?")
            ]
        else:
            clause_queries = [
                ("Main Terms", "What are the main terms?"),
                ("Parties Involved", "Who are the parties involved in the agreement?"),
                ("Effective Date", "What is the date the agreement is entered into as of?"),
                ("Governing Law", "What law governs this agreement?")
            ]
        
        extracted_clauses = {}
        
        with torch.inference_mode():
            for label, question in clause_queries:
                try:
                    focused_context = self.find_focused_context(question, text)
                    result = self.qa_pipeline(question=question, context=focused_context)
                    if result['score'] > 0.05:
                        answer_text = result['answer'].replace('■', '₹').strip()
                        extracted_clauses[label] = {
                            'text': answer_text,
                            'confidence': result['score']
                        }
                except Exception as e:
                    self.logger.warning(f"Error extracting clause: {e}")
        
        return extracted_clauses
    
    def generate_summary(self, text: str, max_length: int = 120) -> str:
        """Generate fast abstractive summary using T5 with inference mode"""
        input_text = f"summarize: {text[:2000]}"
        inputs = self.t5_tokenizer.encode(
            input_text,
            return_tensors="pt",
            max_length=512,
            truncation=True
        )
        
        with torch.inference_mode():
            summary_ids = self.t5_model.generate(
                inputs,
                max_length=max_length,
                min_length=25,
                num_beams=1,
                do_sample=False
            )
        
        summary = self.t5_tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        return summary
    
    def analyze_document(self, text: str) -> Dict[str, Any]:
        """Complete document analysis pipeline optimized for low latency"""
        print("🔍 Starting document analysis...")
        
        with torch.inference_mode():
            # Preprocess
            processed_text = self.preprocess_text(text)
            
            # Classification
            doc_classification = self.classify_document_type(processed_text)
            print(f"📋 Document type: {doc_classification['document_type']}")
            
            # Entity extraction
            entities = self.extract_legal_entities(processed_text)
            print("🏷️ Entities extracted")
            
            # Clause extraction
            clauses = self.extract_key_clauses(
                processed_text, 
                doc_classification['document_type']
            )
            print("📄 Key clauses extracted")
            
            # Summary generation
            summary = self.generate_summary(processed_text)
            print("📝 Summary generated")
            
            results = {
                'document_info': {
                    'type': doc_classification['document_type'],
                    'confidence': doc_classification['confidence'],
                    'length': len(text.split()),
                    'processed_at': datetime.now().isoformat()
                },
                'entities': entities,
                'key_clauses': clauses,
                'summary': summary,
                'classification_scores': doc_classification['all_scores']
            }
            
            print("✅ Document analysis completed!")
            return results

# Test function
if __name__ == "__main__":
    sample_contract = """
    EMPLOYMENT AGREEMENT
    
    This Employment Agreement is entered into effective as of January 1, 2024,
    between Tech Innovations Inc., a Delaware corporation ("Company"), and John Smith ("Employee").
    
    1. EMPLOYMENT TERM: Employee's employment shall commence on January 1, 2024.
    
    2. COMPENSATION: Company shall pay Employee an annual salary of $120,000.
    
    3. TERMINATION: Either party may terminate this Agreement with thirty (30) days written notice.
    
    4. GOVERNING LAW: This Agreement shall be governed by the laws of Delaware.
    """
    
    print("🚀 Testing Legal Document Processor...")
    processor = LegalDocumentProcessor()
    results = processor.analyze_document(sample_contract)
    
    print("\n" + "="*60)
    print("ANALYSIS RESULTS")
    print("="*60)
    print(f"Document Type: {results['document_info']['type']}")
    print(f"Confidence: {results['document_info']['confidence']:.2f}")
    print(f"Summary: {results['summary']}")
