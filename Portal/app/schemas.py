from pydantic import BaseModel, EmailStr
from typing import Optional, List
import datetime
import enum


# Enum for User Roles
class UserRole(str, enum.Enum):
    EMPLOYER = "employer"
    EMPLOYEE = "employee"
    POINT_OF_CONTACT = "point_of_contact"


# User Schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr
    role: UserRole
    company: Optional[str] = None


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int

    class Config:
        from_attributes = True


# Company Schema
class CompanyBase(BaseModel):
    name: str
    industry: str
    about: str
    location: str
    description: str
    title: str
    website: str
    email: EmailStr
    phone: str
    established: int


# Point-of-Contact Schema
class PoCBase(BaseModel):
    name: str
    email: EmailStr
    phone: str


# Employer Schema
class EmployerBase(BaseModel):
    name: str
    email: EmailStr
    phone: str
    industry: str
    poc_ids: List[int] = []  # Accept multiple PoC IDs
    company_id: int


# Job Posting Schemas
class JobPostingBase(BaseModel):
    title: str
    description: str
    company: str
    location: str


class JobPostingCreate(JobPostingBase):
    pass


class JobPosting(JobPostingBase):
    id: int
    posted_at: datetime.datetime
    employer_id: Optional[int]

    class Config:
        from_attributes = True


class JobPostingWithoutId(JobPostingBase):
    posted_at: datetime.datetime


# Token Schema
class Token(BaseModel):
    access_token: str
    token_type: str
