from __future__ import annotations

from unittest.mock import MagicMock, patch

from src.starbucks_analyser.llm.summarize import summarize_metrics, summarize_structured


@patch("src.starbucks_analyser.llm.summarize.get_client")
def test_summarize_metrics(mock_client):
    m = MagicMock()
    m.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="ok"))]
    )
    mock_client.return_value = m
    out = summarize_metrics({"drinks": {"means": {"calories": 100}}})
    assert out == "ok"


@patch("src.starbucks_analyser.llm.summarize._chat_with_retry")
def test_summarize_structured_schema(mock_chat):
    mock_chat.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content='{"summary_text":"s","key_points":["a"],"caveats":[]}'))]
    )
    payload = {"drinks": {"means": {"calories": 100}}, "food": {"means": {"calories": 200}}, "comparisons": {}, "tops": {}}
    obj = summarize_structured(payload)
    assert set(obj.keys()) == {"summary_text", "key_points", "caveats"}
