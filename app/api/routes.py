import uuid
from datetime import datetime, date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, Request, Response, status
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Job, Certificate, JobStatus, CertificateStatus
from app.schemas import (
    JobCreateRequest,
    JobCreateResponse,
    JobSummaryResponse,
    JobDetailResponse,
    CertificateResponse,
)
from app.config import (
    DEFAULT_ORGANIZATION,
    DEFAULT_SIGNATORY_NAME,
    DEFAULT_SIGNATORY_TITLE,
)
from app.services.job_processor import process_certificate_job
from app.services.storage import CertificateStorageService

router = APIRouter(prefix="/api/v1")


def _format_certificate_response(cert: Certificate, request: Request) -> CertificateResponse:
    """Helper to convert Certificate DB model to schema with full download URL."""
    base_url = str(request.base_url).rstrip("/")
    download_url = None
    if cert.status == CertificateStatus.SUCCESS.value and cert.file_path:
        download_url = f"{base_url}/api/v1/certificates/{cert.id}/download"

    return CertificateResponse(
        id=cert.id,
        job_id=cert.job_id,
        recipient_name=cert.recipient_name,
        recipient_email=cert.recipient_email,
        certificate_code=cert.certificate_code,
        status=CertificateStatus(cert.status),
        file_size=cert.file_size,
        error_message=cert.error_message,
        download_url=download_url,
        created_at=cert.created_at,
    )


def _format_job_summary(job: Job) -> JobSummaryResponse:
    """Helper to calculate progress percentage and format Job summary."""
    pct = 0.0
    if job.total_recipients > 0:
        pct = round((job.processed_count / job.total_recipients) * 100, 2)

    return JobSummaryResponse(
        id=job.id,
        event_name=job.event_name,
        organization_name=job.organization_name,
        issue_date=job.issue_date,
        signatory_name=job.signatory_name,
        signatory_title=job.signatory_title,
        status=JobStatus(job.status),
        total_recipients=job.total_recipients,
        processed_count=job.processed_count,
        success_count=job.success_count,
        failed_count=job.failed_count,
        progress_percentage=pct,
        created_at=job.created_at,
        completed_at=job.completed_at,
    )


@router.post(
    "/jobs",
    response_model=JobCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit a bulk certificate generation job",
    description="Submits a list of recipients to generate certificates using the predefined template. Generation is processed asynchronously in the background by default.",
)
def create_generation_job(
    payload: JobCreateRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    response: Response,
    sync: bool = Query(
        False,
        description="If true, processes synchronously before responding. If false (default), runs in background.",
    ),
    db: Session = Depends(get_db),
):
    if not payload.recipients:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Recipient list cannot be empty.",
        )

    job_id = str(uuid.uuid4())
    issue_date = payload.issue_date or date.today().strftime("%B %d, %Y")
    org_name = payload.organization_name or DEFAULT_ORGANIZATION
    sig_name = payload.signatory_name or DEFAULT_SIGNATORY_NAME
    sig_title = payload.signatory_title or DEFAULT_SIGNATORY_TITLE

    new_job = Job(
        id=job_id,
        event_name=payload.event_name.strip(),
        organization_name=org_name.strip(),
        issue_date=issue_date.strip(),
        signatory_name=sig_name.strip(),
        signatory_title=sig_title.strip(),
        status=JobStatus.PENDING.value,
        total_recipients=len(payload.recipients),
        processed_count=0,
        success_count=0,
        failed_count=0,
    )
    db.add(new_job)

    # Pre-populate certificate records
    for recipient in payload.recipients:
        cert_id = str(uuid.uuid4())
        short_code = f"CERT-{job_id[:8].upper()}-{cert_id[:6].upper()}"
        name = recipient.name if recipient.name else ""
        email = recipient.email if recipient.email else None

        cert_record = Certificate(
            id=cert_id,
            job_id=job_id,
            recipient_name=name,
            recipient_email=email,
            certificate_code=short_code,
            status=CertificateStatus.PENDING.value,
        )
        db.add(cert_record)

    db.commit()

    base_url = str(request.base_url).rstrip("/")
    status_url = f"{base_url}/api/v1/jobs/{job_id}"

    if sync:
        # Run synchronously
        process_certificate_job(job_id, db=db)
        db.refresh(new_job)
        response.status_code = status.HTTP_201_CREATED
        return JobCreateResponse(
            job_id=job_id,
            message="Certificate generation job completed synchronously.",
            status=JobStatus(new_job.status),
            total_recipients=new_job.total_recipients,
            status_url=status_url,
        )
    else:
        # Run asynchronously in background
        background_tasks.add_task(process_certificate_job, job_id)
        return JobCreateResponse(
            job_id=job_id,
            message="Certificate generation job accepted and processing in background.",
            status=JobStatus.PENDING,
            total_recipients=new_job.total_recipients,
            status_url=status_url,
        )


@router.get(
    "/jobs/{job_id}",
    response_model=JobDetailResponse,
    summary="Get job status, progress, and certificates",
    description="Returns detailed progress metrics and the status of each certificate generated in the job.",
)
def get_job_details(job_id: str, request: Request, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID '{job_id}' not found.",
        )

    summary = _format_job_summary(job)
    certs = (
        db.query(Certificate)
        .filter(Certificate.job_id == job_id)
        .order_by(Certificate.created_at.asc())
        .all()
    )

    cert_responses = [_format_certificate_response(c, request) for c in certs]

    return JobDetailResponse(
        **summary.model_dump(),
        certificates=cert_responses,
    )


@router.get(
    "/jobs",
    response_model=List[JobSummaryResponse],
    summary="List all certificate generation jobs",
    description="Retrieve a paginated list of certificate generation jobs with optional status filtering.",
)
def list_jobs(
    status_filter: Optional[JobStatus] = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Job)
    if status_filter:
        query = query.filter(Job.status == status_filter.value)

    jobs = query.order_by(Job.created_at.desc()).offset(skip).limit(limit).all()
    return [_format_job_summary(job) for job in jobs]


@router.get(
    "/certificates/{certificate_id}",
    response_model=CertificateResponse,
    summary="Get certificate metadata",
    description="Retrieve status and metadata for a specific certificate.",
)
def get_certificate_metadata(
    certificate_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    cert = db.query(Certificate).filter(Certificate.id == certificate_id).first()
    if not cert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificate with ID '{certificate_id}' not found.",
        )
    return _format_certificate_response(cert, request)


@router.get(
    "/certificates/{certificate_id}/download",
    summary="Download individual certificate PDF",
    description="Streams the generated PDF certificate for a recipient.",
)
def download_certificate(
    certificate_id: str,
    db: Session = Depends(get_db),
):
    cert = db.query(Certificate).filter(Certificate.id == certificate_id).first()
    if not cert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificate with ID '{certificate_id}' not found.",
        )

    if cert.status != CertificateStatus.SUCCESS.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Certificate cannot be downloaded because its status is '{cert.status}'. Reason: {cert.error_message or 'Not generated yet'}",
        )

    if not cert.file_path or not CertificateStorageService.file_exists(cert.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate file does not exist on disk.",
        )

    # Sanitize recipient name for filename
    safe_name = "".join(c for c in cert.recipient_name if c.isalnum() or c in (" ", "-", "_")).strip()
    filename = f"Certificate_{safe_name.replace(' ', '_')}_{cert.certificate_code}.pdf"

    return FileResponse(
        path=cert.file_path,
        media_type="application/pdf",
        filename=filename,
    )


@router.get(
    "/jobs/{job_id}/download-all",
    summary="Download all certificates as a ZIP archive",
    description="Packages all successfully generated certificates in the job into a downloadable ZIP archive.",
)
def download_all_certificates(
    job_id: str,
    db: Session = Depends(get_db),
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID '{job_id}' not found.",
        )

    successful_certs = (
        db.query(Certificate)
        .filter(Certificate.job_id == job_id, Certificate.status == CertificateStatus.SUCCESS.value)
        .all()
    )

    if not successful_certs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No successfully generated certificates found for this job to package.",
        )

    file_entries = []
    for cert in successful_certs:
        if cert.file_path and CertificateStorageService.file_exists(cert.file_path):
            safe_name = "".join(c for c in cert.recipient_name if c.isalnum() or c in (" ", "-", "_")).strip()
            arcname = f"Certificate_{safe_name.replace(' ', '_')}_{cert.certificate_code}.pdf"
            file_entries.append((cert.file_path, arcname))

    if not file_entries:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate files were not found on disk.",
        )

    zip_stream = CertificateStorageService.create_zip_archive(file_entries)
    safe_event = "".join(c for c in job.event_name if c.isalnum() or c in (" ", "-", "_")).strip().replace(" ", "_")
    zip_filename = f"Certificates_{safe_event}_{job.id[:8]}.zip"

    return StreamingResponse(
        zip_stream,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{zip_filename}"'},
    )
