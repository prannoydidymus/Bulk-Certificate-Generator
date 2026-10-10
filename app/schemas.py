from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, ConfigDict
from app.models import JobStatus, CertificateStatus


class RecipientInput(BaseModel):
    name: Optional[str] = Field(default=None, description="Full name of the recipient")
    email: Optional[str] = Field(default=None, description="Email address of the recipient")
    custom_note: Optional[str] = Field(default=None, description="Custom achievement note or distinction")


class JobCreateRequest(BaseModel):
    event_name: str = Field(
        ...,
        min_length=1,
        description="Name of the course, training, or event",
        examples=["Advanced Python & FastAPI Bootcamp"]
    )
    organization_name: Optional[str] = Field(
        default=None,
        description="Issuing organization or institution name",
        examples=["Tech Academy International"]
    )
    issue_date: Optional[str] = Field(
        default=None,
        description="Certificate issue date (e.g. YYYY-MM-DD or October 10, 2026)",
        examples=["2026-10-10"]
    )
    signatory_name: Optional[str] = Field(
        default=None,
        description="Name of the authorized signatory",
        examples=["Dr. Sarah Connor"]
    )
    signatory_title: Optional[str] = Field(
        default=None,
        description="Title of the authorized signatory",
        examples=["Head of Certification"]
    )
    recipients: List[RecipientInput] = Field(
        ...,
        min_length=1,
        description="List of recipients to generate certificates for"
    )

    @field_validator("event_name")
    @classmethod
    def validate_event_name_not_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("event_name cannot be empty or blank")
        return v.strip()


class CertificateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    job_id: str
    recipient_name: str
    recipient_email: Optional[str] = None
    certificate_code: str
    status: CertificateStatus
    file_size: Optional[int] = None
    error_message: Optional[str] = None
    download_url: Optional[str] = None
    created_at: datetime


class JobSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    event_name: str
    organization_name: str
    issue_date: str
    signatory_name: str
    signatory_title: str
    status: JobStatus
    total_recipients: int
    processed_count: int
    success_count: int
    failed_count: int
    progress_percentage: float
    created_at: datetime
    completed_at: Optional[datetime] = None


class JobDetailResponse(JobSummaryResponse):
    certificates: List[CertificateResponse] = []


class JobCreateResponse(BaseModel):
    job_id: str
    message: str
    status: JobStatus
    total_recipients: int
    status_url: str
