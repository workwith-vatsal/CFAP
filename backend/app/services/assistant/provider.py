from abc import ABC, abstractmethod
import json
import logging
from typing import Any, Dict, Optional
import httpx

from backend.app.core.config import settings

logger = logging.getLogger(__name__)


class ProviderUnavailableError(Exception):
    """Raised when an external LLM provider is not configured or unavailable."""
    pass


class BaseLLMProvider(ABC):
    """Abstract base class for AI Assistant LLM providers."""

    @abstractmethod
    def generate_response(
        self,
        prompt: str,
        system_prompt: str,
        context: Dict[str, Any],
        max_tokens: int = 1024,
        temperature: float = 0.2,
    ) -> str:
        """
        Generate a natural language response grounded in the provided context evidence.
        """
        pass


class MockGroundingProvider(BaseLLMProvider):
    """
    Deterministic Grounding Provider for unit testing, integration tests, and offline development.
    Answers strictly using numbers, labels, and evidence present in the context dictionary.
    Does NOT invent ungrounded metrics.
    """

    def generate_response(
        self,
        prompt: str,
        system_prompt: str,
        context: Dict[str, Any],
        max_tokens: int = 1024,
        temperature: float = 0.2,
    ) -> str:
        q_type = context.get("question_type", "OVERVIEW")
        overview = context.get("overview", {})
        total = overview.get("usable_feedback", overview.get("total_feedback", 0))
        sent_dist = overview.get("sentiment_distribution", {})
        pos_info = sent_dist.get("positive", {"count": 0, "percentage": 0.0})
        neg_info = sent_dist.get("negative", {"count": 0, "percentage": 0.0})
        neu_info = sent_dist.get("neutral", {"count": 0, "percentage": 0.0})
        nss = overview.get("net_sentiment_score", 0.0)

        if q_type == "UNSUPPORTED":
            return (
                "I am a dataset-grounded analytical assistant specifically designed to analyze your selected "
                "dataset and completed CFAP analysis. I do not answer unrelated general questions."
            )

        if q_type == "SENTIMENT":
            return (
                f"Based on the analysis of {total} feedback records, the sentiment distribution is as follows:\n"
                f"- **Positive**: {pos_info.get('percentage', 0.0)}% ({pos_info.get('count', 0)} records)\n"
                f"- **Neutral**: {neu_info.get('percentage', 0.0)}% ({neu_info.get('count', 0)} records)\n"
                f"- **Negative**: {neg_info.get('percentage', 0.0)}% ({neg_info.get('count', 0)} records)\n\n"
                f"The Net Sentiment Score (NSS) is {nss}."
            )

        if q_type == "EMOTION":
            top_emotions = context.get("emotions", overview.get("top_emotions", []))
            if not top_emotions:
                return f"No dominant emotion data is available for this analysis across {total} records."
            lines = [f"- **{e.get('emotion', 'unknown').capitalize()}**: {e.get('percentage', 0.0)}% ({e.get('count', 0)} records)" for e in top_emotions[:5]]
            dom = top_emotions[0].get('emotion', 'unknown')
            return (
                f"The dominant emotion identified across {total} records is **{dom}**.\n"
                f"Emotion breakdown:\n" + "\n".join(lines)
            )

        if q_type == "TOPIC":
            top_topics = context.get("topics", overview.get("top_topics", []))
            if not top_topics:
                return f"No topic clusters were identified for this analysis across {total} records."
            lines = [
                f"- **{t.get('label', 'Unknown')}**: {t.get('percentage', 0.0)}% ({t.get('count', 0)} records, NSS: {t.get('net_sentiment_score', 0.0)})"
                for t in top_topics[:5]
            ]
            return (
                f"Topic clustering across {total} records identified the following primary areas:\n"
                + "\n".join(lines)
            )

        if q_type == "CROSS_DIMENSION":
            matrices = context.get("cross_matrices", {})
            st = matrices.get("sentiment_topic", {}).get("topics", [])
            se = matrices.get("sentiment_emotion", {}).get("rows", [])
            lines = []
            if st:
                worst_topic = min(st, key=lambda x: x.get("net_sentiment_score", 0.0))
                lines.append(f"The topic with the lowest sentiment score is **{worst_topic.get('topic_label')}** with a Net Sentiment Score of {worst_topic.get('net_sentiment_score')} and {worst_topic.get('negative_percentage', 0.0)}% negative feedback.")
            if se:
                neg_row = next((r for r in se if r.get("sentiment") == "negative"), None)
                if neg_row:
                    emos = neg_row.get("emotions", {})
                    sorted_emos = sorted(emos.items(), key=lambda x: x[1].get("count", 0), reverse=True)
                    top_neg_emo = sorted_emos[0][0] if sorted_emos else "anger"
                    lines.append(f"Negative feedback is most strongly associated with **{top_neg_emo}**.")
            return "Cross-dimensional analysis shows:\n" + "\n".join(lines) if lines else f"Cross-dimensional patterns were analyzed across {total} records."

        if q_type == "TREND":
            trends = context.get("trends", {})
            if not trends.get("available", False):
                reason = trends.get("reason", "No valid timestamp column was available.")
                return f"Temporal trend analysis is not available for this dataset: {reason}"
            timeline = trends.get("timeline", [])
            return (
                f"Temporal trend analysis spanning {len(timeline)} time periods ({trends.get('interval', 'period')} interval) "
                f"shows feedback tracking over time based on the '{trends.get('date_column', 'date')}' column."
            )

        if q_type == "CATEGORY":
            breakdowns = context.get("categories", {})
            if not breakdowns.get("available", False):
                reason = breakdowns.get("reason", "No categorical dimension columns found.")
                return f"Categorical breakdown is not available: {reason}"
            col = breakdowns.get("column", "dimension")
            items = breakdowns.get("breakdown", [])
            lines = [f"- **{b.get('category_value')}**: {b.get('total_count')} records (NSS: {b.get('net_sentiment_score')})" for b in items[:5]]
            return f"Breakdown across categorical dimension **{col}**:\n" + "\n".join(lines)

        if q_type == "FEEDBACK_SEARCH":
            samples = context.get("feedback_samples", [])
            if not samples:
                return f"No matching feedback records were found for the requested query."
            lines = []
            for i, s in enumerate(samples, 1):
                text_preview = s.get("text", "")[:150]
                lines.append(f"{i}. \"{text_preview}\" (Sentiment: {s.get('sentiment')}, Emotion: {s.get('emotion')}, Topic: {s.get('topic')})")
            return f"Found {len(samples)} representative feedback record(s):\n" + "\n".join(lines)

        if q_type == "DATASET":
            ds_info = context.get("dataset_info", {})
            cols = ds_info.get("columns", [])
            return (
                f"Dataset **{ds_info.get('name', 'Dataset')}** contains {ds_info.get('total_rows', total)} total rows "
                f"and {len(cols)} columns: {', '.join(cols[:10])}. The primary feedback column is '{ds_info.get('feedback_column', 'text')}'."
            )

        # Default OVERVIEW response
        insights = context.get("insights", {})
        health = insights.get("health_status", "Moderate")
        health_score = insights.get("health_score", 50.0)
        return (
            f"Analysis summary across {total} analyzed feedback records:\n"
            f"- **Health Status**: {health} ({health_score}/100)\n"
            f"- **Net Sentiment Score (NSS)**: {nss}\n"
            f"- **Sentiment**: Positive: {pos_info.get('percentage', 0.0)}%, Neutral: {neu_info.get('percentage', 0.0)}%, Negative: {neg_info.get('percentage', 0.0)}%\n"
            f"- **Top Emotions**: {', '.join([e.get('emotion', '') for e in overview.get('top_emotions', [])[:3]]) or 'None'}\n"
            f"- **Top Topics**: {', '.join([t.get('label', '') for t in overview.get('top_topics', [])[:3]]) or 'None'}"
        )


class GeminiProvider(BaseLLMProvider):
    """
    Google Gemini Provider using standard HTTP REST interface.
    Model identifier is configurable via AI_ASSISTANT_MODEL (default: gemini-1.5-flash).
    """

    def __init__(self, model: Optional[str] = None, api_key: Optional[str] = None):
        self.model = model or settings.ai_assistant_model or "gemini-1.5-flash"
        self.api_key = api_key if api_key is not None else (settings.gemini_api_key or settings.llm_api_key)

    def generate_response(
        self,
        prompt: str,
        system_prompt: str,
        context: Dict[str, Any],
        max_tokens: int = 1024,
        temperature: float = 0.2,
    ) -> str:
        if not self.api_key:
            raise ProviderUnavailableError(
                "Gemini API key is not configured. Please configure GEMINI_API_KEY."
            )

        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"

        evidence_str = json.dumps(context, default=str, indent=2)
        user_content = (
            f"AUTHORITATIVE CFAP ANALYTICS EVIDENCE (Source of Truth):\n"
            f"```json\n{evidence_str}\n```\n\n"
            f"USER QUESTION:\n{prompt}"
        )

        payload = {
            "system_instruction": {
                "parts": [{"text": system_prompt}]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": user_content}]
                }
            ],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(endpoint, json=payload)

            if response.status_code == 429:
                raise ProviderUnavailableError("Gemini API rate limit exceeded. Please try again later.")
            if response.status_code in [401, 403]:
                raise ProviderUnavailableError("Gemini API authentication failed. Check credentials.")
            if response.status_code != 200:
                logger.error(f"Gemini API error ({response.status_code}): {response.text}")
                raise ProviderUnavailableError(f"Gemini API returned status code {response.status_code}.")

            data = response.json()
            candidates = data.get("candidates", [])
            if not candidates:
                raise ProviderUnavailableError("No response candidates returned by Gemini.")

            content_parts = candidates[0].get("content", {}).get("parts", [])
            if not content_parts:
                raise ProviderUnavailableError("Empty content returned by Gemini.")

            return content_parts[0].get("text", "").strip()

        except httpx.TimeoutException:
            raise ProviderUnavailableError("Gemini API request timed out.")
        except httpx.RequestError as req_err:
            logger.error(f"Gemini network request error: {req_err}")
            raise ProviderUnavailableError("Failed to connect to Gemini API.")


class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI Provider using standard HTTP REST interface.
    Model identifier is configurable via AI_ASSISTANT_MODEL (e.g. gpt-4o-mini).
    """

    def __init__(self, model: Optional[str] = None, api_key: Optional[str] = None):
        self.model = model or settings.ai_assistant_model or "gpt-4o-mini"
        self.api_key = api_key if api_key is not None else settings.openai_api_key

    def generate_response(
        self,
        prompt: str,
        system_prompt: str,
        context: Dict[str, Any],
        max_tokens: int = 1024,
        temperature: float = 0.2,
    ) -> str:
        if not self.api_key:
            raise ProviderUnavailableError(
                "OpenAI API key is not configured. Please configure OPENAI_API_KEY."
            )

        endpoint = "https://api.openai.com/v1/chat/completions"
        evidence_str = json.dumps(context, default=str, indent=2)
        user_content = (
            f"AUTHORITATIVE CFAP ANALYTICS EVIDENCE (Source of Truth):\n"
            f"```json\n{evidence_str}\n```\n\n"
            f"USER QUESTION:\n{prompt}"
        )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(endpoint, headers=headers, json=payload)

            if response.status_code == 429:
                raise ProviderUnavailableError("OpenAI API rate limit exceeded. Please try again later.")
            if response.status_code in [401, 403]:
                raise ProviderUnavailableError("OpenAI API authentication failed. Check credentials.")
            if response.status_code != 200:
                logger.error(f"OpenAI API error ({response.status_code}): {response.text}")
                raise ProviderUnavailableError(f"OpenAI API returned status code {response.status_code}.")

            data = response.json()
            choices = data.get("choices", [])
            if not choices:
                raise ProviderUnavailableError("No response choices returned by OpenAI.")

            return choices[0].get("message", {}).get("content", "").strip()

        except httpx.TimeoutException:
            raise ProviderUnavailableError("OpenAI API request timed out.")
        except httpx.RequestError as req_err:
            logger.error(f"OpenAI network request error: {req_err}")
            raise ProviderUnavailableError("Failed to connect to OpenAI API.")


def get_llm_provider(provider_name: Optional[str] = None) -> BaseLLMProvider:
    """
    Factory function to retrieve the configured LLM provider instance.
    Never silently masquerades a missing production provider as mock.
    """
    selected = (provider_name or settings.ai_assistant_provider or "mock").lower()

    if selected == "mock":
        return MockGroundingProvider()
    elif selected == "gemini":
        return GeminiProvider(model=settings.ai_assistant_model)
    elif selected == "openai":
        return OpenAIProvider(model=settings.ai_assistant_model)
    else:
        raise ValueError(f"Unsupported AI assistant provider: '{selected}'. Supported: 'gemini', 'openai', 'mock'.")
