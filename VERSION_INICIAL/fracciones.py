
# Suma de fracciones -> primero se solucionan las fracciones que se pasan del grado máximo y luego se reduce el grado de la suma

# Pasar a js: ver si la suma funciona la versión que hay hecha en js + pasar producto_nuevo a js + pasar fracciones.py a js con las llamadas
# Documentar variables + procedimiento de los 3 ficheros

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import argparse
import prod_fracciones_nuevo
import prod_fracciones_incremental
import suma_fracciones_v1_2
import suma_fracciones_0_1
    
def ref_vi(fraccion, vi):
    return {
        "fraccion": fraccion,
        "vi": vi
    }

def factor_original(origen, fraccion, cantidad):
    return {
        "origen": origen,
        "fraccion": fraccion,
        "cantidad": cantidad
    }

def ejecutar_producto(grado_num, grado_den, maxDeg, id):
    prod_fracciones_nuevo.reducir_grado_producto(maxDeg, grado_num, grado_den, id)
    # prod_fracciones_incremental.reducir_grado_producto(maxDeg, grado_num, grado_den, id)

    with open("prod.json", "r") as f:
        prod_reducido = json.load(f)

    return prod_reducido

#  Adaptar salida del producto a formato suma_fracciones
def adaptar_a_suma(prod_reducido, maxDeg):
    grado_num = prod_reducido["degree_numerator"]
    grado_den = prod_reducido["degree_denominator"]

    num = prod_reducido["product"]["numerator"]
    den = prod_reducido["product"]["denominator"]

    comps_num = []

    for elem in num["intermediate"]:
        comps_num.append(elem)

    if num["orig_num"] > 0: comps_num.append(f"orig_n_{num["orig_num"]}")
    if num["orig_den"] > 0: comps_num.append(f"orig_d_{num["orig_den"]}")

    comps_den = []

    for elem in den["intermediate"]:
        comps_den.append(elem)

    if den["orig_num"] > 0: comps_den.append(f"orig_n_{den["orig_num"]}")
    if den["orig_den"] > 0: comps_den.append(f"orig_d_{den["orig_den"]}")

    fraccion_equivalente = {
        "op": "frac",
        "values": [
            {"signals": comps_num, "degree": grado_num},
            {"signals": comps_den, "degree": grado_den}
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

    # se pasa de grado --> reducir grado
    if grado_num > maxDeg or grado_den >= maxDeg: # ******************************************

        print(f"Executing product to fraction {idx}...")
        prod_reducido = ejecutar_producto(grado_num, grado_den, maxDeg, idx)

        lista_vi = prod_reducido["intermediate_variables"]

        vi_global_map = {}
        for k in range(len(lista_vi)):

            int_n = lista_vi[k]["numerator"]["intermediate"]
            for i in range(len(int_n)):
                int_n[i] += vi_utilizadas_total

            int_d = lista_vi[k]["denominator"]["intermediate"]
            for i in range(len(int_d)):
                int_d[i] += vi_utilizadas_total

            numerador = {
                "intermediate": int_n,
                "orig_num": lista_vi[k]["numerator"]["orig_num"],
                "orig_den": lista_vi[k]["numerator"]["orig_den"]
            }

            denominador = {
                "intermediate": int_d,
                "orig_num": lista_vi[k]["denominator"]["orig_num"],
                "orig_den": lista_vi[k]["denominator"]["orig_den"]
            }

            variables_intermedias.append({
                "fraction": idx,
                "iv": k,
                # "contenido": contenido
                "numerator": numerador,
                "denominator": denominador
            })

        comp_num = prod_reducido["product"]["numerator"]
        comp_den = prod_reducido["product"]["denominator"]

        for i in range(len(comp_num["intermediate"])):
            comp_num["intermediate"][i] += vi_utilizadas_total

        for i in range(len(comp_den["intermediate"])):
            comp_den["intermediate"][i] += vi_utilizadas_total

        fracciones_producto.append({
            "fraction": idx,
            "numerator": comp_num,
            "denominator": comp_den
        })

        vi_utilizadas_total += len(lista_vi)

        # Adaptar formato a entrada de suma
        fraccion_adaptada = adaptar_a_suma(prod_reducido, maxDeg)
        fracciones.append(fraccion_adaptada["expressions"][0])

    # NO se pasa de grado --> queda como está
    else:
        fracciones.append(frac)

        num_signals = grado_num
        den_signals = grado_den

        orig_num = {
            "intermediate": [],
            "orig_num": num_signals,
            "orig_den": 0
        }
        
        orig_den = {
            "intermediate": [],
            "orig_num": 0,
            "orig_den": den_signals
        }
        
        fracciones_producto.append({
            "fraction": idx,
            "numerator": orig_num,
            "denominator": orig_den
        })

# Preprocesado descartando las fracciones que no pueden combinarse por su grado con ninguna de las otras
fracciones_combinables = []
fracciones_que_forman_var = []
indices_fracciones_que_forman_var = []
indices_combinables_originales = []

for id_f, f in enumerate(fracciones):
    grado_num_f = f["values"][0]["degree"]
    grado_den_f = f["values"][1]["degree"]

    combinable = False
    for id_g, g in enumerate(fracciones):
        if id_g != id_f:
            grado_num_g = g["values"][0]["degree"]
            grado_den_g = g["values"][1]["degree"]

            if (grado_num_f + grado_den_g <= maxDeg) and (grado_den_f + grado_num_g <= maxDeg) and (grado_den_f + grado_den_g < maxDeg):
                combinable = True
    
    if combinable: 
        fracciones_combinables.append(f)
        indices_combinables_originales.append(id_f) 
        print(f"Fracción {id_f} se puede combinar con alguna otra: grado num {grado_num_f}, grado den {grado_den_f}")
    else: 
        fracciones_que_forman_var.append(f)
        indices_fracciones_que_forman_var.append(id_f)
        print(f"Fracción {id_f} no se puede combinar con ninguna otra, formará una VI nueva: grado num {grado_num_f}, grado den {grado_den_f}")

if len(fracciones_combinables) > 0:
    print("Executing suma_fracciones_v1_2...\n")
    grupos = suma_fracciones_v1_2.suma_fracciones(maxDeg, maxDeg - 1, fracciones_combinables, indices_combinables_originales)

    # print("Executing suma_fracciones_0_1...\n")
    # grupos = suma_fracciones_0_1.suma_fracciones(maxDeg, maxDeg - 1, fracciones_combinables, indices_combinables_originales)

# Calcular cuántas VI se necesitan realmente
total_vi_creadas = 0

print("\n--- Resultado de sumas ---")
for g in grupos:
    frs = g["fractions"]
    cadena = " + ".join(f"fraction {f}" for f in frs)
    print(f"sum{g['sum']} = {cadena}")

    total_vi_creadas += 1

# Cuentan como variables nuevas las que no se pueden combinar con otras y tienen forma de fracción, porque hace falta meterlas en una VI nueva
for idx, f in enumerate(fracciones_que_forman_var):
    grado_num_f = f["values"][0]["degree"]
    grado_den_f = f["values"][1]["degree"]

    if grado_num_f > 0 and grado_den_f > 0:
        vi_utilizadas_total += 1
    
    grupos.append({
        "sum": len(grupos),
        "fractions": [indices_fracciones_que_forman_var[idx]]
    })

print("\nTotal de VI creadas en la suma =", total_vi_creadas)
vi_utilizadas_total += total_vi_creadas
print("\nTotal de VI creadas =", vi_utilizadas_total)

resultado_final = [f"VI_S_{i}" for i in range(len(grupos))]

lista_ecuaciones = []

for suma_id, g in enumerate(grupos):

    frs = g["fractions"]

    # -------- LADO IZQUIERDO --------
    vis_izq = []    
    factores_izq = []

    # denominadores
    for frac in frs:
        den = fracciones_producto[frac]["denominator"]
        if den["orig_den"] > 0:
            factores_izq.append(factor_original("denominator", frac, den["orig_den"]))

        for elem in den["intermediate"]:
            vis_izq.append(elem)

    lado_izquierdo = {
        "type": "prod",
        "sum": suma_id,
        "intermediate": vis_izq,
        "original_factors": factores_izq
    }

    # -------- LADO DERECHO --------
    terminos = []

    for frac in frs:

        vis = []
        factores = []

        num = fracciones_producto[frac]["numerator"]

        # VI del numerador
        for vi_name in num["intermediate"]:
            vis.append(vi_name)

        # originales del numerador
        if num["orig_num"] > 0:
            factores.append(factor_original("numerator", frac, num["orig_num"]))

        # denominadores del resto
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

resultado_final = []

for idx in range(total_vi_creadas):
    resultado_final.append(vi_utilizadas_total - total_vi_creadas + idx)

# Construir JSON FINAL
resultado = {
    "total_vi_created": vi_utilizadas_total,
    "intermediate_variables": variables_intermedias,
    "equations": lista_ecuaciones
}

with open("resultado_final.json", "w") as fout:
    json.dump(resultado, fout, indent=4)

print("\File 'resultado_final.json' generated correctly.")