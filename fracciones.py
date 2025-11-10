
# Suma de fracciones -> primero se solucionan las fracciones que se pasan del grado máximo y luego se reduce el grado de la suma

# Pasar a js: ver si la suma funciona la versión que hay hecha en js + pasar producto_nuevo a js + pasar fracciones.py a js con las llamadas
# Documentar variables + procedimiento de los 3 ficheros

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

def ejecutar_producto(grado_num, grado_den, maxDeg, max_intermedias):
    prod_fracciones_nuevo.reducir_grado_producto(maxDeg, grado_num, grado_den) # max_intermedias

    with open("prod.json", "r") as f:
        prod_reducido = json.load(f)

    return prod_reducido

# -----------------------------------------------------------
#  Adaptar salida del producto a formato suma_fracciones
# -----------------------------------------------------------

# Construir las "señales" del numerador y denominador
def construir_signals(componentes, num_originales):
    señales = []
    for comp in componentes:
        señales.append(comp["nombre"])
    for i in range(num_originales):
        señales.append(f"x_orig_{i+1}")
    return señales

def adaptar_a_suma(prod_reducido, maxDeg):
    """
    Convierte la salida del producto (prod.json) en un formato compatible
    con suma_fracciones_v1_2.suma_fracciones
    """

    grado_num = prod_reducido["grado_numerador_total"]
    grado_den = prod_reducido["grado_denominador_total"]

    num_vars_orig = prod_reducido["producto"]["numerador"].get("variables_originales", 0)
    den_vars_orig = prod_reducido["producto"]["denominador"].get("variables_originales", 0)

    num_comps = prod_reducido["producto"]["numerador"].get("componentes", [])
    den_comps = prod_reducido["producto"]["denominador"].get("componentes", [])

    signals_num = construir_signals(num_comps, num_vars_orig)
    signals_den = construir_signals(den_comps, den_vars_orig)

    # Crear entrada para suma_fracciones
    fraccion_equivalente = {
        "op": "frac",
        "values": [
            {"signals": signals_num, "degree": grado_num},
            {"signals": signals_den, "degree": grado_den}
        ]
    }

    entrada_suma = {
        "expressions": [fraccion_equivalente],
        "degree": maxDeg
    }

    return entrada_suma

parser = argparse.ArgumentParser()
parser.add_argument("filein", type=str)
args = parser.parse_args()

with open(args.filein) as f:
    data = json.load(f)

expresiones = data["expressions"]
maxDeg = data["degree"]
max_intermedias = 5

fracciones = []
vi_utilizadas = 0

for idx, frac in enumerate(expresiones):
    grado_num = frac["values"][0]["degree"]
    grado_den = frac["values"][1]["degree"]

    if grado_num > maxDeg or grado_den > maxDeg:
        print(f"Ejecutando producto sobre la fracción {idx}...")
        prod_reducido = ejecutar_producto(grado_num, grado_den, maxDeg, max_intermedias)

        vi_utilizadas += len(prod_reducido["variables_intermedias"])

        # Adaptar la salida del producto a la entrada de suma_fracciones
        fraccion_adaptada = adaptar_a_suma(prod_reducido, maxDeg)

        # Extraer la fracción equivalente (solo la primera, porque es una sola en expressions)
        fracciones.append(fraccion_adaptada["expressions"][0])

    else:
        fracciones.append(frac)

print("Ejecutando suma_fracciones_v1_2...\n")
vi_utilizadas += suma_fracciones_v1_2.suma_fracciones(maxDeg, fracciones)

print(f"\nEn total se han utilizado {vi_utilizadas} variables intermedias")