import pytest
import app as attendance


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(attendance, "DB_PATH", str(tmp_path / "test.db"))
    return attendance.app.test_client()


def test_calculate_percentage():
    assert attendance.calculate_percentage(8, 10) == 80.0
    assert attendance.calculate_percentage(0, 0) == 0.0


def test_get_status():
    assert attendance.get_status(80.0, 10) == "Safe"
    assert attendance.get_status(60.0, 10) == "Low attendance"
    assert attendance.get_status(0.0, 0) == "No classes yet"


def test_home_page_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Personal Attendance Tracker" in response.data


def test_add_subject(client):
    client.post("/add_subject", data={"name": "Maths"})
    response = client.get("/")
    assert b"Maths" in response.data


def test_mark_attendance_and_percentage(client):
    client.post("/add_subject", data={"name": "Maths"})
    client.post("/mark", data={"subject_id": "1", "att_date": "2026-10-12", "status": "Present"})
    client.post("/mark", data={"subject_id": "1", "att_date": "2026-10-13", "status": "Absent"})
    summary = attendance.get_summary()
    assert summary[0]["total"] == 2
    assert summary[0]["attended"] == 1
    assert summary[0]["percentage"] == 50.0
    assert summary[0]["status"] == "Low attendance"