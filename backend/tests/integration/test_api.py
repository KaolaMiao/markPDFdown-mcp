import pytest
from httpx import AsyncClient, ASGITransport
from src.api.main import app
from src.db.database import get_db, init_db
from src.worker.tasks import convert_pdf_task
from unittest.mock import patch

# ...

@pytest.fixture
def mock_celery_task():
    with patch("src.worker.tasks.convert_pdf_task.delay") as mock:
        yield mock

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
        # We need a dummy PDF
        files = {"file": ("test.pdf", b"%PDF-1.4...", "application/pdf")}
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
