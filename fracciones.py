
# Suma de fracciones -> primero se solucionan las fracciones que se pasan del grado máximo y luego se reduce el grado de la suma

# Pasar a js: ver si la suma funciona la versión que hay hecha en js + pasar producto_nuevo a js + pasar fracciones.py a js con las llamadas
# Documentar variables + procedimiento de los 3 ficheros

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import argparse
import prod_fracciones_nuevo
import suma_fracciones_v1_2
    
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

    with open("prod.json", "r") as f:
        prod_reducido = json.load(f)

    return prod_reducido

#  Adaptar salida del producto a formato suma_fracciones
def adaptar_a_suma(prod_reducido, maxDeg):
    grado_num = prod_reducido["grado_numerador"]
    grado_den = prod_reducido["grado_denominador"]

    num = prod_reducido["producto"]["numerador"]
    den = prod_reducido["producto"]["denominador"]

    comps_num = []

    for elem in num["intermedias"]:
        comps_num.append(elem)

    if num["orig_num"] > 0: comps_num.append(f"orig_n_{num["orig_num"]}")
    if num["orig_den"] > 0: comps_num.append(f"orig_d_{num["orig_den"]}")

    comps_den = []

    for elem in den["intermedias"]:
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
    if grado_num > maxDeg or grado_den > maxDeg:

        print(f"Ejecutando producto sobre la fracción {idx}...")
        prod_reducido = ejecutar_producto(grado_num, grado_den, maxDeg, idx)

        lista_vi = prod_reducido["variables_intermedias"]

        vi_global_map = {}
        for k in range(len(lista_vi)):

            int_n = lista_vi[k]["numerador"]["intermedias"]
            for i in range(len(int_n)):
                int_n[i] += vi_utilizadas_total

            int_d = lista_vi[k]["denominador"]["intermedias"]
            for i in range(len(int_d)):
                int_d[i] += vi_utilizadas_total

            numerador = {
                "intermedias": int_n,
                "orig_num": lista_vi[k]["numerador"]["orig_num"],
                "orig_den": lista_vi[k]["numerador"]["orig_den"]
            }

            denominador = {
                "intermedias": int_d,
                "orig_num": lista_vi[k]["denominador"]["orig_num"],
                "orig_den": lista_vi[k]["denominador"]["orig_den"]
            }

            # contenido = {
            #     "numerador": numerador,
            #     "denominador": denominador
            # }

            variables_intermedias.append({
                "fraccion": idx,
                "vi": k,
                # "contenido": contenido
                "numerador": numerador,
                "denominador": denominador
            })

        comp_num = prod_reducido["producto"]["numerador"]
        comp_den = prod_reducido["producto"]["denominador"]

        for i in range(len(comp_num["intermedias"])):
            comp_num["intermedias"][i] += vi_utilizadas_total

        for i in range(len(comp_den["intermedias"])):
            comp_den["intermedias"][i] += vi_utilizadas_total

        fracciones_producto.append({
            "fraccion": idx,
            "numerador": comp_num,
            "denominador": comp_den
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
            "intermedias": [],
            "orig_num": num_signals,
            "orig_den": 0
        }
        
        orig_den = {
            "intermedias": [],
            "orig_num": 0,
            "orig_den": den_signals
        }
        
        fracciones_producto.append({
            "fraccion": idx,
            "numerador": orig_num,
            "denominador": orig_den
        })

print("Ejecutando suma_fracciones_v1_2...\n")

# Ejecuta la suma y obtiene los grupos. El grado del numerador puede ser maxDeg pero el grado del denominador tiene que ser menor que maxDeg para que
# al pasar mutiplicando al otro lado no te pases de grado
grupos = suma_fracciones_v1_2.suma_fracciones(maxDeg, maxDeg - 1, fracciones)

# Calcular cuántas VI se necesitan realmente
total_vi_creadas = 0

sumas = []

print("\n--- Resultado de sumas ---")
for g in grupos:
    frs = g["fracciones"]
    cadena = " + ".join(f"fracción {f}" for f in frs)
    print(f"suma{g['suma']} = {cadena}")

    sumas.append({
        # "fraccion": None,
        # "vi": total_vi_creadas,
        # "tipo": "suma",
        "fracciones": frs
    })

    total_vi_creadas += 1

print("\nTotal de VI creadas en la suma =", total_vi_creadas)
vi_utilizadas_total += total_vi_creadas
print("\nTotal de VI creadas =", vi_utilizadas_total)

resultado_final = [f"VI_S_{i}" for i in range(len(grupos))]

lista_ecuaciones = []

for suma_id, g in enumerate(grupos):

    frs = g["fracciones"]

    # -------- LADO IZQUIERDO --------
    vis_izq = []

    # V_S_id
    # vis_izq.append(vi_utilizadas_total - total_vi_creadas + suma_id)
    
    factores_izq = []

    # denominadores
    for frac in frs:
        den = fracciones_producto[frac]["denominador"]
        if den["orig_den"] > 0:
            factores_izq.append(factor_original("denominador", frac, den["orig_den"]))

        for elem in den["intermedias"]:
            vis_izq.append(elem)

    lado_izquierdo = {
        "tipo": "prod",
        "suma": suma_id,
        "intermedias": vis_izq,
        "factores_originales": factores_izq
    }

    # -------- LADO DERECHO --------
    terminos = []

    for frac in frs:

        vis = []
        factores = []

        num = fracciones_producto[frac]["numerador"]

        # VI del numerador
        for vi_name in num["intermedias"]:
            vis.append(vi_name)

        # originales del numerador
        if num["orig_num"] > 0:
            factores.append(factor_original("numerador", frac, num["orig_num"]))

        # denominadores del resto
        for j in frs:
            if j != frac:
                den_j = fracciones_producto[j]["denominador"]
                if den_j["orig_den"] > 0:
                    factores.append(factor_original("denominador", j, den_j["orig_den"]))
                
                for elem in den_j["intermedias"]:
                    vis.append(elem)

        terminos.append({
            "tipo": "prod",
            "intermedias": vis,
            "factores_originales": factores
        })

    lado_derecho = {
        "tipo": "sum",
        "terminos": terminos
    }

    lista_ecuaciones.append({
        # "id": suma_id,
        "lado_izquierdo": lado_izquierdo,
        "lado_derecho": lado_derecho
    })

resultado_final = []

for idx in range(total_vi_creadas):
    resultado_final.append(vi_utilizadas_total - total_vi_creadas + idx)

# Construir JSON FINAL
resultado = {
    "total_vi_creadas": vi_utilizadas_total,
    "variables_intermedias": variables_intermedias,
    # "sumas": sumas,
    # "fracciones_producto": fracciones_producto,
    "ecuaciones": lista_ecuaciones
    # "resultado_final": resultado_final
}

with open("resultado_final.json", "w") as fout:
    json.dump(resultado, fout, indent=4)

print("\nArchivo 'resultado_final.json' generado correctamente.")