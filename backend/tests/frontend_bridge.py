"""Frontend contract check helper: real FastAPI schemas/routes, mocked AI only."""
import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient
from app.schemas.idea import IdeaItem
from main import create_app

payload = json.load(sys.stdin)
results = [
    IdeaItem(title="학습 도우미", description="학습 일정을 관리합니다.", tags=["학습"]),
    IdeaItem(title="집중 타이머", description="집중 시간을 관리합니다.", tags=["집중"]),
]
with patch("app.services.ai_service._call_ollama", new_callable=AsyncMock, return_value=results):
    with TestClient(create_app()) as client:
        response = client.post(payload["url"], json=payload["body"])
print(json.dumps({"status": response.status_code, "data": response.json()}, ensure_ascii=False))
