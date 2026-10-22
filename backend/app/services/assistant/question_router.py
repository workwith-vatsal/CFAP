import re
from typing import Dict, List, Tuple


class QuestionCategory:
    OVERVIEW = "OVERVIEW"
    SENTIMENT = "SENTIMENT"
    EMOTION = "EMOTION"
    TOPIC = "TOPIC"
    CROSS_DIMENSION = "CROSS_DIMENSION"
    TREND = "TREND"
    CATEGORY = "CATEGORY"
    FEEDBACK_SEARCH = "FEEDBACK_SEARCH"
    EXPLANATION = "EXPLANATION"
    DATASET = "DATASET"
    UNSUPPORTED = "UNSUPPORTED"


class QuestionRouter:
    """
    Deterministic Question Router for CFAP.
    Classifies natural language user queries into specific analytical categories
    to pinpoint the exact authoritative evidence required from CFAP analytics.
    """

    UNSUPPORTED_PATTERNS = [
        r"\b(weather|capital of|recipe|poem|joke|sing a song|write a story|write code|python script|who is|who won|football|cricket|nba|president)\b",
        r"\b(translate to french|translate to spanish|stock price|crypto|bitcoin|tell me about yourself)\b",
    ]

    FEEDBACK_SEARCH_PATTERNS = [
        r"\b(show|give|find|search|list|sample|display|get)\s+(me\s+)?(examples?|reviews?|comments?|feedback|quotes?|records?|samples?)\b",
        r"\b(examples?\s+of|complaints?\s+about|reviews?\s+mentioning|customers?\s+saying)\b",
        r"\b(quote\s+some|raw\s+feedback|actual\s+reviews?)\b",
    ]

    EXPLANATION_PATTERNS = [
        r"\b(explain\s+why|why\s+is|why\s+was|shap|feature\s+importance|word\s+attribution|model\s+reasoning|why\s+classified)\b",
    ]

    DATASET_PATTERNS = [
        r"\b(what\s+columns?|columns?\s+does|dataset\s+contains?|dataset\s+info|dataset\s+structure|dataset\s+schema|how\s+many\s+rows|total\s+rows|dataset\s+details)\b",
    ]

    TREND_PATTERNS = [
        r"\b(over\s+time|trend|trends|temporal|timeline|by\s+month|by\s+week|by\s+day|daily|weekly|monthly|historically|changed\s+over\s+time|evolution)\b",
    ]

    CROSS_DIMENSION_PATTERNS = [
        r"\b(emotions?\s+dominate\s+negative|emotion.*sentiment|sentiment.*emotion)\b",
        r"\b(which\s+topic\s+has\s+the\s+worst|topic.*sentiment|sentiment.*topic|topic.*emotion|emotion.*topic)\b",
        r"\b(worst\s+topic|negative\s+topic|negative\s+theme|most\s+negative\s+topic|most\s+positive\s+topic)\b",
        r"\b(topic\s+breakdown\s+by\s+sentiment|sentiment\s+across\s+topics|cross\s+dimension|matrix)\b",
    ]

    CATEGORY_PATTERNS = [
        r"\b(by\s+channel|by\s+region|by\s+country|by\s+category|by\s+segment|by\s+tier|by\s+product|categorical|dimension)\b",
    ]

    SENTIMENT_PATTERNS = [
        r"\b(percentage.*negative|percentage.*positive|percentage.*neutral|ratio.*positive|ratio.*negative)\b",
        r"\b(how\s+many\s+negative|how\s+many\s+positive|how\s+many\s+neutral|how\s+much\s+negative|how\s+much\s+positive)\b",
        r"\b(net\s+sentiment\s+score|nss|sentiment\s+distribution|sentiment\s+breakdown|overall\s+sentiment|sentiment\s+ratio)\b",
    ]

    EMOTION_PATTERNS = [
        r"\b(dominant\s+emotions?|top\s+emotions?|most\s+common\s+emotions?|emotion\s+distribution|emotion\s+breakdown|emotional\s+breakdown)\b",
        r"\b(how\s+much\s+anger|how\s+much\s+joy|how\s+much\s+sadness|how\s+much\s+fear|percentage\s+of\s+anger|joy\s+count)\b",
        r"\b(emotions?\s+are\s+present|emotional\s+tone|feelings?|what\s+emotions?)\b",
    ]

    TOPIC_PATTERNS = [
        r"\b(top\s+topics?|topic\s+clusters?|what\s+are\s+the\s+topics?|main\s+topics?|main\s+themes?|top\s+themes?|topic\s+distribution)\b",
        r"\b(what\s+are\s+customers\s+talking\s+about|key\s+topics?|common\s+topics?|frequent\s+topics?|clusters?|which\s+topics?)\b",
    ]

    OVERVIEW_PATTERNS = [
        r"\b(summary|overview|health\s+score|health\s+status|executive\s+summary|how\s+is\s+the\s+dataset|general\s+insights?|overall\s+health)\b",
    ]

    @classmethod
    def route_question(cls, question: str) -> str:
        """
        Routes the user's natural language question into one of the supported question categories.
        """
        q = question.strip().lower()

        # Check for explicit unsupported non-analytical queries
        for pat in cls.UNSUPPORTED_PATTERNS:
            if re.search(pat, q):
                # Ensure it doesn't mention feedback/sentiment/dataset
                if not re.search(r"\b(feedback|sentiment|dataset|review|emotion|topic)\b", q):
                    return QuestionCategory.UNSUPPORTED

        # Specific task categories
        for pat in cls.FEEDBACK_SEARCH_PATTERNS:
            if re.search(pat, q):
                return QuestionCategory.FEEDBACK_SEARCH

        for pat in cls.EXPLANATION_PATTERNS:
            if re.search(pat, q):
                return QuestionCategory.EXPLANATION

        for pat in cls.DATASET_PATTERNS:
            if re.search(pat, q):
                return QuestionCategory.DATASET

        for pat in cls.TREND_PATTERNS:
            if re.search(pat, q):
                return QuestionCategory.TREND

        for pat in cls.CROSS_DIMENSION_PATTERNS:
            if re.search(pat, q):
                return QuestionCategory.CROSS_DIMENSION

        for pat in cls.CATEGORY_PATTERNS:
            if re.search(pat, q):
                return QuestionCategory.CATEGORY

        for pat in cls.SENTIMENT_PATTERNS:
            if re.search(pat, q):
                return QuestionCategory.SENTIMENT

        for pat in cls.EMOTION_PATTERNS:
            if re.search(pat, q):
                return QuestionCategory.EMOTION

        for pat in cls.TOPIC_PATTERNS:
            if re.search(pat, q):
                return QuestionCategory.TOPIC

        for pat in cls.OVERVIEW_PATTERNS:
            if re.search(pat, q):
                return QuestionCategory.OVERVIEW

        # Fallback to OVERVIEW for general analytical queries regarding the dataset
        return QuestionCategory.OVERVIEW
