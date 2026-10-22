from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from backend.app.core.dependencies import get_current_active_verified_user
from backend.app.db.database import get_db
from backend.app.models.user import User
from backend.app.schemas.benchmark import BenchmarkSummaryResponse
from backend.app.services.audit_service import AuditService
from backend.app.services.benchmarking.benchmark_service import BenchmarkService

router = APIRouter(prefix="/benchmarks", tags=["Benchmarking"])


@router.get(
    "/summary",
    response_model=BenchmarkSummaryResponse,
    summary="Get anonymized cross-platform benchmark summary",
)
def get_benchmark_summary(
    request: Request,
    analysis_id: int = Query(..., description="ID of the completed analysis to compare"),
    current_user: User = Depends(get_current_active_verified_user),
    db: Session = Depends(get_db),
):
    """
    Retrieve anonymized aggregate benchmark metrics comparing the user's completed analysis
    against cross-tenant platform aggregates (enforces minimum sample threshold).
    """
    client_ip = request.client.host if request.client else None

    result = BenchmarkService.get_benchmark_summary(
        user=current_user,
        analysis_id=analysis_id,
        db=db,
    )

    AuditService.log_event(
        db=db,
        action="BENCHMARK_ACCESS",
        resource_type="benchmark",
        resource_id=str(analysis_id),
        user_id=current_user.id,
        status="SUCCESS" if result.is_eligible else "INELIGIBLE",
        ip_address=client_ip,
        metadata={
            "analysis_id": analysis_id,
            "is_eligible": result.is_eligible,
            "sample_size": result.eligible_sample_size,
        },
    )

    return result
