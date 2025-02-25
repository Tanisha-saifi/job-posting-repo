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

    poc = relationship("PointOfContact", back_populates="employers", foreign_keys=[poc_id])

# Point-of-Contact Table
class PointOfContact(Base):
    __tablename__ = "pocs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    phone = Column(String, unique=True)

    employers = relationship("Employer", back_populates="poc", cascade="all, delete-orphan")

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

# --------- CRUD API Endpoints --------- #
@app.post("/pocs")
def create_poc(poc: PoCBase, db: Session = Depends(get_db)):
    # Check if email already exists
    existing_poc = db.query(PointOfContact).filter(PointOfContact.email == poc.email).first()
    if existing_poc:
        raise HTTPException(status_code=400, detail="PoC with this email already exists")

    db_poc = PointOfContact(name=poc.name, email=poc.email, phone=poc.phone)
    db.add(db_poc)
    db.commit()
    db.refresh(db_poc)
    return {"message": "PoC created successfully", "poc_id": db_poc.id}

# Get all PoCs
@app.get("/pocs")
def get_pocs(db: Session = Depends(get_db)):
    return db.query(PointOfContact).all()

# Get a single PoC by ID
@app.get("/pocs/{poc_id}")
def get_poc(poc_id: int, db: Session = Depends(get_db)):
    poc = db.query(PointOfContact).filter(PointOfContact.id == poc_id).first()
    if not poc:
        raise HTTPException(status_code=404, detail="PoC not found")
    return poc

# Update a PoC
@app.put("/pocs/{poc_id}")
def update_poc(poc_id: int, poc: PoCBase, db: Session = Depends(get_db)):
    db_poc = db.query(PointOfContact).filter(PointOfContact.id == poc_id).first()
    if not db_poc:
        raise HTTPException(status_code=404, detail="PoC not found")
    
    db_poc.name = poc.name
    db_poc.email = poc.email
    db_poc.phone = poc.phone
    
    db.commit()
    db.refresh(db_poc)
    return {"message": "PoC updated successfully", "poc": db_poc}

# Delete a PoC
@app.delete("/pocs/{poc_id}")
def delete_poc(poc_id: int, db: Session = Depends(get_db)):
    db_poc = db.query(PointOfContact).filter(PointOfContact.id == poc_id).first()
    if not db_poc:
        raise HTTPException(status_code=404, detail="PoC not found")
    
    db.delete(db_poc)
    db.commit()
    return {"message": "PoC deleted successfully"}

# Create an Employer
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

# Get all Employers
@app.get("/employers")
def get_employers(db: Session = Depends(get_db)):
    return db.query(Employer).all()

# Get a single Employer by ID
@app.get("/employers/{employer_id}")
def get_employer(employer_id: int, db: Session = Depends(get_db)):
    employer = db.query(Employer).filter(Employer.id == employer_id).first()
    if not employer:
        raise HTTPException(status_code=404, detail="Employer not found")
    return employer

# Update an Employer
@app.put("/employers/{employer_id}")
def update_employer(employer_id: int, employer: EmployerBase, db: Session = Depends(get_db)):
    db_employer = db.query(Employer).filter(Employer.id == employer_id).first()
    if not db_employer:
        raise HTTPException(status_code=404, detail="Employer not found")
    
    db_employer.name = employer.name
    db_employer.industry = employer.industry
    db_employer.poc_id = employer.poc_id
    
    db.commit()
    db.refresh(db_employer)
    return {"message": "Employer updated successfully", "employer": db_employer}

# Delete an Employer
@app.delete("/employers/{employer_id}")
def delete_employer(employer_id: int, db: Session = Depends(get_db)):
    db_employer = db.query(Employer).filter(Employer.id == employer_id).first()
    if not db_employer:
        raise HTTPException(status_code=404, detail="Employer not found")
    
    db.delete(db_employer)
    db.commit()
    return {"message": "Employer deleted successfully"}