
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import argparse

def check_intermedia_num(final, vi):
    orig_num = final["variables_intermedias"][vi]["numerador"]["orig_num"] + final["variables_intermedias"][vi]["denominador"]["orig_num"]

    for intermedia in final["variables_intermedias"][vi]["numerador"]["intermedias"]:
        orig_num += check_intermedia_num(final, intermedia)

    for intermedia in final["variables_intermedias"][vi]["denominador"]["intermedias"]:
        orig_num += check_intermedia_num(final, intermedia)

    return orig_num

def check_intermedia_den(final, vi):
    orig_den = final["variables_intermedias"][vi]["numerador"]["orig_den"] + final["variables_intermedias"][vi]["denominador"]["orig_den"]

    for intermedia in final["variables_intermedias"][vi]["numerador"]["intermedias"]:
        orig_den += check_intermedia_den(final, intermedia)

    for intermedia in final["variables_intermedias"][vi]["denominador"]["intermedias"]:
        orig_den += check_intermedia_den(final, intermedia)

    return orig_den

def checker(orig, final, maxDeg):
# 1. En ningún sitio te pasas de grado

# 1.1 En variables intermedias del producto

    for i in range(len(final["variables_intermedias"])):
        vi = final["variables_intermedias"][i]

        grado_num = vi["numerador"]["orig_num"] + vi["numerador"]["orig_den"] + len(vi["numerador"]["intermedias"])

        if grado_num > maxDeg: 
            print(f"La variable intermedia {i} se pasa de grado en numerador: {grado_num}")
            return False
        
        grado_den = vi["denominador"]["orig_num"] + vi["denominador"]["orig_den"] + len(vi["denominador"]["intermedias"])

        if grado_den > maxDeg: 
            print(f"La variable intermedia {i} se pasa de grado en denominador: {grado_den}")
            return False
        
# 1.2 En variables intermedias de la suma

    for i in range(len(final["sumas"])):

        grados_num = []
        grados_den = []

        for f in final["sumas"][i]["fracciones"]:
            frac = final["fracciones_producto"][f]

            grado_num = len(frac["numerador"]["intermedias"]) + frac["numerador"]["orig_num"] + frac["numerador"]["orig_den"]

            if grado_num > maxDeg: 
                print(f"La fracción {f} se pasa de grado en numerador: {grado_num}")
                return False
            
            grado_den = len(frac["denominador"]["intermedias"]) + frac["denominador"]["orig_num"] + frac["denominador"]["orig_den"]

            if grado_den > maxDeg: 
                print(f"La fracción {f} se pasa de grado en denominador: {grado_den}")
                return False
            
            grados_num.append(grado_num)
            grados_den.append(grado_den)
        
        grado_den_total = sum(grados_den)
        grado_num_total = 0

        for j in range(len(grados_num)):
            grado_termino = grados_num[j] + grado_den_total - grados_den[j]
            grado_num_total = max(grado_num_total, grado_termino)

        if grado_num_total > maxDeg or grado_den_total > maxDeg:
            print(f"La suma {i} se pasa de grado: num={grado_num_total}, den={grado_den_total}" )
            return False
        
# 1.3 En ecuaciones finales

    for i in range(len(final["ecuaciones"])):

        izq = final["ecuaciones"][i]["lado_izquierdo"]

        grado_izq = len(izq["intermedias"]) + 1 # + 1 por la variable de suma

        for elem in izq["factores_originales"]:
            grado_izq += elem["cantidad"]

        if grado_izq > maxDeg: 
            print(f"La ecuación {i} se pasa de grado en el lado izquierdo: {grado_izq}")
            return False
        
        dere = final["ecuaciones"][i]["lado_derecho"]["terminos"]

        for t in range(len(dere)):

            grado_dere = len(dere[t]["intermedias"])

            for elem in dere[t]["factores_originales"]:
                grado_dere += elem["cantidad"]

            if grado_dere > maxDeg: 
                print(f"La ecuación {i} se pasa de grado en el lado derecho: {grado_dere}")
                return False

# Está todo lo original

    for f in range(len(final["fracciones_producto"])):
        frac = final["fracciones_producto"][f]
        orig_num = 0
        orig_den = 0

        for vi in frac["numerador"]["intermedias"]:

            orig_num += check_intermedia_num(final, vi)
            orig_den += check_intermedia_den(final, vi)

        for vi in frac["denominador"]["intermedias"]:

            orig_num += check_intermedia_num(final, vi)
            orig_den += check_intermedia_den(final, vi)

        orig_num += frac["numerador"]["orig_num"] + frac["denominador"]["orig_num"]
        orig_den += frac["numerador"]["orig_den"] + frac["denominador"]["orig_den"]

        if orig_num != orig["expressions"][f]["values"][0]["degree"]:
            print(f"La fracción {f} no tiene todos los elementos originales de numerador: {orig_num}")
            return False
        
        elif orig_den != orig["expressions"][f]["values"][1]["degree"]:
            print(f"La fracción {f} no tiene todos los elementos originales de denominador: {orig_den}")
            return False

    return True

parser = argparse.ArgumentParser()
parser.add_argument("orig", type=str)
parser.add_argument("final", type=str)
args = parser.parse_args()

with open(args.orig) as f:
    orig = json.load(f)

with open(args.final) as f:
    final = json.load(f)

maxDeg = orig["degree"]

if checker(orig, final, maxDeg):
    print("Resultado correcto")