import re
import os
from datetime import datetime, timezone
from sqlalchemy.orm import Session
import app.database as database
from app.models import Job, Certificate, JobStatus, CertificateStatus
from app.services.certificate_generator import CertificateTemplateGenerator
from app.services.storage import CertificateStorageService

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_recipient_data(name: str | None, email: str | None) -> tuple[bool, str | None]:
    """
    Validates individual recipient data.
    Returns (is_valid, error_message).
    """
    if not name or not isinstance(name, str) or not name.strip():
        return False, "Recipient name is required and cannot be blank."

    if len(name.strip()) > 100:
        return False, "Recipient name exceeds maximum allowed length of 100 characters."

    if email is not None and isinstance(email, str) and email.strip():
        email_clean = email.strip()
        if not EMAIL_REGEX.match(email_clean):
            return False, f"Invalid email format: '{email_clean}'."

    return True, None


def process_certificate_job(job_id: str, db: Session | None = None) -> None:
    """
    Processes all certificates for a given job.
    Designed for background or synchronous execution with full failure isolation.
    """
    owns_session = False
    if db is None:
        db = database.SessionLocal()
        owns_session = True

    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return

        job.status = JobStatus.PROCESSING.value
        db.commit()

        generator = CertificateTemplateGenerator()
        certificates = db.query(Certificate).filter(Certificate.job_id == job_id).all()

        for cert in certificates:
            # Check validation
            is_valid, error_msg = validate_recipient_data(cert.recipient_name, cert.recipient_email)
            if not is_valid:
                cert.status = CertificateStatus.FAILED.value
                cert.error_message = f"Validation Error: {error_msg}"
                job.failed_count += 1
                job.processed_count += 1
                db.commit()
                continue

            # Attempt PDF Generation
            try:
                dest_path = str(CertificateStorageService.get_certificate_path(job.id, cert.id))
                generated_path = generator.generate_pdf(
                    output_path=dest_path,
                    recipient_name=cert.recipient_name.strip(),
                    event_name=job.event_name,
                    organization_name=job.organization_name,
                    issue_date=job.issue_date,
                    signatory_name=job.signatory_name,
                    signatory_title=job.signatory_title,
                    certificate_code=cert.certificate_code,
                )

                cert.file_path = generated_path
                cert.file_size = os.path.getsize(generated_path)
                cert.status = CertificateStatus.SUCCESS.value
                cert.error_message = None
                job.success_count += 1
            except Exception as exc:
                cert.status = CertificateStatus.FAILED.value
                cert.error_message = f"Generation Error: {str(exc)}"
                job.failed_count += 1

            job.processed_count += 1
            db.commit()

        # Update final job status
        if job.total_recipients == 0:
            job.status = JobStatus.COMPLETED.value
        elif job.success_count == job.total_recipients:
            job.status = JobStatus.COMPLETED.value
        elif job.success_count > 0 and job.failed_count > 0:
            job.status = JobStatus.PARTIALLY_COMPLETED.value
        else:
            job.status = JobStatus.FAILED.value

        job.completed_at = datetime.now(timezone.utc)
        db.commit()

    finally:
        if owns_session:
            db.close()
