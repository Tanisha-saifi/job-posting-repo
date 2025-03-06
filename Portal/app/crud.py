import re
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from passlib.context import CryptContext
from . import models, schemas, auth
from .models import UserRole

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Regex Patterns
EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
USERNAME_REGEX = r"^[a-zA-Z0-9_]{3,20}$"
PASSWORD_REGEX = r"^(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"

# Validation Functions
def validate_user_input(user: schemas.UserCreate):
    if not re.match(EMAIL_REGEX, user.email):
        raise HTTPException(status_code=400, detail="Invalid email format.")
    if not re.match(USERNAME_REGEX, user.username):
        raise HTTPException(status_code=400, detail="Username must be 3-20 characters and can only contain letters, numbers, and underscores.")
    if not re.match(PASSWORD_REGEX, user.password):
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters long, contain 1 uppercase letter, 1 number, and 1 special character.")

# Password Hashing & Verification
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

# User Operations
def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, user: schemas.UserCreate):
    if user.role in [UserRole.EMPLOYER, UserRole.POINT_OF_CONTACT] and not user.company:
        raise ValueError("Employers and Points of Contact must have a company.")
    if user.role == UserRole.EMPLOYEE and user.company:
        raise ValueError("Employees should not have a company.")

    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        role=user.role,
        company=user.company if user.role in [UserRole.EMPLOYER, UserRole.POINT_OF_CONTACT] else None
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Job Posting Operations
def get_jobs_by_employer(db: Session, employer_id: int):
    return db.query(models.JobPosting).filter(models.JobPosting.employer_id == employer_id).all()

def create_job_posting(db: Session, job: schemas.JobPostingCreate, employer_id: int):
    employer = db.query(models.User).filter(models.User.id == employer_id).first()
    if not employer:
        raise HTTPException(status_code=404, detail="Employer not found.")
    if employer.role != UserRole.EMPLOYER:
        raise HTTPException(status_code=403, detail="Only employers can create job postings.")
    
    existing_job = db.query(models.JobPosting).filter(
        models.JobPosting.employer_id == employer_id,
        models.JobPosting.title == job.title
    ).first()
    if existing_job:
        raise HTTPException(status_code=400, detail="You have already posted this job.")

    db_job = models.JobPosting(**job.model_dump(), employer_id=employer_id)
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job

# Company Operations
def create_company(db: Session, company: schemas.CompanyBase):
    existing_company = db.query(models.Company).filter(models.Company.name == company.name).first()
    if existing_company:
        raise HTTPException(status_code=400, detail="Company already exists")

    db_company = models.Company(**company.model_dump())
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    return db_company

def get_companies(db: Session):
    return db.query(models.Company).all()

# Point-of-Contact Operations
def create_poc(db: Session, poc: schemas.PoCBase):
    existing_poc = db.query(models.PointOfContact).filter(models.PointOfContact.email == poc.email).first()
    if existing_poc:
        raise HTTPException(status_code=400, detail="PoC with this email already exists")

    db_poc = models.PointOfContact(name=poc.name, email=poc.email, phone=poc.phone)
    db.add(db_poc)
    db.commit()
    db.refresh(db_poc)
    return db_poc

def get_pocs(db: Session):
    return db.query(models.PointOfContact).all()

# Employer Operations
def create_employer(db: Session, employer: schemas.EmployerBase):
    existing_employer = db.query(models.Employer).filter(models.Employer.email == employer.email).first()
    if existing_employer:
        raise HTTPException(status_code=400, detail="Employer with this email already exists")

    company = db.query(models.Company).filter(models.Company.id == employer.company_id).first()
    if not company:
        raise HTTPException(status_code=400, detail="Company not found")

    poc_list = db.query(models.PointOfContact).filter(models.PointOfContact.id.in_(employer.poc_ids)).all()
    if len(poc_list) != len(employer.poc_ids):
        raise HTTPException(status_code=400, detail="One or more PoC IDs not found")

    db_employer = models.Employer(name=employer.name, email=employer.email, phone=employer.phone, company_id=employer.company_id, pocs=poc_list)
    db.add(db_employer)
    db.commit()
    db.refresh(db_employer)
    return db_employer

def get_employers(db: Session):
    return db.query(models.Employer).all()
