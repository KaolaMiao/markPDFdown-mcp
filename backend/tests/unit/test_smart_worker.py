import pytest
from unittest.mock import MagicMock, patch, call, ANY
import asyncio
from concurrent.futures import ThreadPoolExecutor

from src.worker.smart_worker import SmartWorker

@pytest.fixture
def mock_llm_client():
    with patch("src.worker.smart_worker.LLMClient") as mock:
        client_instance = mock.return_value
        client_instance.completion.return_value = "Mocked Markdown Content"
        yield client_instance

@pytest.fixture
def mock_create_worker():
    with patch("src.worker.smart_worker.create_worker") as mock:
        worker_instance = MagicMock()
        # Simulate 3 images
        worker_instance.convert_to_images.return_value = [
            "/tmp/page_1.jpg", 
            "/tmp/page_2.jpg", 
            "/tmp/page_3.jpg"
        ]
        mock.return_value = worker_instance
        yield mock

@pytest.mark.asyncio
async def test_smart_worker_flow(mock_create_worker, mock_llm_client):
    """
    Test that SmartWorker splits PDF and calls LLM in parallel (via threads)
    """
    # Mock loop.run_in_executor to just call the function immediately or use real thread pool
    # Real thread pool is fine if mocks are thread safe or simple.
    
    worker = SmartWorker(model_name="gpt-4o", concurrency=3)
    
    # We call process_file
    result = await worker.process_file("/tmp/test.pdf")
    
    # Verify split was called
    mock_create_worker.assert_called_once_with("/tmp/test.pdf")
    
    # Verify LLM called 3 times
    assert mock_llm_client.completion.call_count == 3
    
    # Verify arguments to LLM (check one of them)
    # We expect verify call args to contain image paths
    # The 'image_paths' arg should be a list containing one image
    mock_llm_client.completion.assert_any_call(
        user_message=ANY,
        system_prompt=ANY,
        image_paths=["/tmp/page_1.jpg"],
        temperature=ANY,
        max_tokens=ANY,
        retry_times=ANY
    )
    
    # Verify Result Combination
    assert "Mocked Markdown Content" in result
    # "Mocked Markdown Content" repeated 3 times with \n\n
    assert result.count("Mocked Markdown Content") == 3
