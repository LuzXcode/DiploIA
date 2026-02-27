from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Literal, Optional
import numpy as np
import joblib
import pandas as pd
import os

BASE_DIR = os.path.dirname(__file__)

model          = joblib.load(os.path.join(BASE_DIR, "modelo.joblib"))
promedios      = joblib.load(os.path.join(BASE_DIR, "promedios_features.joblib"))
features_order = joblib.load(os.path.join(BASE_DIR, "features_order.joblib"))

app = FastAPI(
    title="Valuador Inteligente PH · Córdoba",
    version="3.0.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

@app.get("/", include_in_schema=False)
def frontend():
    return FileResponse(os.path.join(BASE_DIR, "index.html"))

@app.get("/estado")
def estado():
    return {
        "estado": "en línea",
        "modelo": "GradientBoosting v2 con mes_num",
    }

class EntradaManual(BaseModel):
    superficie_mejoras:         float          = Field(..., gt=0, example=80)
    superficie_mejoras_propias: Optional[float]= Field(None,      example=65)
    superficie_mejoras_comunes: Optional[float]= Field(None,      example=15)
    superficie_parcela:         Optional[float]= Field(None,      example=300)
    antiguedad:                 float          = Field(..., ge=0, example=10)
    puntaje_categoria: Literal["Bajo", "Medio", "Alto", "Muy Alto", "Extremo"] = Field(..., example="Alto")
    vut:  float          = Field(..., gt=0, example=900.0)
    x:    Optional[float]= Field(None,      example=4388379.0)
    y:    Optional[float]= Field(None,      example=6527032.0)

class ResultadoPrediccion(BaseModel):
    valor_omi_estimado: float
    log_valor_omi:      float
    mensaje:            str

def preparar_features(data: EntradaManual) -> pd.DataFrame:
    datos = {f: promedios.get(f, 0.0) for f in features_order}

    datos["log_superficie_mejoras"]         = np.log1p(data.superficie_mejoras)
    datos["log_superficie_mejoras_propias"] = np.log1p(data.superficie_mejoras_propias or data.superficie_mejoras)
    datos["log_superficie_mejoras_comunes"] = np.log1p(data.superficie_mejoras_comunes or 0)
    datos["log_superficie_parcela"]         = np.log1p(data.superficie_parcela or data.superficie_mejoras)
    datos["antiguedad"] = data.antiguedad
    datos["vut"]        = data.vut
    datos["x"]          = data.x if data.x is not None else promedios.get("x", 0)
    datos["y"]          = data.y if data.y is not None else promedios.get("y", 0)

    for cat in ["Bajo", "Medio", "Alto", "Muy Alto", "Extremo"]:
        col = f"puntaje_categoria_{cat}"
        if col in datos:
            datos[col] = 1 if data.puntaje_categoria == cat else 0

    datos["mes_num"] = promedios.get("mes_num_max", promedios.get("mes_num", 0))

    return pd.DataFrame([datos])[features_order]

@app.post("/predecir", response_model=ResultadoPrediccion)
def predecir(data: EntradaManual):
    try:
        input_df       = preparar_features(data)
        pred_log       = float(model.predict(input_df)[0])
        pred_valor     = float(10 ** pred_log)
        return ResultadoPrediccion(
            valor_omi_estimado=round(pred_valor, 2),
            log_valor_omi=round(pred_log, 6),
            mensaje=f"Valor OMI estimado: ${pred_valor:,.2f} pesos"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
