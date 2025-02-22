from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from pydantic import BaseModel
from typing import Optional

# Database Setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./database.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Employer Table
class Employer(Base):
    __tablename__ = "employers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    industry = Column(String)
    poc_id = Column(Integer, ForeignKey("pocs.id", ondelete="SET NULL"), nullable=True)

    poc = relationship("PointOfContact", back_populates="employers")

# Point-of-Contact Table
class PointOfContact(Base):
    __tablename__ = "pocs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    phone = Column(String, unique=True)

    employers = relationship("Employer", back_populates="poc")

# Create Database
def create_database():
    Base.metadata.create_all(bind=engine)

# Initialize FastAPI
app = FastAPI()

# Initialize Database
create_database()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic Models (Input Validation)
class PoCBase(BaseModel):
    name: str
    email: str
    phone: str

class EmployerBase(BaseModel):
    name: str
    industry: str
    poc_id: Optional[int] = None  # PoC is optional

# API: Create a PoC
@app.post("/pocs")
def create_poc(poc: PoCBase, db: Session = Depends(get_db)):
    db_poc = PointOfContact(name=poc.name, email=poc.email, phone=poc.phone)
    db.add(db_poc)
    db.commit()
    db.refresh(db_poc)
    return {"message": "PoC created successfully", "poc_id": db_poc.id}

# API: Create an Employer
@app.post("/employers")
def create_employer(employer: EmployerBase, db: Session = Depends(get_db)):
    # Check if the PoC exists
    if employer.poc_id:
        db_poc = db.query(PointOfContact).filter(PointOfContact.id == employer.poc_id).first()
        if not db_poc:
            raise HTTPException(status_code=400, detail="PoC not found")
    
    db_employer = Employer(name=employer.name, industry=employer.industry, poc_id=employer.poc_id)
    db.add(db_employer)
    db.commit()
    db.refresh(db_employer)
    return {"message": "Employer created successfully", "employer_id": db_employer.id}

# API: Get all PoCs
@app.get("/pocs")
def get_pocs(db: Session = Depends(get_db)):
    return db.query(PointOfContact).all()

# API: Get all Employers
@app.get("/employers")
def get_employers(db: Session = Depends(get_db)):
    return db.query(Employer).all()

