import os
from pathlib import Path
from datetime import timedelta
from typing import Optional
from app.config import settings

# Attempt import of google-cloud-storage
try:
    from google.cloud import storage as gcs
    HAS_GCS = True
except ImportError:
    HAS_GCS = False


def sanitize_filename(filename: str) -> str:
    """Sanitizes filename to prevent path traversal vulnerabilities."""
    # Strip directory components
    safe_name = os.path.basename(filename)
    # Remove any remaining dangerous characters or path separators
    safe_name = safe_name.replace("..", "").replace("/", "_").replace("\\", "_")
    if not safe_name or safe_name == ".":
        safe_name = "policy_document.txt"
    return safe_name


def get_gcs_object_path(project_id: str, policy_id: str, filename: str) -> str:
    """Constructs authoritative project-scoped GCS object path: projects/{project_id}/policies/{policy_id}/{filename}."""
    safe_name = sanitize_filename(filename)
    return f"projects/{project_id}/policies/{policy_id}/{safe_name}"


class StorageService:
    def __init__(self, bucket_name: Optional[str] = None):
        self.bucket_name = bucket_name or settings.GCS_BUCKET
        self.local_storage_dir = Path(".mock_gcs") / self.bucket_name
        self.local_storage_dir.mkdir(parents=True, exist_ok=True)

    def _get_gcs_client(self):
        if not HAS_GCS:
            return None
        try:
            return gcs.Client()
        except Exception:
            return None

    def upload_policy_document(self, project_id: str, policy_id: str, filename: str, content: bytes) -> str:
        """Uploads policy document privately to GCS (or mock storage if unconfigured).
        Returns the canonical gcs_uri: gs://{bucket_name}/{object_path}
        """
        object_path = get_gcs_object_path(project_id, policy_id, filename)
        gcs_uri = f"gs://{self.bucket_name}/{object_path}"

        client = self._get_gcs_client()
        if client:
            try:
                bucket = client.bucket(self.bucket_name)
                blob = bucket.blob(object_path)
                blob.upload_from_string(content)
                return gcs_uri
            except Exception:
                # Fallback to local mock storage
                pass

        # Local mock storage fallback for deterministic testing without live credentials
        local_path = self.local_storage_dir / object_path
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_bytes(content)
        return gcs_uri

    def download_policy_document(self, gcs_uri: str) -> bytes:
        """Downloads policy document content by gcs_uri."""
        if not gcs_uri.startswith(f"gs://{self.bucket_name}/"):
            # Strip scheme if formatted slightly differently
            object_path = gcs_uri.replace("gs://", "").split("/", 1)[-1]
        else:
            object_path = gcs_uri[len(f"gs://{self.bucket_name}/"):]

        client = self._get_gcs_client()
        if client:
            try:
                bucket = client.bucket(self.bucket_name)
                blob = bucket.blob(object_path)
                return blob.download_as_bytes()
            except Exception:
                pass

        # Local mock storage fallback
        local_path = self.local_storage_dir / object_path
        if local_path.exists():
            return local_path.read_bytes()
        raise FileNotFoundError(f"Policy object not found in GCS storage: {gcs_uri}")

    def generate_signed_url(self, gcs_uri: str, expiration_minutes: int = 15) -> str:
        """Generates short-lived signed URL (15-minute TTL)."""
        object_path = gcs_uri.replace(f"gs://{self.bucket_name}/", "")
        client = self._get_gcs_client()
        if client:
            try:
                bucket = client.bucket(self.bucket_name)
                blob = bucket.blob(object_path)
                return blob.generate_signed_url(expiration=timedelta(minutes=expiration_minutes))
            except Exception:
                pass
        # Fallback signed URL format for dev/mock
        return f"{settings.API_BASE_URL}/mock_storage/{self.bucket_name}/{object_path}?ttl=900"


storage_service = StorageService()

