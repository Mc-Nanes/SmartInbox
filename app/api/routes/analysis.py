from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from app.core.exceptions import AppBaseException
from app.schemas.analysis import AnalysisResponse
from app.services.analysis_orchestrator import AnalysisOrchestratorService

router = APIRouter(prefix="/api/v1", tags=["analysis"])


@router.post("/analyze", response_model=AnalysisResponse, status_code=status.HTTP_200_OK)
async def analyze_email(
    text: str | None = Form(default=None),
    file: UploadFile | None = File(default=None),
) -> AnalysisResponse:
    service = AnalysisOrchestratorService()

    try:
        return await service.analyze(text=text, upload_file=file)
    except AppBaseException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
