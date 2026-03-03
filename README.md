# Valuador Inteligente de PH · Córdoba — API

API de predicción de valor fiscal para propiedades horizontales en Córdoba, Argentina.
Stack: **FastAPI + GradientBoosting + Render (free tier)**

Desarrollado en el marco de la **Dirección General de Catastro** en conjunto con **IDECOR**.

---

## Contexto

La Dirección General de Catastro conjuntamente con el programa de Infraestructura de Datos Espaciales de Córdoba (IDECOR) requieren resolver la determinación de la valuación fiscal de los inmuebles bajo el régimen de Propiedades Horizontales (PH), de la cual devendrán los impuestos tributarios.

La metodología vigente presenta una problemática estructural: se basa en sumar la valuación de la tierra y la de las mejoras ajustadas por un coeficiente de comercialización inmobiliario. Este enfoque no construye la valuación fiscal a partir de las características intrínsecas del inmueble, sino que se ajusta a valores externos y no estandarizados. Como consecuencia, se generan resultados que se alejan significativamente del valor real de mercado — tanto por exceso como por defecto — afectando la transparencia y equidad en las operaciones inmobiliarias.

El **Valuador Inteligente de PH** es la solución propuesta: una herramienta basada en inteligencia artificial que integra variables objetivas como la localización, las características constructivas, el entorno urbano y las relaciones espaciales, para ofrecer estimaciones rápidas, confiables y consistentes con la dinámica real del mercado inmobiliario. Mientras la metodología vigente ajusta valores externos mediante coeficientes, este enfoque construye el valor fiscal desde las características objetivas del inmueble y su entorno inmediato.

---

## Estructura del proyecto
```
/
├── main.py                         ← API FastAPI
├── index.html                      ← Interfaz web con mapa interactivo
├── requirements.txt                ← Dependencias
├── render.yaml                     ← Config de deploy en Render
├── datos.csv                       ← Dataset de propiedades
├── modelo.joblib                   ← Modelo entrenado (generado desde el notebook)
├── promedios_features.joblib       ← Promedios de features (ídem)
└── features_order.joblib           ← Orden de columnas (ídem)
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
   - `index.html`
   - `requirements.txt`
   - `render.yaml`
   - `datos.csv`
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
5. Click en **Deploy Web Service** y esperá ~3 minutos

Tu API va a estar viva en una URL del estilo:
`https://diploia6.onrender.com`

---

## Uso de la API

### Endpoint de predicción

**POST** `/predecir`
```bash
curl -X POST "https://diploia6.onrender.com/predecir" \
  -H "Content-Type: application/json" \
  -d '{
    "superficie_mejoras": 80,
    "superficie_mejoras_propias": 65,
    "superficie_mejoras_comunes": 15,
    "antiguedad": 10,
    "puntaje_categoria": "Alto",
    "vut": 900.0,
    "x": 4388379.0,
    "y": 6527032.0
  }'
```

**Respuesta:**
```json
{
  "valor_omi_estimado": 61554604.67,
  "log_valor_omi": 7.789261,
  "mensaje": "Valor estimado: $61.554.604,67 pesos"
}
```

### Verificar estado del servidor

**GET** `/estado`
```json
{
  "estado": "en línea",
  "modelo": "GradientBoosting v2 con mes_num",
  "propiedades_en_base": 15000
}
```

---

## Notas importantes

- **Plan gratuito de Render:** el servicio "duerme" tras 15 minutos de inactividad. La primera request puede tardar ~30 segundos en "despertar".
- **`mes_num`** se fija automáticamente al máximo del período de entrenamiento (el más reciente).
- Los features no ingresados por el usuario se completan con el promedio del dataset de entrenamiento.
- Las coordenadas **X e Y** se seleccionan directamente desde el mapa interactivo en la interfaz.

---

## Licencia

Proyecto desarrollado para la **Dirección General de Catastro de Córdoba** en conjunto con **IDECOR** · Uso institucional interno.
