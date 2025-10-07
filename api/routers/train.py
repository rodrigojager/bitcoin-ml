from fastapi import APIRouter, Query
from services.training_service import train_job
from services.series_cache_service import build_series_cache
from models.schemas import TrainResponse

router = APIRouter(prefix="/train", tags=["train"])

@router.post("", response_model=TrainResponse, summary="Treino de modelos (XGB)", description="Treina regressões para OHLC/amp e classificador de direção, com split temporal 80/20. Retorna métricas de validação para close_next.")
def train(days: int = Query(90, ge=1, le=90)):
    return train_job(days=days)


@router.post("/apply", summary="Materializa série consolidada pós-treino")
def apply_series(days: int = Query(90, ge=1, le=90)):
    n = build_series_cache(days)
    return {"status":"ok","materialized": n}
