#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script que ejecuta el flujo completo: producto → suma → resultado_final.
Flujo: input.json (múltiples expresiones) → reducir_grado_producto (si es necesario) → suma_fracciones → resultado_final.json
"""

import json
import argparse
import sys
from pathlib import Path

# Importar módulos de producto y suma
try:
    import producto_genera_multiopcion_min_vars as prod_module
    import suma_fracciones_multiopcion as suma_fracciones
except ImportError as e:
    print(f"Error: No se puede importar módulos necesarios: {e}")
    sys.exit(1)


def ejecutar_producto(grado_num, grado_den, maxDeg, id_fraccion=0):
    
    print(f"Ejecutando producto para fracción {id_fraccion}...")
    print(f"  Grado numerador: {grado_num}, Grado denominador: {grado_den}")
    
    # Llamar la función del módulo de producto
    prod_module.reducir_grado_producto(maxDeg, grado_num, grado_den, id_fraccion)
    
    # Leer el archivo prod.json generado
    with open("prod.json", 'r') as f:
        prod_data = json.load(f)
    
    return prod_data


def adaptar_producto_a_suma(prod_data, maxDeg):

    fracciones = []
    indices_originales = []
    
    # Si hay opciones múltiples (producto_genera_multiopcion)
    if "opciones" in prod_data:
        for idx, opcion in enumerate(prod_data["opciones"]):
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
            indices_originales.append(idx)
    
    # Si hay una sola solución (producto_genera_multiopcion_sin_grado_minimo)
    else:
        grado_num = prod_data["degree_numerator"]
        grado_den = prod_data["degree_denominator"]
        
        num = prod_data["product"]["numerator"]
        den = prod_data["product"]["denominator"]
        
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
        indices_originales.append(0)
    
    return fracciones, indices_originales


def factor_original(origen, fraccion, cantidad):
    return {
        "origen": origen,
        "fraccion": fraccion,
        "cantidad": cantidad
    }


def procesar_suma(fracciones, indices_originales, maxDeg, total_vi_producto):

    print("Ejecutando suma_fracciones...\n")
    resultado_suma = suma_fracciones.suma_fracciones_multiopcion(maxDeg, maxDeg - 1, fracciones, indices_originales)
    
    grupos = resultado_suma["groups"]
    total_vi_suma = resultado_suma.get("total_vi_created_in_sum", 0)
    
    print("\n--- Resultado de sumas ---")
    for g in grupos:
        frs = g["fractions"]
        vi_info = f" → crea 1 VI" if g["vi_created"] == 1 else " → NO crea VI"
        cadena = " + ".join(f"fracción {f}" for f in frs)
        print(f"sum{g['sum']} = {cadena}{vi_info}")

    total_vi_created = total_vi_producto + total_vi_suma
    
    resultado_final = {
        "total_vi_created": total_vi_created,
        "vi_from_product": total_vi_producto,
        "vi_from_sum": total_vi_suma,
        "sum_groups": grupos,
        "sum_options": resultado_suma.get("options", [])
    }
    
    return resultado_final

parser = argparse.ArgumentParser()
parser.add_argument("filein", type=str)

parser.add_argument(
    "-o", "--output",
    default="resultado_final.json",
    help="Ruta del archivo de salida (default: resultado_final.json)"
)

args = parser.parse_args()

with open(args.filein, 'r') as f:
    data = json.load(f)

expresiones = data["expressions"]
maxDeg = data["degree"]

print(f"Se encontraron {len(expresiones)} expresión(es)")
print(f"Grado máximo permitido: {maxDeg}\n")

fracciones_finales = []
total_vi_producto = 0

for idx, expr in enumerate(expresiones):
    grado_num = expr["values"][0]["degree"]
    grado_den = expr["values"][1]["degree"]
    
    print(f"Procesando expresión {idx}: grado_num={grado_num}, grado_den={grado_den}")
    
    # Si se pasa de grado, ejecutar producto
    if grado_num > maxDeg or grado_den >= maxDeg:
        print(f"  → Se pasa de grado, ejecutando PRODUCTO...\n")
        
        prod_data = ejecutar_producto(grado_num, grado_den, maxDeg, idx)
        print(f"  ✓ Producto ejecutado correctamente\n")
        
        if "opciones" in prod_data:
            lista_vi = prod_data["opciones"][0].get("intermediate_variables", [])
        else:
            lista_vi = prod_data.get("intermediate_variables", [])
        total_vi_producto += len(lista_vi)
        
        fracciones_adaptadas, _ = adaptar_producto_a_suma(prod_data, maxDeg)
        for frac in fracciones_adaptadas:
            fracciones_finales.append([frac])

    # NO se pasa de grado
    else:
        print(f"  → NO se pasa de grado, se mantiene como está\n")
        fracciones_finales.append([expr])

print(f"Ejecutando suma...\n")
print(f"Total de fracciones a sumar: {len(fracciones_finales)}\n")

resultado = procesar_suma(fracciones_finales, list(range(len(fracciones_finales))), maxDeg, total_vi_producto)
print()

with open("resultado_final.json", "w") as fout:
    json.dump(resultado, fout, indent=4)

print("File 'resultado_final.json' generated correctly.")
print(f"Total de VI creadas: {resultado['total_vi_created']}")