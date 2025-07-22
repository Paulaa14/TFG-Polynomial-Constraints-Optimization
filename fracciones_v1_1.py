#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import itertools
import json
from z3 import *
import argparse

"""
Para el caso particular de suma de fracciones

El grado de una suma de fracciones es el máximo entre todos los productos de los numeradores por el mínimo común múltiplo de los denominadores

"""
def addsum(a):
    if len(a) == 0:
        return 0
    else:
        asum = a[0]
        for i in range(1,len(a)):
            asum = asum + a[i]
        return asum

parser = argparse.ArgumentParser()

parser.add_argument("filein", type=str)
# parser.add_argument("fileout")

args=parser.parse_args()

f = open(args.filein)
data = json.load(f)

# file = open(args.fileout, "w")

expresiones = data["expressions"]
maxDeg = data["degree"]
num_expresiones = len(expresiones)
max_intermedias = 3

degrees = [] # Cada expresión qué grado tiene -> máximo entre numerador y denominador???
combinaciones = set()
cjto_variables = set()

solver = Solver()

# Para cada expresión, me la quedo tal cual o la expando. Si me la quedo significa que va a ser un "VI" final
expando = []
cuantas_keep = []

for exp in range(num_expresiones):
    expando.append(Bool("exp_" + str(exp)))
    cuantas_keep.append(If(Not(expando[exp]), 1, 0))
    
# Para cada expresión que ha sido expandida, booleano que indica si se junta o no con la expresión i-ésima
juntar = []

for exp in range(num_expresiones):
    juntar_exp = []
    for e in range(num_expresiones):
        juntar_exp.append(Bool("juntar_" + str(exp) + "_" + str(e)))
    
    juntar.append(juntar_exp)

for exp in range(num_expresiones):
    for e in range(num_expresiones):
        if exp == e:  # No juntar una expresión consigo misma
            solver.add(Not(juntar[exp][e]))
            solver.add(Not(juntar[e][exp]))

        elif exp > e:
            solver.add(Not(juntar[exp][e]))
        else:
            # Si se cumple esto, se pueden unir. Sino, obligatoriamente el booleano debe ir a false
            solver.add(Implies(Not(And(expando[exp], expando[e])), Not(juntar[exp][e])))
            solver.add(Implies(Not(And(expando[exp], expando[e])), Not(juntar[e][exp])))
            solver.add(Implies(juntar[exp][e], Not(juntar[e][exp]))) # Porque sabes que estás en el caso exp < e

            # Para que las relaciones entén en la primera fracción que forma la unión de fracciones y no contar el grado 2 veces
            for anterior in range(0, e):
                solver.add(Implies(And(juntar[exp][e], juntar[exp][anterior]), Not(juntar[anterior][e])))
                # La implicación de no juntar anterior con exp se cumple trivial porque e > anterior

# Comprobar que las expresiones que se forman no superan el grado
for exp in range(num_expresiones):
    # grado_exp = []
    grado_num = [If(expando[exp], expresiones[exp]["values"][0]["degree"], 0)]
    grado_den = [If(expando[exp], expresiones[exp]["values"][1]["degree"], 0)]

    for e in range(num_expresiones):
        expr1 = addsum(grado_num) + expresiones[e]["values"][1]["degree"]
        expr2 = addsum(grado_den) + expresiones[e]["values"][0]["degree"]

        grado_num.append(If(juntar[exp][e], If(expr1 > expr2, expr1, expr2), 0))

        # grado_num.append(If(juntar[exp][e], max(addsum(grado_num) + expresiones[e]["values"][1]["degree"], addsum(grado_den) + expresiones[e]["values"][0]["degree"]), 0))
        grado_den.append(If(juntar[exp][e], addsum(grado_den) + expresiones[e]["values"][1]["degree"], 0))

    expr1 = addsum(grado_num) # + expresiones[exp]["values"][0]["degree"]
    expr2 = addsum(grado_den) # + expresiones[exp]["values"][1]["degree"]

    # grado_final.append(If(expando[exp], If(expr1 > expr2, expr1, expr2), 1))
    solver.add(Implies(expando[exp], If(expr1 > expr2, expr1, expr2) <= maxDeg))
    
    # grado_final.append(If(expando[exp], addsum(grado_exp) + 1, 1))
    
# La expresión final no supera el grado máximo
grado_final = []
for exp in range(num_expresiones):
    depende = []
    for e in range(num_expresiones):
        depende.append(If(juntar[exp][e], 1, 0))

    exp1 = expresiones[exp]["values"][0]["degree"]
    exp2 = expresiones[exp]["values"][1]["degree"]
    grado_final.append(If(And(expando[exp], addsum(depende) > 0), 1, 0))
    grado_final.append(If(And(expando[exp], addsum(depende) == 0), 0, 0))
    grado_final.append(If(Not(expando[exp]), If(exp1 > exp2, exp1, exp2), 0))

solver.add(addsum(grado_final) <= maxDeg)

solver.add(addsum(cuantas_keep) <= 0)

if solver.check() == sat:
    modelo = solver.model()
    print("Solución encontrada:\n")

    expanden = [i for i in range(num_expresiones) if modelo.evaluate(expando[i]) == True]

    # Helper: convertir una fracción en texto legible
    def fraccion_a_texto(exp):
        num_signals = expresiones[exp]["values"][0]["signals"]
        den_signals = expresiones[exp]["values"][1]["signals"]
        return f"({'+'.join(map(str, num_signals))}) / ({'+'.join(map(str, den_signals))})"

    unificaciones = []
    ya_vistas = set()

    for i in expanden:
        grupo = [i]
        for j in range(num_expresiones):
            if i != j and modelo.evaluate(juntar[i][j]) == True:
                grupo.append(j)
        grupo_set = frozenset(grupo)
        if len(grupo) > 1 and grupo_set not in ya_vistas:
            unificaciones.append(sorted(grupo))
            ya_vistas.add(grupo_set)

    if unificaciones:
        for idx, grupo in enumerate(unificaciones):
            print(f"Fracción nueva {idx+1}: combinación de expresiones {grupo}")
            for g in grupo:
                print(f"    - {fraccion_a_texto(g)}")
    else:
        print("No se han unificado fracciones.")
else:
    print("No se encontró una solución válida bajo las restricciones dadas.")
