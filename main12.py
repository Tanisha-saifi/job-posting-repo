from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from database import SessionLocal, create_database, JobPosting
from pydantic import BaseModel
from typing import Optional

# Initialize FastAPI app
app = FastAPI()

# Initialize database
create_database()

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic model for job posting input validation
class JobPostingCreate(BaseModel):
    title: str
    description: Optional[str] = None
    company: str

# Endpoint to create a new job posting
@app.post("/job-postings")
def create_job_post(job: JobPostingCreate, db: Session = Depends(get_db)):
    db_job_post = JobPosting(title=job.title, description=job.description, company=job.company)
    db.add(db_job_post)
    db.commit()
    db.refresh(db_job_post)
    return {"message": "Job posting created successfully", "job_id": db_job_post.id}

# Endpoint to delete a job posting by ID
@app.delete("/job-postings/{job_id}")
def delete_job_post(job_id: int, db: Session = Depends(get_db)):
    db_job_post = db.query(JobPosting).filter(JobPosting.id == job_id).first()
    
    if db_job_post is None:
        raise HTTPException(status_code=404, detail="Job posting not found")
    
    db.delete(db_job_post)
    db.commit()
    return {"message": f"Job posting with ID {job_id} deleted successfully"}
