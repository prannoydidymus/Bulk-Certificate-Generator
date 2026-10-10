import os
from pathlib import Path
from app.services.certificate_generator import CertificateTemplateGenerator


def test_certificate_generator_creates_valid_pdf(tmp_path: Path):
    generator = CertificateTemplateGenerator()
    output_file = tmp_path / "sample_certificate.pdf"

    result_path = generator.generate_pdf(
        output_path=str(output_file),
        recipient_name="Jane Doe",
        event_name="Full Stack Web Development Bootcamp",
        organization_name="Global Tech University",
        issue_date="October 10, 2026",
        signatory_name="Prof. Alan Turing",
        signatory_title="Head of Computer Science",
        certificate_code="CERT-2026-TEST01",
        custom_note="Completed with High Honors",
    )

    assert os.path.exists(result_path)
    assert os.path.getsize(result_path) > 1000  # ReportLab PDF should be multiple KB

    # Validate PDF magic header
    with open(result_path, "rb") as f:
        header = f.read(5)
        assert header == b"%PDF-", "Generated file must start with PDF magic bytes"
