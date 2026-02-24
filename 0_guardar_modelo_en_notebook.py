# ============================================================
# PASO 0 — Ejecutá esta celda AL FINAL de tu notebook
# para guardar el modelo y los promedios de features.
# Luego descargá los 2 archivos generados.
# ============================================================

import joblib
import numpy as np

# Guardar el modelo entrenado
joblib.dump(gb_v2, "modelo.joblib")
print("✅ modelo.joblib guardado")

# Guardar los promedios de features (para rellenar valores por defecto)
promedios = X2.mean().to_dict()
promedios['mes_num_max'] = int(df['mes_num'].max())  # también guardamos el mes máximo
joblib.dump(promedios, "promedios_features.joblib")
print("✅ promedios_features.joblib guardado")

# Guardar la lista de features en el orden correcto
joblib.dump(list(FEATURES_PLUS), "features_order.joblib")
print("✅ features_order.joblib guardado")

print("\n📥 Ahora descargá los 3 archivos desde el panel de archivos de Colab:")
print("   - modelo.joblib")
print("   - promedios_features.joblib")
print("   - features_order.joblib")
