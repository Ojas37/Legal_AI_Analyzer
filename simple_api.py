from fastapi import FastAPI, HTTPException, Request, File, UploadFile, Form, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from pdf_processor import PDFProcessor
import uvicorn
import logging
import io
import pickle
import os
from functools import lru_cache
from typing import Optional

app = FastAPI(title="Legal Document AI API")

# Mount static files
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/static/app.js")
async def get_js():
    return FileResponse(
        Path("static/app.js"),
        media_type="application/javascript"
    )

# Setup templates
templates = Jinja2Templates(directory="templates")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(level=logging.INFO)

class DocumentRequest(BaseModel):
    text: str

# Load the pickled model
def load_pickled_model():
    model_path = 'legal_processor.pkl'
    if not os.path.exists(model_path):
        raise FileNotFoundError(
            "Model file not found. Please run save_model.py first to create the model file."
        )
    
    print("📥 Loading model from disk...")
    with open(model_path, 'rb') as f:
        processor = pickle.load(f)
    print("✅ Model loaded successfully!")
    return processor

# Cache the processor instance
@lru_cache(maxsize=1)
def get_processor():
    return load_pickled_model()

# Initialize processor
print("🚀 Initializing Legal Document AI API...")
try:
    processor = get_processor()
    print("✅ API Ready!")
except Exception as e:
    print(f"❌ Error loading model: {str(e)}")
    raise

# Processing status storage
processing_status = {}

@app.post("/analyze")
async def analyze_document(request: DocumentRequest):
    try:
        logging.info("Received text document for analysis")
        if not request.text:
            raise HTTPException(status_code=400, detail="No document content provided")
        
        results = processor.analyze_document(request.text)
        logging.info("Document analysis completed successfully")
        return JSONResponse(content=results)
    except Exception as e:
        logging.error(f"Error during document analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_pdf_background(task_id: str, pdf_content: bytes):
    try:
        # Update status
        processing_status[task_id] = {"status": "extracting_text", "progress": 10}
        
        # Extract text from PDF
        pdf_file = io.BytesIO(pdf_content)
        pdf_processor = PDFProcessor()
        text = pdf_processor.extract_text_from_pdf(pdf_file)
        
        if not text.strip():
            processing_status[task_id] = {"status": "error", "error": "Could not extract text from PDF"}
            return
            
        # Update status
        processing_status[task_id] = {"status": "analyzing", "progress": 50}
        
        # Process the extracted text
        results = processor.analyze_document(text)
        
        # Store results
        processing_status[task_id] = {
            "status": "completed",
            "progress": 100,
            "results": results
        }
        
    except Exception as e:
        logging.error(f"Error in background processing: {str(e)}")
        processing_status[task_id] = {"status": "error", "error": str(e)}

@app.post("/analyze-pdf")
async def analyze_pdf_document(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    try:
        logging.info(f"Received PDF file: {file.filename}")
        
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="File must be a PDF")
            
        # Generate task ID
        import uuid
        task_id = str(uuid.uuid4())
        
        # Initialize status
        processing_status[task_id] = {"status": "starting", "progress": 0}
        
        # Read the PDF file content
        pdf_content = await file.read()
        
        # Start background processing
        background_tasks.add_task(process_pdf_background, task_id, pdf_content)
        
        return JSONResponse(content={"task_id": task_id, "status": "processing"})
        
    except Exception as e:
        logging.error(f"Error processing PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status/{task_id}")
async def get_processing_status(task_id: str):
    if task_id not in processing_status:
        raise HTTPException(status_code=404, detail="Task not found")
        
    status = processing_status[task_id]
    
    # Clean up completed or error tasks after sending status
    if status["status"] in ["completed", "error"]:
        # Keep the status for a while before cleaning up
        # You might want to implement a proper cleanup mechanism
        pass
        
    return JSONResponse(content=status)

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
