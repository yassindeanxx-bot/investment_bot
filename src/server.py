import shutil
import uuid
import os
import uvicorn
import aiofiles
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from pydantic import BaseModel

# Import your Stateless Engine
from processor import DocumentProcessor, PipelineObserver
from data_pipeline.rag_agent import generate_answer, generate_answer_async

# --- 1. Global State (The "In-Memory Database") ---
# In production, this would be Redis or Postgres.
# Structure: { "job_id": { "status": "processing", "log": [], "progress": 0 } }
JOBS = {}

# --- 2. The Bridge (Web Observer) ---
# This class translates Pipeline events into Dictionary updates that the API can read.
class WebObserver:
    def __init__(self, job_id):
        self.job_id = job_id
    
    def on_start(self, filename):
        JOBS[self.job_id]["status"] = "processing"
        JOBS[self.job_id]["file"] = filename
        JOBS[self.job_id]["log"].append(f"Started processing {filename}")
        
    def on_progress(self, stage, count, msg):
        # Update progress so the UI bar moves
        JOBS[self.job_id]["progress"] = count
        JOBS[self.job_id]["log"].append(f"[{stage}] {msg}")
            
    def on_finish(self, filename, stats):
        JOBS[self.job_id]["status"] = "completed"
        JOBS[self.job_id]["stats"] = stats
        JOBS[self.job_id]["progress"] = 100
        JOBS[self.job_id]["log"].append("Done!")
            
    def on_error(self, error):
        JOBS[self.job_id]["status"] = "failed"
        JOBS[self.job_id]["error"] = str(error)

# --- 3. The Background Task ---
# This runs in a separate thread pool, keeping the API responsive.
def run_pipeline_task(job_id: str, file_path: str):
    observer = WebObserver(job_id)
    processor = DocumentProcessor()
    # The processor blocks THIS thread, but not the main Server thread.
    processor.run(file_path, observer)

# --- 4. The API Routes ---
app = FastAPI(title="Deep Research API")

class ChatRequest(BaseModel):
    question: str

@app.post("/ingest")
async def ingest_document(
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...)
):
    """
    Async Ingestion:
    1. Save file to disk.
    2. Register background task.
    3. Return Job ID immediately.
    """
    job_id = str(uuid.uuid4())
    
    # Initialize Job State
    JOBS[job_id] = {"status": "queued", "log": [], "progress": 0}
    
    # Save Uploaded File
    file_location = f"data_pipeline/temp_{job_id}.pdf"
    try:
        # Open the destination file asynchronously
        async with aiofiles.open(file_location, 'wb') as out_file:
            # Read 1MB chunks from the uploaded file (which is async)
            while content := await file.read(1024 * 1024): 
                await out_file.write(content)  # Write async
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File save failed: {e}")

    # Handoff to Background Worker
    background_tasks.add_task(run_pipeline_task, job_id, file_location)
    
    return {"job_id": job_id, "status": "queued"}

@app.get("/status/{job_id}")
async def get_status(job_id: str):
    """Client polls this endpoint to check progress."""
    if job_id not in JOBS:
        raise HTTPException(status_code=404, detail="Job not found")
    return JOBS[job_id]

@app.post("/chat")
async def chat(request: ChatRequest):
    """Simple wrapper for RAG Agent."""
    return {"answer": await generate_answer_async(request.question)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)