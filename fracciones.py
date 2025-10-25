
# Suma de fracciones -> primero se solucionan las fracciones que se pasan del grado máximo y luego se reduce el grado de la suma

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from z3 import *
import argparse
import prod_fracciones_nuevo
import suma_fracciones_v1_2

def addsum(a):
    if len(a) == 0:
        return IntVal(0)
    else:
        asum = a[0]
        for i in range(1, len(a)):
            asum = asum + a[i]
        return asum


# -----------------------------------------------------------
# 🔹 Función: Ejecutar producto (reducción de grado)
# -----------------------------------------------------------
def ejecutar_producto(grado_num, grado_den, maxDeg, max_intermedias):
    prod_fracciones_nuevo.reducir_grado_producto(max_intermedias, maxDeg, grado_num, grado_den)

    with open("prod.json", "r") as f:
        prod_reducido = json.load(f)

    return prod_reducido


# -----------------------------------------------------------
# 🔹 Función: Adaptar salida del producto a formato suma_fracciones
# -----------------------------------------------------------
def adaptar_a_suma(prod_reducido, maxDeg):
    """
    Convierte la salida del producto (prod.json) en un formato compatible
    con suma_fracciones_v1_2.suma_fracciones.
    """

    grado_num = prod_reducido["grado_numerador_total"]
    grado_den = prod_reducido["grado_denominador_total"]

    num_vars_orig = prod_reducido["producto"]["numerador"].get("variables_originales", 0)
    den_vars_orig = prod_reducido["producto"]["denominador"].get("variables_originales", 0)

    num_comps = prod_reducido["producto"]["numerador"].get("componentes", [])
    den_comps = prod_reducido["producto"]["denominador"].get("componentes", [])

    # Construir las "señales" del numerador y denominador
    def construir_signales(componentes, num_originales):
        señales = []
        for comp in componentes:
            señales.append(comp["nombre"])
        for i in range(num_originales):
            señales.append(f"x_orig_{i+1}")
        return señales

    signals_num = construir_signales(num_comps, num_vars_orig)
    signals_den = construir_signales(den_comps, den_vars_orig)

    # Crear estructura compatible con suma_fracciones
    fraccion_equivalente = {
        "op": "frac",
        "values": [
            {"signals": signals_num, "degree": grado_num},
            {"signals": signals_den, "degree": grado_den}
        ]
    }

    # Empaquetar en estructura de entrada válida
    entrada_suma = {
        "expressions": [fraccion_equivalente],
        "degree": maxDeg
    }

    return entrada_suma

# -----------------------------------------------------------
# 🔹 Programa principal
# -----------------------------------------------------------
parser = argparse.ArgumentParser()
parser.add_argument("filein", type=str)
args = parser.parse_args()

with open(args.filein) as f:
    data = json.load(f)

expresiones = data["expressions"]
maxDeg = data["degree"]
max_intermedias = 5

fracciones = []

# -----------------------------------------------------------
# Paso 1️⃣ Reducir fracciones que se pasen de maxDeg
# -----------------------------------------------------------
for idx, frac in enumerate(expresiones):
    grado_num = frac["values"][0]["degree"]
    grado_den = frac["values"][1]["degree"]

    if grado_num > maxDeg or grado_den > maxDeg:
        print(f"⚙️ Ejecutando producto sobre la fracción {idx} ({grado_num}/{grado_den})...")
        prod_reducido = ejecutar_producto(grado_num, grado_den, maxDeg, max_intermedias)
        # print(prod_reducido)

        # Adaptar la salida del producto al formato esperado por suma_fracciones
        print("🔄 Adaptando salida del producto a formato suma_fracciones...")
        fraccion_adaptada = adaptar_a_suma(prod_reducido, maxDeg)

        # Extraer la fracción equivalente (solo la primera, porque es una sola en expressions)
        fracciones.append(fraccion_adaptada["expressions"][0])
        print("✅ Fracción reducida adaptada correctamente.\n")

    else:
        fracciones.append(frac)

# -----------------------------------------------------------
# Paso 2️⃣ Ejecutar suma_fracciones con todas las fracciones resultantes
# -----------------------------------------------------------
print("🚀 Ejecutando suma_fracciones_v1_2 sobre las fracciones finales...\n")
suma_fracciones_v1_2.suma_fracciones(maxDeg, fracciones)
