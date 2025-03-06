from sqlalchemy import Column, Integer, String, Enum, Text, DateTime, ForeignKey,CheckConstraint,Table
from sqlalchemy.orm import relationship
from .database import Base
import enum
from datetime import datetime,timezone
from app. models import Base  
  

class UserRole(enum.Enum):
    EMPLOYER = "employer"
    EMPLOYEE = "employee"
    POINT_OF_CONTACT = "point_of_contact"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(150), unique=True, index=True)
    email = Column((String(255)), unique=True, index=True)
    hashed_password = Column(String(255))
    role = Column(String(50), nullable=False)

    company = Column(String(255), nullable=True)   # Company should be optional

    __table_args__ = (
        CheckConstraint(
            "(role IN ('employer', 'point_of_contact') AND company IS NOT NULL) OR (role = 'employee' AND company IS NULL)",
            name="check_company_for_roles"
        ),
    )
    # Relationship to JobPosting
    jobs = relationship("JobPosting", back_populates="employer")
    

    def belongs_to_company(self) -> bool:
        """Returns True if the user is an Employer or PoC."""
        return self.role in [UserRole.EMPLOYER, UserRole.POINT_OF_CONTACT]

class JobPosting(Base):
    __tablename__ = "job_postings"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), index=True)  
    description = Column(Text, nullable=False)
    company = Column(String(255), index=True)  
    location = Column(String(255), nullable=True)  
    posted_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    employer_id = Column(Integer, ForeignKey("users.id"))


    # Association Table for Many-to-Many Relationship
employer_poc_association = Table(
    "employer_poc_association",
    Base.metadata,
    Column("employer_id", Integer, ForeignKey("employers.id"), primary_key=True),
    Column("poc_id", Integer, ForeignKey("pocs.id"), primary_key=True)
)


# Company Table
class Company(Base):
    __tablename__ = "companies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True)  
    industry = Column(String(255), nullable=True)  
    about = Column(Text, nullable=True)  
    website = Column(String(255), nullable=True) 
    email = Column(String(255), nullable=False, unique=True, index=True)  
    phone = Column(String(20), unique=True, nullable=True)  
    location = Column(String(255), nullable=True)  
    established = Column(Integer, nullable=True)  
    
    employers = relationship("Employer", back_populates="company")



# Employer Table
class Employer(Base):
    __tablename__ = "employers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True)  
    email = Column(String(255), unique=True, index=True)  
    phone = Column(String(20), unique=True, nullable=True)  
    industry = Column(String(255), nullable=True)  # ✅ Added length
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)  # Employer belongs to ONE company

    # relationship between employer and poc
    
    company = relationship("Company", back_populates="employers")
 # Many-to-Many Relationship with PoCs
    pocs = relationship("PointOfContact", secondary=employer_poc_association, back_populates="employers")

# Point-of-Contact Table
class PointOfContact(Base):
    __tablename__ = "pocs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)  
    email = Column(String(255), unique=True, nullable=False, index=True)  
    phone = Column(String(20), unique=True, nullable=True)

 # Many-to-Many Relationship with Employers
    employers = relationship("Employer", secondary=employer_poc_association, back_populates="pocs")
