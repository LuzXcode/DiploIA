from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Literal, Optional
import numpy as np
import joblib
import pandas as pd
import os

# ── Cargar artefactos al inicio ──────────────────────────────────────────────
BASE_DIR = os.path.dirname(__file__)

model          = joblib.load(os.path.join(BASE_DIR, "modelo.joblib"))
promedios      = joblib.load(os.path.join(BASE_DIR, "promedios_features.joblib"))
features_order = joblib.load(os.path.join(BASE_DIR, "features_order.joblib"))

# Cargar el CSV con los datos de propiedades
CSV_PATH = os.path.join(BASE_DIR, "datos.csv")
try:
    df_propiedades = pd.read_csv(CSV_PATH)
    df_propiedades['cuenta'] = df_propiedades['cuenta'].astype(str).str.strip()
    print(f"✅ CSV cargado: {len(df_propiedades)} propiedades")
except Exception as e:
    df_propiedades = None
    print(f"⚠️ No se pudo cargar el CSV: {e}")

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Valuador Inteligente PH · Córdoba",
    description="Predice el valor OMI de una propiedad horizontal en Córdoba, Argentina.",
    version="2.0.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

@app.get("/", include_in_schema=False)
def frontend():
    return FileResponse(os.path.join(BASE_DIR, "index.html"))

# ── Esquemas ──────────────────────────────────────────────────────────────────
class EntradaManual(BaseModel):
    superficie_mejoras: float = Field(..., gt=0, example=100, description="Superficie cubierta en m²")
    superficie_parcela: float = Field(..., gt=0, example=300, description="Superficie total del terreno en m²")
    antiguedad: float         = Field(..., ge=0, example=5,   description="Antigüedad en años")
    puntaje_categoria: Literal["Bajo", "Medio", "Alto", "Muy Alto", "Extremo"] = Field(..., example="Bajo")
    vut: float                = Field(..., gt=0, example=450.0, description="Valor Unitario de Tierra")

class EntradaPorCuenta(BaseModel):
    cuenta: str = Field(..., example="123456", description="Número de cuenta de la propiedad")

class ResultadoPrediccion(BaseModel):
    valor_omi_estimado: float = Field(..., description="Valor OMI estimado en pesos")
    log_valor_omi: float      = Field(..., description="Predicción en escala logarítmica (log10)")
    cuenta: Optional[str]     = Field(None, description="Número de cuenta consultado")
    mensaje: str              = Field(..., description="Descripción del resultado")

# ── Función central de preparación de features ───────────────────────────────
def preparar_features_desde_fila(fila: dict) -> pd.DataFrame:
    datos = {f: promedios.get(f, 0.0) for f in features_order}

    sup_mejoras = fila.get("superficie_mejoras", 0)
    sup_parcela = fila.get("superficie_parcela", 0)

    datos["log_superficie_mejoras"]         = np.log1p(sup_mejoras)
    datos["log_superficie_mejoras_propias"] = np.log1p(fila.get("superficie_mejoras_propias", sup_mejoras))
    datos["log_superficie_mejoras_comunes"] = np.log1p(fila.get("superficie_mejoras_comunes", 0))
    datos["log_superficie_parcela"]         = np.log1p(sup_parcela)
    datos["log_cantidad_cuentas_250"]       = np.log1p(fila.get("cantidad_cuentas_250", 0))

    datos["antiguedad"] = fila.get("antiguedad", promedios.get("antiguedad", 0))
    datos["vut"]        = fila.get("vut",        promedios.get("vut", 0))
    datos["x"]          = fila.get("x",          promedios.get("x", 0))
    datos["y"]          = fila.get("y",          promedios.get("y", 0))

    # One-hot encoding de puntaje_categoria
    for cat in ["Bajo", "Medio", "Alto", "Muy Alto", "Extremo"]:
        col = f"puntaje_categoria_{cat}"
        if col in datos:
            datos[col] = 1 if fila.get("puntaje_categoria") == cat else 0

    datos["mes_num"] = promedios.get("mes_num_max", promedios.get("mes_num", 0))

    return pd.DataFrame([datos])[features_order]


def preparar_features_manual(data: EntradaManual) -> pd.DataFrame:
    fila = {
        "superficie_mejoras": data.superficie_mejoras,
        "superficie_parcela": data.superficie_parcela,
        "antiguedad":         data.antiguedad,
        "puntaje_categoria":  data.puntaje_categoria,
        "vut":                data.vut,
    }
    return preparar_features_desde_fila(fila)


def hacer_prediccion(input_df: pd.DataFrame):
    prediccion_log = float(model.predict(input_df)[0])
    prediccion     = float(10 ** prediccion_log)
    return prediccion, prediccion_log

# ── Endpoints ─────────────────────────────────────────────────────────────────
@app.get("/estado", tags=["Estado"])
def estado():
    propiedades_cargadas = len(df_propiedades) if df_propiedades is not None else 0
    return {
        "estado": "en línea",
        "modelo": "GradientBoosting v2 con mes_num",
        "propiedades_en_base": propiedades_cargadas,
        "descripcion": "Valuador Inteligente de Propiedades Horizontales · Córdoba"
    }


@app.post("/predecir", response_model=ResultadoPrediccion, tags=["Predicción"])
def predecir_manual(data: EntradaManual):
    """Predice el valor OMI ingresando los datos manualmente."""
    try:
        input_df             = preparar_features_manual(data)
        prediccion, pred_log = hacer_prediccion(input_df)
        return ResultadoPrediccion(
            valor_omi_estimado=round(prediccion, 2),
            log_valor_omi=round(pred_log, 6),
            cuenta=None,
            mensaje=f"Valor OMI estimado: ${prediccion:,.2f} pesos"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar la predicción: {str(e)}")


@app.post("/predecir-por-cuenta", response_model=ResultadoPrediccion, tags=["Predicción"])
def predecir_por_cuenta(data: EntradaPorCuenta):
    """Busca la propiedad por número de cuenta y predice su valor OMI automáticamente."""
    if df_propiedades is None:
        raise HTTPException(status_code=503, detail="La base de datos de propiedades no está disponible.")

    cuenta_str = str(data.cuenta).strip()
    fila_df    = df_propiedades[df_propiedades['cuenta'] == cuenta_str]

    if fila_df.empty:
        raise HTTPException(
            status_code=404,
            detail=f"No se encontró ninguna propiedad con el número de cuenta '{cuenta_str}'."
        )

    try:
        fila                 = fila_df.iloc[0].to_dict()
        input_df             = preparar_features_desde_fila(fila)
        prediccion, pred_log = hacer_prediccion(input_df)
        return ResultadoPrediccion(
            valor_omi_estimado=round(prediccion, 2),
            log_valor_omi=round(pred_log, 6),
            cuenta=cuenta_str,
            mensaje=f"Cuenta {cuenta_str} — Valor OMI estimado: ${prediccion:,.2f} pesos"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar la predicción: {str(e)}")


@app.get("/propiedad/{cuenta}", tags=["Consulta"])
def consultar_propiedad(cuenta: str):
    """Devuelve los datos registrados de una propiedad sin predecir."""
    if df_propiedades is None:
        raise HTTPException(status_code=503, detail="La base de datos de propiedades no está disponible.")

    cuenta_str = str(cuenta).strip()
    fila_df    = df_propiedades[df_propiedades['cuenta'] == cuenta_str]

    if fila_df.empty:
        raise HTTPException(
            status_code=404,
            detail=f"No se encontró ninguna propiedad con el número de cuenta '{cuenta_str}'."
        )

    return {
        "cuenta": cuenta_str,
        "datos": fila_df.iloc[0].to_dict()
    }
