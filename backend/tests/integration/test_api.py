import pytest
from httpx import AsyncClient, ASGITransport
from src.api.main import app
from src.db.database import get_db, init_db
from src.worker.tasks import convert_pdf_task
from unittest.mock import patch, MagicMock
import os

# ...

@pytest.fixture
def mock_celery_task():
    # Mock both the Celery task and settings to use Celery
    with patch("src.worker.tasks.convert_pdf_task.delay") as mock_delay:
        # Set environment variable to enable Celery
        original_use_celery = os.getenv("USE_CELERY")
        os.environ["USE_CELERY"] = "true"
        yield mock_delay
        # Restore original value
        if original_use_celery is not None:
            os.environ["USE_CELERY"] = original_use_celery
        else:
            os.environ.pop("USE_CELERY", None)

@pytest.fixture(autouse=True)
async def setup_db():
    # Initialize DB before tests
    await init_db()
    yield
    # We could drop tables here if we want clean state


@pytest.mark.asyncio
async def test_upload_pdf(mock_celery_task):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Create a minimal valid PDF file
        minimal_pdf = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Test) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000206 00000 n
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
298
%%EOF
"""
        files = {"file": ("test.pdf", minimal_pdf, "application/pdf")}
        response = await ac.post("/api/v1/upload", files=files)

    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["status"] == "pending"

    # Verify Celery called
    mock_celery_task.assert_called_once()
    args = mock_celery_task.call_args[0]
    assert args[0] == data["id"] # First arg is task_id

@pytest.mark.asyncio
async def test_get_task_not_found():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/v1/tasks/non-existent-id")
        assert response.status_code == 404
