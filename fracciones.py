
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

def ejecutar_producto(grado_num, grado_den, maxDeg, id):
    prod_fracciones_nuevo.reducir_grado_producto(maxDeg, grado_num, grado_den, id) # max_intermedias

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

fracciones = []
vi_utilizadas_total = 0
variables_intermedias = []
fracciones_producto = []

for idx, frac in enumerate(expresiones):
    grado_num = frac["values"][0]["degree"]
    grado_den = frac["values"][1]["degree"]

    # ------------------------------------
    # CASO 1: se pasa de grado → usar prod.json
    # ------------------------------------
    if grado_num > maxDeg or grado_den > maxDeg:

        print(f"Ejecutando producto sobre la fracción {idx}...")
        prod_reducido = ejecutar_producto(grado_num, grado_den, maxDeg, idx)

        vi_dict = prod_reducido["variables_intermedias"]
        vi_utilizadas_total += len(vi_dict)

        # --- mapear todas las VI a nombres globales ---
        vi_global_map = {}  # map local_name -> global_name
        for k, vi_local in enumerate(vi_dict.keys()):
            vi_global = f"VI_{idx}_{k}"
            variables_intermedias.append({vi_global: vi_dict[vi_local]})
            vi_global_map[vi_local] = vi_global

        # --- producto numerador y denominador solo con VI que se usan ---
        numerador_componentes = [vi_global_map[comp["nombre"]] 
                         for comp in prod_reducido["producto"]["numerador"]["componentes"]]
        denominador_componentes = [vi_global_map[comp["nombre"]] 
                           for comp in prod_reducido["producto"]["denominador"]["componentes"]]
        # --- variables originales ---
        num_orig_count = prod_reducido["producto"]["numerador"].get("variables_originales", 0)
        den_orig_count = prod_reducido["producto"]["denominador"].get("variables_originales", 0)

        orig_num = f"orig_{idx}_0_{num_orig_count}" if num_orig_count > 0 else []
        orig_den = f"orig_{idx}_1_{den_orig_count}" if den_orig_count > 0 else []

        if num_orig_count > 0: numerador_componentes.append(orig_num)
        if den_orig_count > 0: denominador_componentes.append(orig_den)

        comp_num = numerador_componentes  # ahora lista plana de strings
        comp_den = denominador_componentes

        fracciones_producto.append({
            "fraccion": idx,
            "numerador": comp_num,
            "denominador": comp_den
        })

        # --- adaptar para suma_fracciones ---
        fraccion_adaptada = adaptar_a_suma(prod_reducido, maxDeg)
        fracciones.append(fraccion_adaptada["expressions"][0])

    # ------------------------------------
    # CASO 2: NO se pasa de grado → queda como está
    # ------------------------------------
    else:
        fracciones.append(frac)

        # señales originales
        num_signals = grado_num
        den_signals = grado_den

        # generar numeración orig_idx_lado_k
        orig_num = f"orig_{idx}_0_{num_signals}"
        orig_den = f"orig_{idx}_1_{den_signals}"

        fracciones_producto.append({
            "fraccion": idx,
            "numerador": orig_num,
            "denominador": orig_den
        })


print("Ejecutando suma_fracciones_v1_2...\n")

# Ejecuta la suma y obtiene los grupos
grupos = suma_fracciones_v1_2.suma_fracciones(maxDeg, fracciones)
# grupos = [ { "suma": k, "fracciones": [i,j,...] }, ... ]

# -------------------------------
# Calcular cuántas VI se necesitan realmente
# -------------------------------
total_vi_creadas = 0

print("\n--- Resultado de sumas ---")
for g in grupos:
    frs = g["fracciones"]
    cadena = " + ".join(f"fracción {f}" for f in frs)
    print(f"suma{g['suma']} = {cadena}")

    nombre_vi = f"VI_S_{total_vi_creadas}"

    variables_intermedias.append({
        nombre_vi: {
            "tipo": "suma",
            "fracciones": frs
        }
    })

    total_vi_creadas += 1

print("\nTotal de VI creadas en la suma =", total_vi_creadas)
vi_utilizadas_total += total_vi_creadas
print("\nTotal de VI creadas =", vi_utilizadas_total)

# -------------------------------------
# Construir JSON FINAL
# -------------------------------------
resultado = {
    "variables_intermedias": variables_intermedias,
    "fracciones_producto": fracciones_producto,
    "resultado_final": [f"VI_S_{i}" for i in range(len(grupos))],
    "total_vi_creadas": vi_utilizadas_total
}

# Guardarlo
with open("resultado_final.json", "w") as fout:
    json.dump(resultado, fout, indent=4)

print("\nArchivo 'resultado_final.json' generado correctamente.")