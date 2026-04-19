#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import argparse
import sys
from pathlib import Path

try:
    import producto_genera_multiopcion_min_vars as prod_module
    import suma_fracciones_multiopcion as suma_module
except ImportError as e:
    print(f"Error: Cannot import required modules: {e}")
    sys.exit(1)


def ejecutar_producto(grado_num, grado_den, maxDeg, id_fraccion=0):
    print(f"Executing product for fraction {id_fraccion}...")
    print(f"  Numerator degree: {grado_num}, Denominator degree: {grado_den}")
    
    prod_module.reducir_grado_producto(maxDeg, grado_num, grado_den, id_fraccion)
    
    with open("prod.json", 'r') as f:
        prod_data = json.load(f)
    
    return prod_data


def adaptar_producto_a_suma(prod_data, maxDeg):
    fracciones = []
    
    if "options" in prod_data:
        for opcion in prod_data["options"]:
            grado_num = opcion["degree_numerator"]
            grado_den = opcion["degree_denominator"]
            
            num = opcion["product"]["numerator"]
            den = opcion["product"]["denominator"]
            
            comps_num = list(num["intermediate"])
            if num["orig_num"] > 0:
                comps_num.append(f"orig_n_{num['orig_num']}")
            if num["orig_den"] > 0:
                comps_num.append(f"orig_d_{num['orig_den']}")
            
            comps_den = list(den["intermediate"])
            if den["orig_num"] > 0:
                comps_den.append(f"orig_n_{den['orig_num']}")
            if den["orig_den"] > 0:
                comps_den.append(f"orig_d_{den['orig_den']}")
            
            fraccion = {
                "op": "frac",
                "values": [
                    {"signals": comps_num, "degree": grado_num},
                    {"signals": comps_den, "degree": grado_den}
                ]
            }
            
            fracciones.append(fraccion)
    
    return fracciones


parser = argparse.ArgumentParser()
parser.add_argument("filein", type=str)
parser.add_argument(
    "-o", "--output",
    default="resultado_final.json",
    help="Output file path (default: resultado_final.json)"
)

args = parser.parse_args()

with open(args.filein, 'r') as f:
    data = json.load(f)

expresiones = data["expressions"]
maxDeg = data["degree"]

print(f"Found {len(expresiones)} expression(s)")
print(f"Maximum allowed degree: {maxDeg}\n")

fracciones_finales = []
total_vi_producto = 0

for idx, expr in enumerate(expresiones):
    grado_num = expr["values"][0]["degree"]
    grado_den = expr["values"][1]["degree"]
    
    print(f"Processing expression {idx}: degree_num={grado_num}, degree_den={grado_den}")
    
    if grado_num > maxDeg or grado_den >= maxDeg:
        print(f"  -> Exceeds max degree, executing PRODUCT...\n")
        
        prod_data = ejecutar_producto(grado_num, grado_den, maxDeg, idx)
        
        lista_vi = []
        if "options" in prod_data and len(prod_data["options"]) > 0:
            for opcion in prod_data["options"]:
                lista_vi.extend(opcion.get("intermediate_variables", []))
        
        total_vi_producto += len(lista_vi)
        
        fracciones_adaptadas = adaptar_producto_a_suma(prod_data, maxDeg)
        fracciones_finales.append(fracciones_adaptadas)

    else:
        fracciones_finales.append([expr])

print(f"\nExecuting sum_fracciones...\n")

resultado_suma = suma_module.suma_fracciones_multiopcion(maxDeg, maxDeg - 1, fracciones_finales)

grupos = resultado_suma["groups"]
total_vi_suma = resultado_suma.get("total_vi_created_in_sum", 0)

print("\n--- Sum results ---")
for g in grupos:
    frs = g["fractions"]
    vi_info = "-> creates 1 VI" if g["vi_created"] == 1 else "-> does NOT create VI"
    cadena = " + ".join(f"fraction {f}" for f in frs)
    print(f"sum{g['sum']} = {cadena} {vi_info}")

total_vi_created = total_vi_producto + total_vi_suma

resultado_final = {
    "total_vi_created": total_vi_created,
    "vi_from_product": total_vi_producto,
    "vi_from_sum": total_vi_suma,
    "sum_groups": grupos,
    "sum_options": resultado_suma.get("options", [])
}

with open(args.output, "w") as fout:
    json.dump(resultado_final, fout, indent=4)

print(f"\nFile '{args.output}' generated correctly.")
print(f"Total VI created: {resultado_final['total_vi_created']}")