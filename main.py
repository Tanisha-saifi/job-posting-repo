from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey ,Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from pydantic import BaseModel
from pydantic import BaseModel, EmailStr
from typing import List

from typing import Optional

# Database Setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./database.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Company Table
class Company(Base):
    __tablename__ = "companies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    industry = Column(String)
    
    # One-to-Many: A company can have multiple employers
    employers = relationship("Employer", back_populates="company")


# Association Table for Many-to-Many Relationship
employer_poc_association = Table(
    "employer_poc_association",
    Base.metadata,
    Column("employer_id", Integer, ForeignKey("employers.id"), primary_key=True),
    Column("poc_id", Integer, ForeignKey("pocs.id"), primary_key=True)
)
# Employer Table
class Employer(Base):
    __tablename__ = "employers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String ,unique=True, index=True)
    email = Column(String, unique=True, index=True)
    phone = Column(String, unique=True)
    industry = Column(String)
    company_id = Column(Integer, ForeignKey("companies.id"))  # Employer belongs to ONE company

    # relationship between employer and poc
    
    company = relationship("Company", back_populates="employers")
 # Many-to-Many Relationship with PoCs
    pocs = relationship("PointOfContact", secondary=employer_poc_association, back_populates="employers")

# Point-of-Contact Table
class PointOfContact(Base):
    __tablename__ = "pocs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    phone = Column(String, unique=True)

 # Many-to-Many Relationship with Employers
    employers = relationship("Employer", secondary=employer_poc_association, back_populates="pocs")

def create_database():
    Base.metadata.drop_all(bind=engine)  # ⚠️ Deletes all existing tables
    Base.metadata.create_all(bind=engine)  # ✅ Recreates tables


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
class CompanyBase(BaseModel):
    name: str
    industry: str



class PoCBase(BaseModel):
    name: str
    email: EmailStr
    phone: str

class EmployerBase(BaseModel):
    name: str
    email: EmailStr
    phone: str
    industry: str
    poc_ids: List[int] =[] # Accept multiple PoC IDs
    company_id: int
  

# --------- CRUD API Endpoints --------- #

# Create a company
@app.post("/companies")
def create_company(company: CompanyBase, db: Session = Depends(get_db)):
    existing_company = db.query(Company).filter(Company.name == company.name).first()
    if existing_company:
        raise HTTPException(status_code=400, detail="Company already exists")

    db_company = Company(name=company.name, industry=company.industry)
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    
    return {"message": "Company created successfully", "company_id": db_company.id}

# Get all companies
@app.get("/companies")
def get_companies(db: Session = Depends(get_db)):
    return db.query(Company).all()

# create pocs

@app.post("/pocs")
def create_poc(poc: PoCBase, db: Session = Depends(get_db)):
    #Ensure phone is stored as a string
    phone_number = str(poc.phone)
    # Check if email already exists
    existing_poc = db.query(PointOfContact).filter(PointOfContact.email == poc.email).first()
    if existing_poc:
        raise HTTPException(status_code=400, detail="PoC with this email already exists")

    db_poc = PointOfContact(name=poc.name, email=poc.email, phone=poc.phone)
    db.add(db_poc)
    db.commit()
    db.refresh(db_poc)
    return {"message": "PoC created successfully", "poc_id": db_poc.id}

# get all pocs

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

   # create employers
    
@app.post("/employers")
def create_employer(employer: EmployerBase, db: Session = Depends(get_db)):

    # Check if Employer already exists by email
    existing_employer = db.query(Employer).filter(Employer.email == employer.email).first()
    if existing_employer:
        raise HTTPException(status_code=400, detail="Employer with this email already exists")

         # Ensure company exists
    company = db.query(Company).filter(Company.id == employer.company_id).first()
    if not company:
        raise HTTPException(status_code=400, detail="Company not found")

    # Ensure PoC IDs are provided and exist
    poc_list = []
    if employer.poc_ids:
        poc_list = db.query(PointOfContact).filter(PointOfContact.id.in_(employer.poc_ids)).all()
        if len(poc_list) != len(employer.poc_ids):
            raise HTTPException(status_code=400, detail="One or more PoC IDs not found")

    # Create employer
    db_employer = Employer(name=employer.name, industry=employer.industry, pocs=poc_list , email=employer.email, phone=employer.phone, company_id=employer.company_id)

    # Link employer to multiple PoCs
    db_employer.pocs = poc_list  #  assign multiple PoCs

    db.add(db_employer)
    db.commit()
    db.refresh(db_employer)
    
    return {"message": "Employer created successfully", "employer_id": db_employer.id}

# Get all Employers
@app.get("/employers")
def get_employers(db: Session = Depends(get_db)):
    employers = db.query(Employer).all()
    return [
        {
            "id": emp.id,
            "name": emp.name,
            "email": emp.email,
            "phone": emp.phone,
            "company": {
                "id": emp.company.id,
                "name": emp.company.name,
                "industry": emp.company.industry
            } if emp.company else None,
            "pocs": [{"id": poc.id, "name": poc.name, "email": poc.email, "phone": poc.phone} for poc in emp.pocs]
        }
        for emp in employers
    ]

# Get a single Employer by ID
@app.get("/employers/{employer_id}")
def get_employer(employer_id: int, db: Session = Depends(get_db)):
    employer = db.query(Employer).filter(Employer.id == employer_id).first()
    if not employer:
        raise HTTPException(status_code=404, detail="Employer not found")

    return {
        "id": employer.id,
        "name": employer.name,
        "email": employer.email,
        "phone": employer.phone,
        "company": {
            "id": employer.company.id,
            "name": employer.company.name,
            "industry": employer.company.industry
        } if employer.company else None,
        "pocs": [{"id": poc.id, "name": poc.name, "email": poc.email, "phone": poc.phone} for poc in employer.pocs]
    }

# Update an Employer
@app.put("/employers/{employer_id}")
def update_employer(employer_id: int, employer: EmployerBase, db: Session = Depends(get_db)):
    db_employer = db.query(Employer).filter(Employer.id == employer_id).first()
    if not db_employer:
        raise HTTPException(status_code=404, detail="Employer not found")
    
    # Fetch updated PoCs
    db_pocs = db.query(PointOfContact).filter(PointOfContact.id.in_(employer.poc_ids)).all()

    # Validate PoC IDs
    if len(db_pocs) != len(employer.poc_ids):
        raise HTTPException(status_code=400, detail="One or more PoCs not found")

    # Update Employer fields
    db_employer.name = employer.name
    db_employer.industry = employer.industry
    db_employer.pocs = db_pocs  # Update PoC assignments

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