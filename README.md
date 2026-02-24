# Valuador Inteligente PH · Córdoba — API

API de predicción de valor_omi para propiedades horizontales en Córdoba, Argentina.  
Stack: **FastAPI + GradientBoosting + Render (free tier)**

---

## Estructura del proyecto

```
/
├── main.py                      ← API FastAPI
├── requirements.txt             ← Dependencias
├── render.yaml                  ← Config de deploy en Render
├── modelo.joblib                ← Modelo entrenado (lo generás vos desde el notebook)
├── promedios_features.joblib    ← Promedios de features (ídem)
└── features_order.joblib        ← Orden de columnas (ídem)
```

---

## PASO 1 — Guardar el modelo desde el notebook

Agregá esta celda **al final** de tu notebook de Google Colab y ejecutala:

```python
# (el contenido está en 0_guardar_modelo_en_notebook.py)
```

Descargá los 3 archivos generados:
- `modelo.joblib`
- `promedios_features.joblib`  
- `features_order.joblib`

---

## PASO 2 — Armar el repositorio

1. Creá una cuenta en [GitHub](https://github.com) si no tenés
2. Creá un repositorio nuevo (público o privado)
3. Subí todos estos archivos al repo:
   - `main.py`
   - `requirements.txt`
   - `render.yaml`
   - `modelo.joblib`
   - `promedios_features.joblib`
   - `features_order.joblib`

> **Tip:** Los archivos `.joblib` pueden ser grandes. Si superan 100 MB usá [Git LFS](https://git-lfs.github.com/).

---

## PASO 3 — Deploy en Render

1. Entrá a [render.com](https://render.com) y creá una cuenta gratis
2. Click en **New → Web Service**
3. Conectá tu cuenta de GitHub y seleccioná el repositorio
4. Render va a detectar el `render.yaml` automáticamente
5. Click en **Deploy** y esperá ~3 minutos

Tu API va a quedar en: `https://valuador-ph-cordoba.onrender.com`

---

## Uso de la API

### Endpoint de predicción

**POST** `/predecir`

```bash
curl -X POST "https://valuador-ph-cordoba.onrender.com/predecir" \
  -H "Content-Type: application/json" \
  -d '{
    "superficie_mejoras": 100,
    "superficie_parcela": 300,
    "antiguedad": 5,
    "puntaje_categoria": "Bajo",
    "vut": 450.0
  }'
```

**Respuesta:**
```json
{
  "valor_omi_estimado": 12345678.90,
  "log_valor_omi": 7.091543,
  "inputs_usados": { ... }
}
```

### Documentación interactiva (Swagger)

Disponible en: `https://valuador-ph-cordoba.onrender.com/docs`

---

## Notas importantes

- **Plan gratuito de Render:** el servicio "duerme" tras 15 minutos de inactividad. La primera request puede tardar ~30 segundos en "despertar".
- **`mes_num`** se fija automáticamente al máximo del período de entrenamiento (el más reciente).
- Los features no ingresados por el usuario se completan con el promedio del dataset de entrenamiento.
