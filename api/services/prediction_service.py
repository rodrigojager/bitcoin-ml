import joblib, numpy as np, pandas as pd
from typing import Optional
from core.db import pg_conn
from ml.features import build_features_targets, TARGET_REG_COLS
from ml.model_paths import REG_PATH, CLS_PATH


def load_models():
	return joblib.load(REG_PATH), joblib.load(CLS_PATH)


def _predict_regressors(reg_bundle, X: pd.DataFrame) -> pd.DataFrame:
	"""Suporta tanto o formato antigo (um único modelo multi-saída) quanto o novo (dict por alvo)."""
	# Formato novo: um dicionário com vários modelos
	if isinstance(reg_bundle, dict) and "models" in reg_bundle:
		preds = {}
		for target in TARGET_REG_COLS:
			model = reg_bundle["models"].get(target)
			if model is None:
				preds[target] = np.full((len(X),), np.nan)
			else:
				preds[target] = model.predict(X)
		return pd.DataFrame(preds, index=X.index)
	# Formato antigo: modelo único, .predict() retorna uma matriz com várias colunas (uma por target)
	else:
		arr = reg_bundle.predict(X)
		return pd.DataFrame(arr, columns=TARGET_REG_COLS, index=X.index)


def series_data(start: Optional[str], end: Optional[str], fallback_days: int=90):
	with pg_conn() as conn:
		if start and end:
			q = """SELECT time, open, high, low, close, volume FROM btc_candles
				   WHERE time BETWEEN %s AND %s ORDER BY time;"""
			df = pd.read_sql(q, conn, params=(start,end))
		else:
			q = """SELECT time, open, high, low, close, volume FROM btc_candles
				   WHERE time >= NOW() - INTERVAL %s ORDER BY time;"""
			df = pd.read_sql(q, conn, params=(f'{fallback_days} days',))
	if df.empty or len(df) < 30: return {"points":[]}

	df2, X, Yreg, Ycls = build_features_targets(df)
	try:
		reg_bundle, cls = load_models()
		reg_pred = _predict_regressors(reg_bundle, X)
		cls_pred = cls.predict(X); prob = cls.predict_proba(X)
	except Exception:
		reg_pred = cls_pred = prob = None

	out = []
	for i in range(len(df2)):
		real = {k: (float(df2.iloc[i][k]) if k!="time" else df2.iloc[i]["time"].isoformat())
				for k in ["time","open","high","low","close","volume"]}
		pred = {k: float(reg_pred.iloc[i][k]) for k in TARGET_REG_COLS} if reg_pred is not None else None
		clsinfo = ({"dir_next": int(cls_pred[i]), "prob_up": float(prob[i][1]), "prob_down": float(prob[i][0])}
				   if cls_pred is not None else None)
		err = None
		if pred is not None and i+1 < len(df2):
			real_next_close = float(df2.iloc[i+1]["close"])
			real_next_amp = float(df2.iloc[i+1]["high"] - df2.iloc[i+1]["low"])
			err = {
				"close_abs": abs(pred["close_next"] - real_next_close),
				"close_signed": pred["close_next"] - real_next_close,
				"amp_abs": abs(pred["amp_next"] - real_next_amp)
			}
		out.append({"real": real, "pred": pred, "cls": clsinfo, "err": err})
	return {"points": out}
