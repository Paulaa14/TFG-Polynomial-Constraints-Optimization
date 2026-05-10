#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import argparse
import sys
from pathlib import Path
import multioption_fractions_variables_minimizing
import multioption_fractions_sum
    
def factor_original(origen, fraccion, cantidad):
    return {
        "origen": origen,
        "fraccion": fraccion,
        "cantidad": cantidad
    }

def ejecutar_producto(grado_num, grado_den, maxDeg, id):
    multioption_fractions_variables_minimizing.reducir_grado_producto(maxDeg, grado_num, grado_den, id)

    with open("prod.json", "r") as f:
        prod_reducido = json.load(f)

    return prod_reducido

#  Adaptar salida del producto a formato suma_fracciones
def adaptar_a_suma(prod_reducido):

    opciones = []

    for opcion in prod_reducido["options"]: 
        grado_num = opcion["degree_numerator"]
        grado_den = opcion["degree_denominator"]

        num = opcion["product"]["numerator"]
        den = opcion["product"]["denominator"]

        comps_num = list(num["intermediate"])

        if num["orig_num"] > 0: comps_num.append(f"orig_n_{num["orig_num"]}")
        if num["orig_den"] > 0: comps_num.append(f"orig_d_{num["orig_den"]}")

        comps_den = list(den["intermediate"])

        if den["orig_num"] > 0: comps_den.append(f"orig_n_{den["orig_num"]}")
        if den["orig_den"] > 0: comps_den.append(f"orig_d_{den["orig_den"]}")

        opciones.append({
            "values": [
                {"signals": comps_num, "degree": grado_num},
                {"signals": comps_den, "degree": grado_den}
            ]
        })

    fraccion_equivalente = {
        "op": "frac",
        "options": opciones
    }

    return fraccion_equivalente

def construir_fracc_producto_desde_opcion(option_data):

    num = option_data["product"]["numerator"]
    den = option_data["product"]["denominator"]

    result = {
        "numerator": {
            "intermediate": list(num["intermediate"]),
            "orig_num": num["orig_num"],
            "orig_den": num.get("orig_den", 0)
        },
        "denominator": {
            "intermediate": list(den["intermediate"]),
            "orig_num": den.get("orig_num", 0),
            "orig_den": den["orig_den"]
        }
    }

    return result

parser = argparse.ArgumentParser()
parser.add_argument("filein", type=str)
args = parser.parse_args()

with open(args.filein) as f:
    data = json.load(f)

expresiones = data["expressions"]
maxDeg = data["degree"]

prod_data_por_fraccion = []
fracciones_para_suma = []
vi_utilizadas_total  = 0
variables_intermedias = []

for idx, frac in enumerate(expresiones):
    grado_num = frac["values"][0]["degree"]
    grado_den = frac["values"][1]["degree"]

    # se pasa de grado --> reducir grado
    if grado_num > maxDeg or grado_den >= maxDeg:

        print(f"Executing product to fraction {idx}...")
        prod_reducido = ejecutar_producto(grado_num, grado_den, maxDeg, idx)
        prod_data_por_fraccion.append(prod_reducido)
        fracciones_para_suma.append(adaptar_a_suma(prod_reducido))

    # NO se pasa de grado --> queda como está
    else:
        prod_data_por_fraccion.append(None)

        opcion_suma = {
            "op": "frac",
            "options": [{
                "values": [
                    {"signals": [], "degree": grado_num},
                    {"signals": [], "degree": grado_den}
                ]
            }]
        }

        fracciones_para_suma.append(opcion_suma)

# Preprocesado descartando las fracciones que no pueden combinarse por su grado con ninguna de las otras
fracciones_combinables = []
indices_combinables_originales = []

fracciones_no_combinables = []
indices_no_combinables = []

for id_f, f in enumerate(fracciones_para_suma):
    combinable = False

    for opt_f in f["options"]:
        grado_num_f = opt_f["values"][0]["degree"]
        grado_den_f = opt_f["values"][1]["degree"]

        for id_g, g in enumerate(fracciones_para_suma):
            if id_g != id_f:

                for opt_g in g["options"]:
                    grado_num_g = opt_g["values"][0]["degree"]
                    grado_den_g = opt_g["values"][1]["degree"]

                    if (grado_num_f + grado_den_g <= maxDeg) and (grado_den_f + grado_num_g <= maxDeg) and (grado_den_f + grado_den_g < maxDeg):
                        combinable = True
                        break
            
            if combinable: break

        if combinable: break
    
    if combinable: 
        fracciones_combinables.append(f)
        indices_combinables_originales.append(id_f) 
        # print(f"Fracción {id_f} se puede combinar con alguna otra: grado num {grado_num_f}, grado den {grado_den_f}")
    else: 
        fracciones_no_combinables.append(f)
        indices_no_combinables.append(id_f)
        # print(f"Fracción {id_f} no se puede combinar con ninguna otra, formará una VI nueva: grado num {grado_num_f}, grado den {grado_den_f}")

resultado_suma = None
grupos = []

if len(fracciones_combinables) > 0:
    print("Executing suma_fracciones...\n")
    resultado_suma = multioption_fractions_sum.suma_fracciones_multiopcion(maxDeg, maxDeg - 1, fracciones_combinables)

    grupos = resultado_suma["groups"]

    print("\n--- Resultado de sumas ---")
    for g in grupos:
        frs = g["fractions"]
        cadena = " + ".join(f"fraction {indices_combinables_originales[f]}" for f in frs)
        print(f"sum{g['sum']} = {cadena}")

    # print("Executing suma_fracciones_0_1...\n")
    # grupos = suma_fracciones_0_1.suma_fracciones(maxDeg, maxDeg - 1, fracciones_combinables, indices_combinables_originales)

opcion_elegida = {}

if resultado_suma is not None:
    for info in resultado_suma["options"]:
        local_idx = info["expression"]
        global_idx = indices_combinables_originales[local_idx]
        opcion_elegida[global_idx] = info["selected_option"]

# Para las fracciones no combinables se elige la opción 0 que siempre va a existir
for idx in indices_no_combinables:
    opcion_elegida[idx] = 0

fracciones_producto = {}

for idx in range(len(expresiones)):

    opt_idx = opcion_elegida[idx]
    prod = prod_data_por_fraccion[idx]

    # Ha sido una fracción que ha ejecutado el producto
    if prod is not None:
        opcion_data = prod["options"][opt_idx]

        lista_vi_opcion = opcion_data.get("intermediate_variables", [])
         
        for k, vi in enumerate(lista_vi_opcion):
            int_n = [x + vi_utilizadas_total for x in vi["numerator"]["intermediate"]]
            int_d = [x + vi_utilizadas_total for x in vi["denominator"]["intermediate"]]
 
            variables_intermedias.append({
                "fraction": idx,
                "iv": k,
                "numerator": {
                    "intermediate": int_n,
                    "orig_num":     vi["numerator"]["orig_num"],
                    "orig_den":     vi["numerator"].get("orig_den", 0)
                },
                "denominator": {
                    "intermediate": int_d,
                    "orig_num":     vi["denominator"].get("orig_num", 0),
                    "orig_den":     vi["denominator"]["orig_den"]
                }
            })
        
        frac = construir_fracc_producto_desde_opcion(opcion_data)
        frac["numerator"]["intermediate"] = [x + vi_utilizadas_total for x in frac["numerator"]["intermediate"]]
        frac["denominator"]["intermediate"] = [x + vi_utilizadas_total for x in frac["denominator"]["intermediate"]]
        fracciones_producto[idx] = frac

        vi_utilizadas_total += len(lista_vi_opcion)
        print(f"Fracción {idx} ha ejecutado el producto, creando {len(lista_vi_opcion)} VI intermedias")

    else:

        frac_orig = expresiones[idx]
        grado_num = frac_orig["values"][0]["degree"]
        grado_den = frac_orig["values"][1]["degree"]

        fracciones_producto[idx] = {
            "numerator": {
                "intermediate": [],
                "orig_num": grado_num,
                "orig_den": 0
            },
            "denominator": {
                "intermediate": [],
                "orig_num": 0,
                "orig_den": grado_den
            }
        }

        print(f"Fracción {idx} no ha ejecutado el producto, no crea VI intermedias")

grupos_finales = []

for g in grupos:
    frs = [indices_combinables_originales[f] for f in g["fractions"]]
    grupos_finales.append({
        "sum": g["sum"],
        "fractions": frs,
    })

if resultado_suma is not None:
    total_vi_suma = resultado_suma["total_vi_created"] 
else:
    total_vi_suma = 0

for pos, id_x in enumerate(indices_no_combinables):
    frac_orig = expresiones[id_x]
    grado_num = frac_orig["values"][0]["degree"]
    grado_den = frac_orig["values"][1]["degree"]

    # Si tiene denominador no puede quedarse como fracción: necesita una VI propia
    if grado_den > 0: total_vi_suma += 1

    grupos_finales.append({
        "sum": len(grupos_finales) + 1,
        "fractions": [id_x],
    })

vi_utilizadas_total += total_vi_suma

# Las fracciones no combinables con denominador crean una VI sola.
# Hay que contarlas en vi_utilizadas_total y añadirlas a variables_intermedias
# para que aparezcan en el JSON final.
for id_x in indices_no_combinables:
    frac_orig = expresiones[id_x]
    grado_num_nc = frac_orig["values"][0]["degree"]
    grado_den_nc = frac_orig["values"][1]["degree"]

    if grado_den_nc > 0:
        # La VI de suma para esta fracción no combinable
        # Su numerador y denominador vienen directamente de fracciones_producto[id_x]
        fp = fracciones_producto[id_x]
        variables_intermedias.append({
            "fraction": id_x,
            "iv": "sum",
            "numerator":   fp["numerator"],
            "denominator": fp["denominator"]
        })
        # vi_utilizadas_total += 1

print(f"\nTotal VIs de producto: {vi_utilizadas_total - total_vi_suma}")
print(f"Total VIs de suma: {total_vi_suma}")
print(f"Total VIs creadas: {vi_utilizadas_total}")

# Construir ecuaciones finales

lista_ecuaciones = []

for suma_id, g in enumerate(grupos_finales):
    frs = g["fractions"]
    
    # Lado izquierdo
    vis_izq = []
    fractores_izq = [] 

    for frac in frs:
        den = fracciones_producto[frac]["denominator"]
        if den["orig_den"] > 0:
            fractores_izq.append(factor_original("denominator", frac, den["orig_den"]))

        for elem in den["intermediate"]:
            vis_izq.append(elem)
        
    lado_izquierdo = {
        "type": "prod",
        "sum": suma_id,
        "intermediate": vis_izq,
        "original_factors": fractores_izq
    }

    # Lado derecho
    terminos = []

    for frac in frs:
        vis = []
        factores = []

        num = fracciones_producto[frac]["numerator"]

        for vi_name in num["intermediate"]:
            vis.append(vi_name)

        if num["orig_num"] > 0:
            factores.append(factor_original("numerator", frac, num["orig_num"]))

        for j in frs:
            if j != frac:
                den_j = fracciones_producto[j]["denominator"]
                if den_j["orig_den"] > 0:
                    factores.append(factor_original("denominator", j, den_j["orig_den"]))
                
                for elem in den_j["intermediate"]:
                    vis.append(elem)

        terminos.append({
            "type": "prod",
            "intermediate": vis,
            "original_factors": factores
        })
    
    lado_derecho = {
        "type": "sum",
        "terms": terminos
    }

    lista_ecuaciones.append({
        "left_side": lado_izquierdo,
        "right_side": lado_derecho
    })

# JSON final

resultado = {
    "total_vi_created": vi_utilizadas_total,
    "intermediate_variables": variables_intermedias,
    "equations": lista_ecuaciones
}

with open("final_result.json", "w") as fout:
    json.dump(resultado, fout, indent=4)

print("File 'final_result.json' generated correctly.")