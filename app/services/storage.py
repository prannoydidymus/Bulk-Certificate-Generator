import os
import zipfile
import io
from pathlib import Path
from typing import List, Tuple
from app.config import STORAGE_DIR


class CertificateStorageService:
    """Manages storage, retrieval, and packaging of certificate PDF files."""

    @staticmethod
    def get_certificate_path(job_id: str, certificate_id: str) -> Path:
        """Returns the destination filesystem path for a certificate."""
        job_dir = STORAGE_DIR / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        return job_dir / f"{certificate_id}.pdf"

    @staticmethod
    def file_exists(file_path: str | None) -> bool:
        """Checks if the certificate file exists on disk."""
        if not file_path:
            return False
        return os.path.isfile(file_path)

    @staticmethod
    def create_zip_archive(files: List[Tuple[str, str]]) -> io.BytesIO:
        """
        Creates an in-memory ZIP archive of multiple certificate files.
        
        Args:
            files: List of tuples (file_path_on_disk, arcname_in_zip)
            
        Returns:
            BytesIO stream of the zip archive.
        """
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for file_path, arcname in files:
                if os.path.isfile(file_path):
                    zip_file.write(file_path, arcname=arcname)
        zip_buffer.seek(0)
        return zip_buffer
