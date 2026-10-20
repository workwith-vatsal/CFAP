from fastapi.testclient import TestClient
import pytest
from sqlalchemy.orm import Session

from backend.app.core.security import create_access_token, hash_password
from backend.app.models.analysis import Analysis, AnalysisStatus
from backend.app.models.assistant import AssistantConversation, AssistantMessage
from backend.app.models.dataset import Dataset, DatasetStatus
from backend.app.models.feedback_result import FeedbackResult
from backend.app.models.user import User


def _setup_test_user_with_analysis(db: Session, email: str, status: AnalysisStatus = AnalysisStatus.COMPLETED):
    user = User(
        email=email,
        first_name="Assistant",
        last_name="Tester",
        password_hash=hash_password("Pass1234!"),
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    dataset = Dataset(
        owner_id=user.id,
        name="Feedback Data",
        original_filename="feedback.csv",
        storage_path="uploads/feedback.csv",
        file_type="csv",
        file_size_bytes=2048,
        row_count=5,
        feedback_column="feedback",
        quality_score=95.0,
        quality_report={
            "detected_columns": {
                "feedback": {"role": "feedback", "type": "string"},
                "channel": {"role": "category", "type": "string"},
            }
        },
        status=DatasetStatus.READY,
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)

    analysis = Analysis(
        dataset_id=dataset.id,
        owner_id=user.id,
        status=status,
        progress=100 if status == AnalysisStatus.COMPLETED else 20,
        total_feedback_rows=5,
        usable_feedback_rows=5,
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    # Add feedback records
    for i in range(5):
        s_lbl = "positive" if i < 3 else "negative"
        e_lbl = "joy" if i < 3 else "anger"
        fr = FeedbackResult(
            analysis_id=analysis.id,
            row_index=i,
            text_length=40,
            sentiment_label=s_lbl,
            sentiment_score=0.92,
            emotion_label=e_lbl,
            emotion_score=0.88,
            topic_id=1,
            topic_label="Product Quality",
            is_valid=True,
        )
        db.add(fr)
    db.commit()

    token = create_access_token(subject=str(user.id))
    headers = {"Authorization": f"Bearer {token}"}

    return user, dataset, analysis, headers


def test_create_conversation_success(client: TestClient, db_session: Session):
    user, dataset, analysis, headers = _setup_test_user_with_analysis(db_session, "user_conv1@example.com")

    payload = {
        "dataset_id": dataset.id,
        "analysis_id": analysis.id,
        "title": "My Analysis Thread",
    }
    response = client.post("/api/v1/assistant/conversations", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "My Analysis Thread"
    assert data["dataset_id"] == dataset.id
    assert data["analysis_id"] == analysis.id
    assert "id" in data


def test_create_conversation_requires_completed_analysis(client: TestClient, db_session: Session):
    user, dataset, analysis, headers = _setup_test_user_with_analysis(
        db_session, "user_conv_proc@example.com", status=AnalysisStatus.PROCESSING
    )

    payload = {
        "dataset_id": dataset.id,
        "analysis_id": analysis.id,
        "title": "Thread for processing",
    }
    response = client.post("/api/v1/assistant/conversations", json=payload, headers=headers)
    assert response.status_code == 400
    assert "require a COMPLETED analysis" in response.json()["detail"]


def test_send_message_and_grounded_response(client: TestClient, db_session: Session):
    user, dataset, analysis, headers = _setup_test_user_with_analysis(db_session, "user_msg@example.com")

    # 1. Create conversation
    res_conv = client.post(
        "/api/v1/assistant/conversations",
        json={"dataset_id": dataset.id, "analysis_id": analysis.id},
        headers=headers,
    )
    conv_id = res_conv.json()["id"]

    # 2. Send analytical question
    msg_payload = {"content": "What percentage of feedback is negative?"}
    res_msg = client.post(f"/api/v1/assistant/conversations/{conv_id}/messages", json=msg_payload, headers=headers)
    assert res_msg.status_code == 200
    msg_data = res_msg.json()
    assert msg_data["role"] == "assistant"
    assert msg_data["question_type"] == "SENTIMENT"
    assert msg_data["is_grounded"] is True
    assert "40.0%" in msg_data["content"] or "40%" in msg_data["content"] or "negative" in msg_data["content"].lower()

    # 3. Retrieve conversation history
    res_hist = client.get(f"/api/v1/assistant/conversations/{conv_id}", headers=headers)
    assert res_hist.status_code == 200
    hist_data = res_hist.json()
    assert len(hist_data["messages"]) == 2  # user + assistant


def test_suggested_questions(client: TestClient, db_session: Session):
    user, dataset, analysis, headers = _setup_test_user_with_analysis(db_session, "user_sugg@example.com")

    response = client.get(f"/api/v1/assistant/analyses/{analysis.id}/suggested-questions", headers=headers)
    assert response.status_code == 200
    suggestions = response.json()
    assert len(suggestions) >= 4
    assert any("negative" in s["question"].lower() for s in suggestions)


def test_multi_tenant_isolation_idor(client: TestClient, db_session: Session):
    """Verify User B cannot view or send messages to User A's conversations."""
    user_a, dataset_a, analysis_a, headers_a = _setup_test_user_with_analysis(db_session, "user_a_sec@example.com")
    user_b, dataset_b, analysis_b, headers_b = _setup_test_user_with_analysis(db_session, "user_b_sec@example.com")

    # User A creates a conversation
    res_a = client.post(
        "/api/v1/assistant/conversations",
        json={"dataset_id": dataset_a.id, "analysis_id": analysis_a.id},
        headers=headers_a,
    )
    conv_a_id = res_a.json()["id"]

    # User B tries to view User A's conversation -> 404
    res_b_view = client.get(f"/api/v1/assistant/conversations/{conv_a_id}", headers=headers_b)
    assert res_b_view.status_code == 404

    # User B tries to post a message into User A's conversation -> 404
    res_b_msg = client.post(
        f"/api/v1/assistant/conversations/{conv_a_id}/messages",
        json={"content": "Can I spy on User A?"},
        headers=headers_b,
    )
    assert res_b_msg.status_code == 404

    # User B tries to delete User A's conversation -> 404
    res_b_del = client.delete(f"/api/v1/assistant/conversations/{conv_a_id}", headers=headers_b)
    assert res_b_del.status_code == 404


def test_conversation_deletion(client: TestClient, db_session: Session):
    user, dataset, analysis, headers = _setup_test_user_with_analysis(db_session, "user_del@example.com")

    res_conv = client.post(
        "/api/v1/assistant/conversations",
        json={"dataset_id": dataset.id, "analysis_id": analysis.id},
        headers=headers,
    )
    conv_id = res_conv.json()["id"]

    del_res = client.delete(f"/api/v1/assistant/conversations/{conv_id}", headers=headers)
    assert del_res.status_code == 200

    # Verify 404 upon subsequent fetch
    get_res = client.get(f"/api/v1/assistant/conversations/{conv_id}", headers=headers)
    assert get_res.status_code == 404
