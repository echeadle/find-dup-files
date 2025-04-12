import pytest
from fastapi.testclient import TestClient
from pathlib import Path
# Assuming your FastAPI app instance is named 'app' and is importable
# Adjust the import below if your app instance is located elsewhere
from app.main import app

# Define the client fixture for tests in this module
@pytest.fixture(scope="module")
def client():
    """
    Provides a TestClient instance for the FastAPI app.
    Scope is 'module' so the client is created once per test module.
    """
    with TestClient(app) as c:
        yield c

def test_scan_endpoint_scan_fails_with_file_path(tmp_path: Path, client: TestClient): # Renamed for clarity
    """
    Test that the /api/scan endpoint returns 404 if the provided path
    points to a file instead of a directory.
    """
    # Create a file instead of a directory
    scan_target_file = tmp_path / "scan_target.txt"
    scan_target_file.write_text("This is a file, not a directory.")
    scan_target_path_str = str(scan_target_file)

    # Send a POST request to scan the file path
    response = client.post("/api/scan", json={"directory_path": scan_target_path_str})

    # Assert that the response is a 404 Not Found
    assert response.status_code == 404, f"Expected status code 404, but got {response.status_code}. Response: {response.text}"

    # Assert that the detail message indicates the directory was not found
    response_data = response.json()
    assert "detail" in response_data
    expected_detail_substring = f"Directory not found: {scan_target_path_str}" # Or just "Directory not found" or "Not a directory"
    assert expected_detail_substring in response_data["detail"], \
        f"Expected detail to contain '{expected_detail_substring}', but got: {response_data['detail']}"

    # --- You could keep a more flexible check if needed ---
    # possible_details = ["Directory not found", "Not a directory"]
    # assert any(detail in response_data["detail"] for detail in possible_details), \
    #     f"Expected detail to indicate a directory issue, but got: {response_data['detail']}"

