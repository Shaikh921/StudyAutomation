import os
import sys
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app

client = TestClient(app)


def test_endpoints():
    print("Testing FastAPI Application Endpoints...")

    # 1. Health check
    res = client.get("/health")
    print(f"GET /health status: {res.status_code}, data: {res.json()}")
    assert res.status_code == 200

    # 2. System status
    res = client.get("/system/status")
    print(f"GET /system/status status: {res.status_code}, data: {res.json()}")
    assert res.status_code == 200

    # 3. Program status
    res = client.get("/program/status")
    print(f"GET /program/status status: {res.status_code}, data: {res.json()}")
    assert res.status_code == 200

    # 4. Program start (or duplicate start)
    res = client.post("/program/start")
    print(f"POST /program/start status: {res.status_code}, data: {res.json()}")
    assert res.status_code == 200

    # 5. Today's study plan
    res = client.get("/study/today")
    print(f"GET /study/today status: {res.status_code}, day: {res.json().get('day_number')}")
    assert res.status_code == 200

    # 6. DSA progress
    res = client.get("/dsa/progress")
    print(f"GET /dsa/progress status: {res.status_code}, data: {res.json()}")
    assert res.status_code == 200

    # 7. Job digest
    res = client.get("/jobs/digest")
    print(f"GET /jobs/digest status: {res.status_code}")
    assert res.status_code == 200

    # 8. Applications stats
    res = client.get("/applications/stats")
    print(f"GET /applications/stats status: {res.status_code}, data: {res.json()}")
    assert res.status_code == 200

    # 9. Dashboard HTML
    res = client.get("/dashboard")
    print(f"GET /dashboard status: {res.status_code}, HTML length: {len(res.text)}")
    assert res.status_code == 200
    assert "60-Day CSE Job Preparation Automation Platform" in res.text

    print("\nAll API endpoints tested and functioning 100% successfully!")


if __name__ == "__main__":
    test_endpoints()
