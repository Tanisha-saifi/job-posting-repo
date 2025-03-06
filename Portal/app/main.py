import os
from datetime import timedelta
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from . import models, schemas, crud, auth
from .database import SessionLocal, engine 

# Initialize FastAPI
app = FastAPI()

# Create database tables (AFTER all imports)
models.Base.metadata.create_all(bind=engine)

# Set frontend build path
frontend_build_path = r"C:\Users\Sheraj\Documents\merged folder\HaH_Main\Frontend_code\dist"

# Serve static assets
app.mount("/static", StaticFiles(directory=frontend_build_path), name="static")

# CORS Middleware for React API calls
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React/Vite frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Database Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# API Endpoints
@app.post("/companies")
def create_company(company: schemas.CompanyBase, db: Session = Depends(get_db)):
    return crud.create_company(db, company)

@app.get("/companies")
def get_companies(db: Session = Depends(get_db)):
    return crud.get_companies(db)

@app.post("/pocs")
def create_poc(poc: schemas.PoCBase, db: Session = Depends(get_db)):
    return crud.create_poc(db, poc)

@app.get("/pocs")
def get_pocs(db: Session = Depends(get_db)):
    return crud.get_pocs(db)

@app.post("/employers")
def create_employer(employer: schemas.EmployerBase, db: Session = Depends(get_db)):
    return crud.create_employer(db, employer)

@app.get("/employers")
def get_employers(db: Session = Depends(get_db)):
    return crud.get_employers(db)

@app.post("/signup/", response_model=schemas.User)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    new_user = crud.create_user(db=db, user=user)
    
    return schemas.User(
        id=new_user.id,
        username=new_user.username,
        email=new_user.email,
        role=schemas.UserRole(new_user.role.lower()),
        company=new_user.company
    )

@app.post("/login", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/jobpost/", response_model=schemas.JobPosting)
def create_job_posting(
    job: schemas.JobPostingCreate, 
    employer_id: int, 
    db: Session = Depends(get_db)
):
    return crud.create_job_posting(db, job, employer_id)

@app.get("/jobpost/employer/{employer_id}", response_model=list[schemas.JobPostingWithoutId])
def get_jobs_by_employer(employer_id: int, db: Session = Depends(get_db)):
    return crud.get_jobs_by_employer(db, employer_id)

@app.get("/")


async def serve_react():
    return FileResponse(os.path.join(frontend_build_path, "index.html"))

@app.get("/{full_path:path}")
async def catch_all(full_path: str):
    return FileResponse(os.path.join(frontend_build_path, "index.html"))
