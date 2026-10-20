import io
from datetime import datetime
import logging
import traceback
from typing import Optional
import pandas as pd
from sqlalchemy.orm import Session

from backend.app.core.celery_app import celery_app
from backend.app.db.database import SessionLocal
from backend.app.models.analysis import Analysis, AnalysisStage, AnalysisStatus
from backend.app.models.dataset import Dataset
from backend.app.models.feedback_result import FeedbackResult
from backend.app.services.ai.aggregation import calculate_analysis_aggregations
from backend.app.services.ai.embeddings import EmbeddingService, EmbeddingStorage
from backend.app.services.ai.emotion import EmotionService
from backend.app.services.ai.model_registry import ModelRegistry
from backend.app.services.ai.preprocessing import preprocess_feedback_dataset
from backend.app.services.ai.sentiment import SentimentService
from backend.app.services.ai.topics import TopicService
from backend.app.services.storage import LocalStorageService

logger = logging.getLogger(__name__)


def execute_analysis_pipeline(analysis_id: int, db: Optional[Session] = None) -> bool:
    """
    Synchronous analysis pipeline execution engine.
    Can be run directly or from Celery worker.
    """
    close_db_when_done = False
    if db is None:
        db = SessionLocal()
        close_db_when_done = True

    try:
        analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if not analysis:
            logger.error(f"Analysis with ID {analysis_id} not found.")
            return False

        # Update to PROCESSING
        analysis.status = AnalysisStatus.PROCESSING
        analysis.current_stage = AnalysisStage.LOADING
        analysis.progress = 5
        analysis.started_at = datetime.utcnow()
        analysis.error_message = None
        db.commit()

        # Step 1: Load dataset file
        dataset: Dataset = analysis.dataset
        if not dataset:
            raise ValueError(f"Dataset for Analysis {analysis_id} not found.")

        storage = LocalStorageService()
        file_bytes = storage.get_file(dataset.storage_path)
        if not file_bytes:
            raise FileNotFoundError(f"Dataset file at {dataset.storage_path} could not be read.")

        # Read into DataFrame
        if dataset.file_type == "csv":
            df = pd.read_csv(io.BytesIO(file_bytes), encoding_errors="replace")
        else:
            df = pd.read_excel(io.BytesIO(file_bytes))

        feedback_col = dataset.feedback_column
        if not feedback_col or feedback_col not in df.columns:
            raise ValueError(f"Feedback column '{feedback_col}' not found in dataset columns: {list(df.columns)}")

        # Step 2: Preprocessing
        analysis.current_stage = AnalysisStage.PREPROCESSING
        analysis.progress = 15
        analysis.total_feedback_rows = len(df)
        db.commit()

        prep_result = preprocess_feedback_dataset(
            df=df,
            feedback_column=feedback_col,
        )

        analysis.usable_feedback_rows = prep_result.usable_rows
        db.commit()

        if prep_result.usable_rows == 0:
            raise ValueError("No usable feedback text entries were found after preprocessing.")

        valid_items = prep_result.valid_items
        clean_texts = [item.clean_text for item in valid_items]

        # Step 3: Sentiment Analysis
        analysis.current_stage = AnalysisStage.SENTIMENT
        analysis.progress = 30
        db.commit()

        sentiment_service = SentimentService()
        sentiments = sentiment_service.analyze_batch(clean_texts)

        analysis.progress = 50
        db.commit()

        # Step 4: Emotion Classification
        analysis.current_stage = AnalysisStage.EMOTION
        analysis.progress = 55
        db.commit()

        emotion_service = EmotionService()
        emotions = emotion_service.analyze_batch(clean_texts)

        analysis.progress = 70
        db.commit()

        # Step 5: Sentence Embeddings
        analysis.current_stage = AnalysisStage.EMBEDDINGS
        analysis.progress = 75
        db.commit()

        embedding_service = EmbeddingService()
        embeddings = embedding_service.generate_embeddings(clean_texts)

        analysis.progress = 85
        db.commit()

        # Step 6: Topic Discovery (BERTopic)
        analysis.current_stage = AnalysisStage.TOPIC_MODELING
        analysis.progress = 90
        db.commit()

        topic_service = TopicService()
        topic_result = topic_service.discover_topics(clean_texts, embeddings=embeddings)

        analysis.progress = 95
        db.commit()

        # Step 7: Aggregations & Result Persistence
        analysis.current_stage = AnalysisStage.AGGREGATION
        analysis.progress = 97
        db.commit()

        aggregations = calculate_analysis_aggregations(
            sentiments=sentiments,
            emotions=emotions,
            topic_result=topic_result,
        )

        # Model Versioning metadata
        registry = ModelRegistry.get_instance()
        _, _, sentiment_model_name = registry.get_sentiment_pipeline_components()
        _, _, emotion_model_name = registry.get_emotion_pipeline_components()
        _, embedding_model_name = registry.get_embedding_model()
        bertopic_version = registry.get_bertopic_version()

        analysis.sentiment_model = sentiment_model_name
        analysis.emotion_model = emotion_model_name
        analysis.embedding_model = embedding_model_name
        analysis.bertopic_version = bertopic_version

        analysis.sentiment_summary = aggregations["sentiment_summary"]
        analysis.emotion_summary = aggregations["emotion_summary"]
        analysis.topic_summary = aggregations["topic_summary"]
        analysis.topic_info = aggregations["topic_info"]

        # Delete any existing feedback results for this analysis
        db.query(FeedbackResult).filter(FeedbackResult.analysis_id == analysis.id).delete()

        # Prepare FeedbackResult ORM objects
        # Map valid items to ML results
        valid_idx = 0
        db_results = []

        for item in prep_result.items:
            if item.is_valid:
                sent = sentiments[valid_idx]
                emo = emotions[valid_idx]
                top = topic_result.row_topics[valid_idx]
                emb_bytes = EmbeddingStorage.serialize(embeddings[valid_idx])

                result_obj = FeedbackResult(
                    analysis_id=analysis.id,
                    row_index=item.row_index,
                    text_length=item.text_length,
                    sentiment_label=sent.sentiment_label,
                    raw_sentiment_label=sent.raw_sentiment_label,
                    sentiment_score=sent.sentiment_score,
                    emotion_label=emo.emotion_label,
                    emotion_score=emo.emotion_score,
                    emotion_scores=emo.emotion_scores,
                    topic_id=top.topic_id,
                    topic_label=top.topic_label,
                    embedding=emb_bytes,
                    is_valid=True,
                )
                valid_idx += 1
            else:
                result_obj = FeedbackResult(
                    analysis_id=analysis.id,
                    row_index=item.row_index,
                    text_length=item.text_length,
                    sentiment_label=None,
                    raw_sentiment_label=None,
                    sentiment_score=None,
                    emotion_label=None,
                    emotion_score=None,
                    emotion_scores=None,
                    topic_id=None,
                    topic_label=None,
                    embedding=None,
                    is_valid=False,
                )
            db_results.append(result_obj)

        # Bulk save feedback results
        db.bulk_save_objects(db_results)

        # Mark Analysis as COMPLETED
        analysis.status = AnalysisStatus.COMPLETED
        analysis.current_stage = AnalysisStage.COMPLETED
        analysis.progress = 100
        analysis.completed_at = datetime.utcnow()
        analysis.error_message = None

        db.commit()
        logger.info(f"Analysis {analysis_id} completed successfully.")
        return True

    except Exception as e:
        err_msg = str(e)
        logger.error(f"Analysis {analysis_id} failed: {err_msg}\n{traceback.format_exc()}")
        try:
            db.rollback()
            failed_analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
            if failed_analysis:
                failed_analysis.status = AnalysisStatus.FAILED
                failed_analysis.current_stage = AnalysisStage.FAILED
                failed_analysis.error_message = err_msg
                failed_analysis.completed_at = datetime.utcnow()
                db.commit()
        except Exception as rollback_err:
            logger.error(f"Failed to record analysis failure state: {rollback_err}")
        return False

    finally:
        if close_db_when_done:
            db.close()


@celery_app.task(bind=True, name="run_analysis_pipeline")
def run_analysis_pipeline(self, analysis_id: int):
    """
    Celery background task entrypoint.
    """
    logger.info(f"Celery task started for Analysis ID: {analysis_id}")
    return execute_analysis_pipeline(analysis_id)
