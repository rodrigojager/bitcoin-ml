import joblib, pandas as pd
from datetime import datetime
from core.config import settings
from core.db import pg_conn
from core.logging import log_job
from ml.features import build_features_targets, exp_sample_weights, FEATURE_COLS, TARGET_REG_COLS
from ml.model_paths import REG_PATH, CLS_PATH


def load_candles_window(days: int) -> pd.DataFrame:
	with pg_conn() as conn:
		q = """SELECT time, open, high, low, close, volume
			   FROM btc_candles
			   WHERE time >= NOW() - INTERVAL %s
			   ORDER BY time;"""
		return pd.read_sql(q, conn, params=(f'{days} days',))


def mean_absolute_percentage_error(y_true, y_pred):
	import numpy as np
	y_true = np.asarray(y_true)
	y_pred = np.asarray(y_pred)
	den = np.where(y_true == 0, 1e-9, y_true)
	return float((np.abs((y_true - y_pred) / den)).mean() * 100.0)


def symmetric_mape(y_true, y_pred):
	import numpy as np
	y_true = np.asarray(y_true)
	y_pred = np.asarray(y_pred)
	den = (np.abs(y_true) + np.abs(y_pred))
	den = np.where(den == 0, 1e-9, den)
	return float((2.0 * np.abs(y_pred - y_true) / den).mean() * 100.0)


def train_job(days: int|None=None, alpha: float|None=None):
	from xgboost import XGBRegressor, XGBClassifier
	from sklearn.metrics import mean_absolute_error
	import numpy as np

	days = days or settings.LOOKBACK_DAYS
	alpha = alpha or settings.ALPHA_DECAY
	start = datetime.utcnow()
	try:
		df = load_candles_window(days)
		if len(df) < 200: raise RuntimeError("Dados insuficientes para treino.")
		_, X, Yreg, Ycls = build_features_targets(df)

		# Split temporal: 80% treino, 20% validação (últimos pontos)
		n = len(X)
		split_idx = max(int(n * 0.8), n - 500)
		X_train, X_val = X.iloc[:split_idx], X.iloc[split_idx:]
		Yreg_train, Yreg_val = Yreg.iloc[:split_idx], Yreg.iloc[split_idx:]
		Ycls_train, Ycls_val = Ycls.iloc[:split_idx], Ycls.iloc[split_idx:]

		# Pesos exponenciais apenas no treino
		w_train = exp_sample_weights(len(X_train), alpha)

		# Treino de regressão por alvo (sem early stopping por compatibilidade)
		reg_models: dict[str, XGBRegressor] = {}
		for target in TARGET_REG_COLS:
			reg = XGBRegressor(
				n_estimators=400,
				learning_rate=0.05,
				max_depth=6,
				subsample=0.8,
				colsample_bytree=0.8,
				tree_method="hist",
				random_state=42,
			)
			y_tr = Yreg_train[target].values
			reg.fit(X_train, y_tr, sample_weight=w_train)
			reg_models[target] = reg

		# Treino do classificador (sem early stopping por compatibilidade)
		cls = XGBClassifier(
			n_estimators=400,
			learning_rate=0.05,
			max_depth=6,
			subsample=0.8,
			colsample_bytree=0.8,
			tree_method="hist",
			use_label_encoder=False,
			random_state=42,
		)
		cls.fit(X_train, Ycls_train, sample_weight=w_train)

		# Métricas no conjunto de validação para close_next
		y_true = Yreg_val["close_next"].values
		y_pred = reg_models["close_next"].predict(X_val)
		mae = float(mean_absolute_error(y_true, y_pred))
		mape = mean_absolute_percentage_error(y_true, y_pred)
		smape = symmetric_mape(y_true, y_pred)

		# Persistência: salvar regressão como dict e classificador separado
		joblib.dump({"models": reg_models, "feature_cols": FEATURE_COLS}, REG_PATH)
		joblib.dump(cls, CLS_PATH)

		msg = (
			f"Treinado {days}d, n={n}, split={split_idx}/{n}. "
			f"Val close_next -> MAE={mae:.4f}, MAPE={mape:.2f}%, SMAPE={smape:.2f}%"
		)
		log_job("train","ok", msg, start, datetime.utcnow())
		return {"status":"ok","samples":n,"mae":mae,"mape":mape,"smape":smape}
	except Exception as e:
		log_job("train","error",str(e),start,datetime.utcnow())
		return {"status":"error","message":str(e)}
