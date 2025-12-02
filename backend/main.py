import os
import time
import shutil
import json
from typing import List, Optional
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agents import OrchestratorAgent
from services import DocumentService

# Initialize FastAPI app
app = FastAPI(
    title="Electrolyte Design Multi-Agent System",
    description="AI-powered system for electrolyte formulation design and experiment planning",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
document_service = DocumentService()
orchestrator = OrchestratorAgent(vector_store=document_service.get_vector_store())

# Track pending (uploaded but not indexed) documents
pending_documents: List[dict] = []
indexed_documents: List[dict] = []

# Request/Response models
class QueryRequest(BaseModel):
    query: str
    user_materials: Optional[str] = None  # User-specified materials/formulation
    
class QueryResponse(BaseModel):
    query: str
    summary: str
    experiment_plans: List[dict]
    agent_responses: List[dict]
    processing_time: float

class DocumentStatus(BaseModel):
    total_documents: int
    status: str

class HealthResponse(BaseModel):
    status: str
    agents: dict
    documents_indexed: int

class IndexRequest(BaseModel):
    filenames: Optional[List[str]] = None  # If None, index all pending documents

class IndexResponse(BaseModel):
    status: str
    indexed_count: int
    indexed_files: List[dict]
    total_chunks: int
    message: str

class PendingDocumentsResponse(BaseModel):
    pending: List[dict]
    indexed: List[dict]
    pending_count: int
    indexed_count: int

# Ensure upload directory exists
UPLOAD_DIR = Path("./data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Metadata file to persist document status
METADATA_FILE = UPLOAD_DIR / ".document_metadata.json"

def load_document_metadata():
    """Load document metadata from file."""
    global pending_documents, indexed_documents
    if METADATA_FILE.exists():
        try:
            with open(METADATA_FILE, 'r') as f:
                data = json.load(f)
                pending_documents = data.get('pending', [])
                indexed_documents = data.get('indexed', [])
        except Exception:
            pending_documents = []
            indexed_documents = []

def save_document_metadata():
    """Save document metadata to file."""
    with open(METADATA_FILE, 'w') as f:
        json.dump({
            'pending': pending_documents,
            'indexed': indexed_documents
        }, f, indent=2)

# Load metadata on startup
load_document_metadata()

@app.get("/", response_model=dict)
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Electrolyte Design Multi-Agent System",
        "version": "1.0.0",
        "endpoints": {
            "query": "/api/query",
            "upload": "/api/upload",
            "documents": "/api/documents",
            "health": "/api/health"
        }
    }

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Check system health and agent status."""
    agent_status = await orchestrator.get_agent_status()
    return {
        "status": "healthy",
        "agents": agent_status,
        "documents_indexed": document_service.get_document_count()
    }

@app.post("/api/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    Process a user query through the multi-agent system.
    Returns analysis and three experiment plans.
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    try:
        # Update orchestrator with latest vector store
        orchestrator.update_vector_store(document_service.get_vector_store())
        
        # Process the query with user-specified materials if provided
        result = await orchestrator.process({
            "query": request.query,
            "user_materials_input": request.user_materials or ""
        })
        
        return QueryResponse(
            query=result["query"],
            summary=result["summary"],
            experiment_plans=result["experiment_plans"],
            agent_responses=result["agent_responses"],
            processing_time=result["processing_time"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@app.post("/api/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a document (PDF, DOCX, or TXT) - saves file but does NOT index it.
    Documents are added to the pending queue for later indexing.
    """
    global pending_documents
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    # Validate file type
    allowed_extensions = {'.pdf', '.txt', '.doc', '.docx'}
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"File type {file_ext} not supported. Allowed: {', '.join(allowed_extensions)}"
        )
    
    try:
        # Save file to upload directory
        file_path = UPLOAD_DIR / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # Check if already in pending or indexed
        existing_pending = [d for d in pending_documents if d['filename'] == file.filename]
        existing_indexed = [d for d in indexed_documents if d['filename'] == file.filename]
        
        if existing_pending:
            return {
                "filename": file.filename,
                "status": "already_pending",
                "message": f"File '{file.filename}' is already in the pending queue",
                "file_type": file_ext,
                "file_size": file_size
            }
        
        if existing_indexed:
            return {
                "filename": file.filename,
                "status": "already_indexed",
                "message": f"File '{file.filename}' has already been indexed",
                "file_type": file_ext,
                "file_size": file_size
            }
        
        # Add to pending documents queue
        doc_info = {
            "filename": file.filename,
            "file_path": str(file_path),
            "file_type": file_ext,
            "file_size": file_size,
            "uploaded_at": datetime.now().isoformat(),
            "status": "pending"
        }
        pending_documents.append(doc_info)
        save_document_metadata()
        
        return {
            "filename": file.filename,
            "status": "uploaded",
            "message": f"File '{file.filename}' uploaded successfully. Click 'Index' to add to the knowledge base.",
            "file_type": file_ext,
            "file_size": file_size,
            "pending_count": len(pending_documents)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

@app.post("/api/index", response_model=IndexResponse)
async def index_documents(request: IndexRequest = None):
    """
    Index pending documents into the vector store.
    If filenames are specified, only index those files.
    Otherwise, index all pending documents.
    """
    global pending_documents, indexed_documents
    
    if not pending_documents:
        return IndexResponse(
            status="no_pending",
            indexed_count=0,
            indexed_files=[],
            total_chunks=0,
            message="No pending documents to index"
        )
    
    # Determine which files to index
    if request and request.filenames:
        files_to_index = [d for d in pending_documents if d['filename'] in request.filenames]
    else:
        files_to_index = pending_documents.copy()
    
    if not files_to_index:
        return IndexResponse(
            status="not_found",
            indexed_count=0,
            indexed_files=[],
            total_chunks=0,
            message="Specified files not found in pending queue"
        )
    
    indexed_files = []
    total_chunks = 0
    errors = []
    
    for doc in files_to_index:
        try:
            file_path = doc['file_path']
            filename = doc['filename']
            file_ext = doc['file_type']
            
            # Process based on file type
            if file_ext == '.pdf':
                result = await document_service.process_pdf(file_path, filename)
            elif file_ext in ['.doc', '.docx']:
                result = await document_service.process_docx(file_path, filename)
            else:
                result = await document_service.process_text(file_path, filename)
            
            chunks_created = result.get('chunks_created', 0)
            total_chunks += chunks_created
            
            # Update document info
            doc_indexed = {
                **doc,
                "status": "indexed",
                "indexed_at": datetime.now().isoformat(),
                "chunks_created": chunks_created
            }
            indexed_files.append(doc_indexed)
            indexed_documents.append(doc_indexed)
            
            # Remove from pending
            pending_documents = [d for d in pending_documents if d['filename'] != filename]
            
        except Exception as e:
            errors.append(f"{doc['filename']}: {str(e)}")
    
    # Save metadata
    save_document_metadata()
    
    # Update orchestrator with new vector store
    orchestrator.update_vector_store(document_service.get_vector_store())
    
    status = "success" if not errors else "partial_success"
    message = f"Successfully indexed {len(indexed_files)} document(s) with {total_chunks} chunks"
    if errors:
        message += f". Errors: {'; '.join(errors)}"
    
    return IndexResponse(
        status=status,
        indexed_count=len(indexed_files),
        indexed_files=indexed_files,
        total_chunks=total_chunks,
        message=message
    )

@app.get("/api/documents/pending", response_model=PendingDocumentsResponse)
async def get_pending_documents():
    """Get list of pending and indexed documents."""
    return PendingDocumentsResponse(
        pending=pending_documents,
        indexed=indexed_documents,
        pending_count=len(pending_documents),
        indexed_count=len(indexed_documents)
    )

@app.delete("/api/documents/pending/{filename}")
async def remove_pending_document(filename: str):
    """Remove a document from the pending queue (does not delete the file)."""
    global pending_documents
    
    original_count = len(pending_documents)
    pending_documents = [d for d in pending_documents if d['filename'] != filename]
    
    if len(pending_documents) < original_count:
        save_document_metadata()
        return {"status": "success", "message": f"Removed '{filename}' from pending queue"}
    else:
        raise HTTPException(status_code=404, detail=f"File '{filename}' not found in pending queue")

@app.get("/api/documents")
async def get_documents():
    """Get comprehensive information about all documents."""
    return {
        "total_indexed": document_service.get_document_count(),
        "total_pending": len(pending_documents),
        "indexed_documents": indexed_documents,
        "pending_documents": pending_documents,
        "status": "ready"
    }

@app.delete("/api/documents")
async def clear_documents():
    """Clear all indexed documents and reset pending queue."""
    global pending_documents, indexed_documents
    
    try:
        document_service.clear_store()
        orchestrator.update_vector_store(document_service.get_vector_store())
        
        # Clear tracking lists
        pending_documents = []
        indexed_documents = []
        save_document_metadata()
        
        return {"status": "success", "message": "All documents cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing documents: {str(e)}")

@app.post("/api/search")
async def search_documents(query: QueryRequest):
    """Search indexed documents."""
    if not query.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    results = document_service.search(query.query)
    return {
        "query": query.query,
        "results": results,
        "count": len(results)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

