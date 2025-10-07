from fastapi import APIRouter
from services.ingestion_service import fetch_binance_klines, upsert_candles
from services.futures_service import save_predictions_for_times
from core.logging import log_job
from datetime import datetime
from models.schemas import IngestResponse

router = APIRouter(prefix="/ingest", tags=["ingest"])

@router.post("", response_model=IngestResponse, summary="Ingestão de candles recentes", description="Busca klines na Binance e upserta em btc_candles. Atualiza a série prospectiva 'futuros' para o último timestamp válido.")
def ingest():
	start = datetime.utcnow()
	try:
		df = fetch_binance_klines()
		inserted = upsert_candles(df)
		# Usar penúltimo timestamp (tem par com T-1 nas features)
		last_valid_time = df["time"].iloc[-2] if len(df) >= 2 else None
		updated = save_predictions_for_times([last_valid_time]) if last_valid_time is not None else 0
		log_job("ingest","ok",f"Inserted {inserted}; futures_updated {updated}",start,datetime.utcnow())
		return {"status":"ok","inserted":inserted, "futures_updated": updated}
	except Exception as e:
		log_job("ingest","error",str(e),start,datetime.utcnow())
		return {"status":"error","message":str(e)}
