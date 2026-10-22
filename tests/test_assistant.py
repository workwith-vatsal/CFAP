import pytest
from unittest.mock import MagicMock, patch

from backend.app.services.assistant.grounding import GroundingValidator
from backend.app.services.assistant.prompts import ASSISTANT_SYSTEM_PROMPT
from backend.app.services.assistant.provider import (
    BaseLLMProvider,
    GeminiProvider,
    MockGroundingProvider,
    OpenAIProvider,
    ProviderUnavailableError,
    get_llm_provider,
)
from backend.app.services.assistant.question_router import (
    QuestionCategory,
    QuestionRouter,
)


def test_question_router_categories():
    """Verify deterministic routing across all analytical categories."""
    assert QuestionRouter.route_question("What percentage of feedback is negative?") == QuestionCategory.SENTIMENT
    assert QuestionRouter.route_question("What is the Net Sentiment Score?") == QuestionCategory.SENTIMENT
    assert QuestionRouter.route_question("What emotions dominate negative feedback?") == QuestionCategory.CROSS_DIMENSION
    assert QuestionRouter.route_question("Which topic has the worst sentiment?") == QuestionCategory.CROSS_DIMENSION
    assert QuestionRouter.route_question("What are the dominant emotions?") == QuestionCategory.EMOTION
    assert QuestionRouter.route_question("What are the top topics in this feedback?") == QuestionCategory.TOPIC
    assert QuestionRouter.route_question("How has sentiment changed over time?") == QuestionCategory.TREND
    assert QuestionRouter.route_question("Show examples of delivery complaints.") == QuestionCategory.FEEDBACK_SEARCH
    assert QuestionRouter.route_question("Give me sample quotes about pricing.") == QuestionCategory.FEEDBACK_SEARCH
    assert QuestionRouter.route_question("Explain why this review was classified as negative with SHAP.") == QuestionCategory.EXPLANATION
    assert QuestionRouter.route_question("What columns does this dataset contain?") == QuestionCategory.DATASET
    assert QuestionRouter.route_question("Give me an executive summary and health status.") == QuestionCategory.OVERVIEW
    assert QuestionRouter.route_question("What is the capital of France?") == QuestionCategory.UNSUPPORTED
    assert QuestionRouter.route_question("Write a python script to parse json.") == QuestionCategory.UNSUPPORTED


def test_mock_grounding_provider_sentiment():
    """Verify mock provider returns strictly grounded sentiment metrics."""
    provider = MockGroundingProvider()
    context = {
        "question_type": "SENTIMENT",
        "overview": {
            "usable_feedback": 1000,
            "total_feedback": 1000,
            "net_sentiment_score": 50.0,
            "sentiment_distribution": {
                "positive": {"count": 700, "percentage": 70.0},
                "neutral": {"count": 100, "percentage": 10.0},
                "negative": {"count": 200, "percentage": 20.0},
            },
        },
    }
    resp = provider.generate_response("What is the negative percentage?", ASSISTANT_SYSTEM_PROMPT, context)
    assert "70.0%" in resp
    assert "20.0%" in resp
    assert "50.0" in resp
    assert "1000" in resp


def test_mock_grounding_provider_unsupported():
    """Verify mock provider politely rejects unsupported general questions."""
    provider = MockGroundingProvider()
    context = {"question_type": "UNSUPPORTED"}
    resp = provider.generate_response("Tell me a joke", ASSISTANT_SYSTEM_PROMPT, context)
    assert "dataset-grounded" in resp.lower()


def test_grounding_validator_causality_safeguard():
    """Verify ungrounded causal assertions are rewritten to associative phrasing."""
    context = {
        "overview": {
            "sentiment_distribution": {
                "positive": {"percentage": 60.0},
                "neutral": {"percentage": 20.0},
                "negative": {"percentage": 20.0},
            }
        }
    }
    ungrounded_text = "Late delivery caused customers to churn immediately."
    res = GroundingValidator.validate_and_sanitize(ungrounded_text, context)
    assert "caused customers to churn" not in res.sanitized_text.lower()
    assert "is associated with" in res.sanitized_text
    assert res.corrections_applied is True


def test_grounding_validator_hallucinated_percentage_rejection():
    """Verify detectable hallucinated percentages (not in context) are flagged."""
    context = {
        "overview": {
            "usable_feedback": 1000,
            "net_sentiment_score": 10.0,
            "sentiment_distribution": {
                "positive": {"percentage": 25.0},
                "neutral": {"percentage": 25.0},
                "negative": {"percentage": 50.0},
            }
        }
    }
    # 88.5% is completely made up
    text_with_hallucination = "Negative sentiment represents 88.5% of total feedback."
    res = GroundingValidator.validate_and_sanitize(text_with_hallucination, context)
    assert res.is_grounded is False
    assert any("88.5%" in issue for issue in res.issues)
    assert "Authoritative CFAP Breakdown" in res.sanitized_text


def test_grounding_validator_acceptable_rounding():
    """Verify reasonable rounding (e.g. 24.96% -> 25%) is accepted as grounded."""
    context = {
        "overview": {
            "sentiment_distribution": {
                "positive": {"percentage": 24.96},
                "neutral": {"percentage": 25.04},
                "negative": {"percentage": 50.0},
            }
        }
    }
    text = "Approximately 25% of customers gave positive feedback."
    res = GroundingValidator.validate_and_sanitize(text, context)
    assert res.is_grounded is True


def test_provider_factory_and_missing_keys():
    """Verify provider factory raises ProviderUnavailableError on missing credentials."""
    # Mock provider always works
    mock_prov = get_llm_provider("mock")
    assert isinstance(mock_prov, MockGroundingProvider)

    # Gemini with missing key raises ProviderUnavailableError on generation
    gemini_prov = GeminiProvider(api_key="")
    with pytest.raises(ProviderUnavailableError, match="Gemini API key is not configured"):
        gemini_prov.generate_response("hello", "sys", {})

    # OpenAI with missing key raises ProviderUnavailableError on generation
    openai_prov = OpenAIProvider(api_key="")
    with pytest.raises(ProviderUnavailableError, match="OpenAI API key is not configured"):
        openai_prov.generate_response("hello", "sys", {})
