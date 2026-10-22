from unittest.mock import MagicMock, patch
import pytest
import numpy as np

from backend.app.services.ai.explainability import (
    ExplainabilityService,
    RAW_STAR_TO_SENTIMENT,
    STAR_MAPPING_RULES,
)


def test_star_to_sentiment_mapping_rules():
    assert RAW_STAR_TO_SENTIMENT["1 star"] == "Negative"
    assert RAW_STAR_TO_SENTIMENT["2 stars"] == "Negative"
    assert RAW_STAR_TO_SENTIMENT["3 stars"] == "Neutral"
    assert RAW_STAR_TO_SENTIMENT["4 stars"] == "Positive"
    assert RAW_STAR_TO_SENTIMENT["5 stars"] == "Positive"

    assert "1★" in STAR_MAPPING_RULES["1 star"]
    assert "5★" in STAR_MAPPING_RULES["5 stars"]


def test_explain_text_empty_input():
    service = ExplainabilityService.__new__(ExplainabilityService)
    service.model_name = "nlptown/bert-base-multilingual-uncased-sentiment"
    service.explainer_name = "PartitionExplainer"

    result = service.explain_text("")
    assert result["predicted_label"] == "Neutral"
    assert result["raw_predicted_label"] == "3 stars"
    assert result["confidence"] == 0.0
    assert result["token_contributions"] == []
    assert result["positive_tokens"] == []
    assert result["negative_tokens"] == []
    assert result["sentiment_mapping"]["raw_star_output"] == "3 stars"
    assert result["sentiment_mapping"]["cfap_mapped_sentiment"] == "Neutral"


def test_explain_text_mocked_shap():
    service = ExplainabilityService.__new__(ExplainabilityService)
    service.model_name = "nlptown/bert-base-multilingual-uncased-sentiment"
    service.explainer_name = "PartitionExplainer"

    mock_pipe = MagicMock()
    mock_pipe.return_value = [
        [
            {"label": "1 star", "score": 0.05},
            {"label": "2 stars", "score": 0.05},
            {"label": "3 stars", "score": 0.10},
            {"label": "4 stars", "score": 0.10},
            {"label": "5 stars", "score": 0.70},
        ]
    ]
    service.pipe = mock_pipe

    mock_shap_values = MagicMock()
    mock_shap_values.data = [["", "The", "app", "is", "super", "fast", "!", ""]]
    # 8 tokens, 5 classes
    shap_matrix = np.zeros((8, 5))
    shap_matrix[4, 4] = 0.45  # "super" -> positive for 5 stars
    shap_matrix[5, 4] = 0.35  # "fast" -> positive for 5 stars
    shap_matrix[2, 4] = -0.05 # "app" -> slightly negative
    mock_shap_values.values = [shap_matrix]
    mock_shap_values.base_values = [[0.1, 0.1, 0.1, 0.1, 0.2]]

    mock_explainer = MagicMock()
    mock_explainer.return_value = mock_shap_values
    service.explainer = mock_explainer

    res = service.explain_text("The app is super fast!")

    assert res["predicted_label"] == "Positive"
    assert res["raw_predicted_label"] == "5 stars"
    assert res["confidence"] == 0.70
    assert res["base_value"] == 0.2
    assert len(res["token_contributions"]) == 6  # 6 non-empty tokens
    assert res["positive_tokens"][0]["token"] == "super"
    assert res["positive_tokens"][0]["shap_value"] == 0.45
    assert res["negative_tokens"][0]["token"] == "app"
    assert res["sentiment_mapping"]["raw_star_output"] == "5 stars"
    assert res["sentiment_mapping"]["cfap_mapped_sentiment"] == "Positive"
    assert "4★" in res["sentiment_mapping"]["mapping_rule"] or "5★" in res["sentiment_mapping"]["mapping_rule"]
