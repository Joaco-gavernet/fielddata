import pytest


@pytest.mark.asyncio
async def test_seeded_fields_are_listed(client) -> None:
    response = await client.get("/fields")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert {field["name"] for field in data} == {"North Field", "South Field"}


@pytest.mark.asyncio
async def test_alert_evaluation_creates_a_single_notification_and_deduplicates(client) -> None:
    fields_response = await client.get("/fields")
    field_id = fields_response.json()[0]["id"]

    create_alert_response = await client.post(
        "/alerts",
        json={
            "field_id": field_id,
            "event_type": "RAIN",
            "probability_threshold_percent": 80,
            "intensity_threshold_value": 8,
            "validity_windows": [
                {
                    "kind": "RELATIVE",
                    "relative_value": 1,
                    "relative_unit": "WEEK",
                }
            ],
        },
    )

    assert create_alert_response.status_code == 201
    assert create_alert_response.json()["intensity_unit"] == "MM_PER_HOUR"

    first_run_response = await client.post("/internal/jobs/evaluate-alerts")
    assert first_run_response.status_code == 200
    assert first_run_response.json()["created_notifications"] == 1

    notifications_response = await client.get("/notifications")
    assert notifications_response.status_code == 200
    notifications = notifications_response.json()
    assert len(notifications) == 1
    assert notifications[0]["event_type"] == "RAIN"
    assert notifications[0]["intensity_unit"] == "MM_PER_HOUR"

    second_run_response = await client.post("/internal/jobs/evaluate-alerts")
    assert second_run_response.status_code == 200
    assert second_run_response.json()["created_notifications"] == 0


@pytest.mark.asyncio
async def test_frost_alert_uses_celsius_and_less_than_comparison(client) -> None:
    fields_response = await client.get("/fields")
    field_id = fields_response.json()[0]["id"]

    create_alert_response = await client.post(
        "/alerts",
        json={
            "field_id": field_id,
            "event_type": "FROST",
            "probability_threshold_percent": 90,
            "intensity_threshold_value": -1,
            "validity_windows": [
                {
                    "kind": "RELATIVE",
                    "relative_value": 1,
                    "relative_unit": "WEEK",
                }
            ],
        },
    )

    assert create_alert_response.status_code == 201
    assert create_alert_response.json()["intensity_unit"] == "CELSIUS"

    evaluate_response = await client.post("/internal/jobs/evaluate-alerts")
    assert evaluate_response.status_code == 200
    assert evaluate_response.json()["created_notifications"] == 1

    notifications_response = await client.get("/notifications", params={"event_type": "FROST"})
    assert notifications_response.status_code == 200
    notifications = notifications_response.json()
    assert len(notifications) == 1
    assert notifications[0]["trigger_intensity_value"] == -2.0
    assert notifications[0]["intensity_unit"] == "CELSIUS"
