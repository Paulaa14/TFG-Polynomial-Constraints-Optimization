#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from z3 import *
import argparse

"""
Para el caso particular de suma de fracciones

El grado de una suma de fracciones es el máximo entre todos los productos de los numeradores por el mínimo común múltiplo de los denominadores

Cuando se cambia por variables ya no son fracciones, el grado es el máximo grado de los operandos de la suma

Versión sin controlar fracciones repetidas pero reduciendo el número de variables -> triángulo superior

"""
def addsum(a):
    if len(a) == 0:
        return IntVal(0)
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

solver = Optimize()

# Para cada expresión, me la quedo tal cual o la expando. Si me la quedo significa que va a ser una "VI" final
expando = []

for exp in range(num_expresiones):
    expando.append(Bool("exp_" + str(exp)))

    # Minimiza el número de variables "originales"
    solver.add_soft(expando[exp], 5, "keeps")

# Si ya se pasa de grado no se va a poder unificar con nada
for exp in range(num_expresiones):
    grado_num_exp = expresiones[exp]["values"][0]["degree"]
    grado_den_exp = expresiones[exp]["values"][1]["degree"] 
    
    if grado_num_exp > maxDeg or grado_den_exp > maxDeg:
        solver.add(Not(expando[exp]))
    
# Para cada expresión que ha sido expandida, booleano que indica si se junta o no con la expresión i-ésima
juntar = []

for exp in range(num_expresiones):
    juntar_exp = []
    for e in range(exp + 1, num_expresiones):
        juntar_exp.append(Bool("juntar_" + str(exp) + "_" + str(e)))
    
    juntar.append(juntar_exp) 

for exp in range(num_expresiones):
    for e in range(exp + 1, num_expresiones):     
        # Si se cumple esto, se pueden unir. Sino, obligatoriamente el booleano debe ir a false
        solver.add(Implies(Or(Not(expando[exp]), Not(expando[e])), Not(juntar[exp][e - exp - 1])))

        # Para que las relaciones entén en la primera fracción que forma la unión de fracciones y no contar el grado 2 veces
        for anterior in range(0, e - exp - 1):
            solver.add(Implies(And(juntar[exp][e - exp - 1], juntar[exp][anterior]), Not(juntar[anterior][e - anterior - 1])))

# Las variables que se juntan y pasan de grado obligatoriamente tienen que tener su juntar a false
for exp in range(num_expresiones):
    for e in range(exp + 1, num_expresiones):
        grado_num_exp = expresiones[exp]["values"][0]["degree"]
        grado_den_exp = expresiones[exp]["values"][1]["degree"] 
        grado_num_e = expresiones[e]["values"][0]["degree"]
        grado_den_e = expresiones[e]["values"][1]["degree"]

        # Si se juntan se pasa de grado
        if grado_num_exp + grado_den_e > maxDeg or grado_num_e + grado_den_exp > maxDeg or grado_den_exp + grado_den_e > maxDeg:
            solver.add(Not(juntar[exp][e - exp - 1]))

# Comprobar que las expresiones que se forman no superan el grado
for exp in range(num_expresiones):
    grado_num = expresiones[exp]["values"][0]["degree"]
    grado_den = expresiones[exp]["values"][1]["degree"]

    for e in range(exp + 1, num_expresiones):

        # max(numerador actual * denominador de e, numerador de e * denominador actual)
        expr1 = grado_num + expresiones[e]["values"][1]["degree"]
        expr2 = grado_den + expresiones[e]["values"][0]["degree"]

        nuevo_grado_num = If(juntar[exp][e - exp - 1], If(expr1 > expr2, expr1, expr2), grado_num)
        nuevo_grado_den = If(juntar[exp][e - exp - 1], grado_den + expresiones[e]["values"][1]["degree"], grado_den)

        grado_num = nuevo_grado_num
        grado_den = nuevo_grado_den

    grado_total = If(expando[exp], If(grado_num > grado_den, grado_num, grado_den), 0)

    solver.add(grado_total <= maxDeg)

# Si se expande una expresión, obligatoriamente se tiene que unificar con otra. Variables que realmente cuentan
for exp in range(num_expresiones):
    suma_fila = []
    suma_col = []
    for e in range(exp + 1, num_expresiones): # En la fila solo puede tener activos los siguientes
        suma_fila.append(If(juntar[exp][e - exp - 1], 1, 0))
    
    for e in range(0, exp): # En la columna solo puede estar activo en los anteriores
        suma_col.append(If(juntar[e][exp - e - 1], 1, 0))
    
    # Cada fracción unicamente está unificada 1 vez
    s_fila = addsum(suma_fila)
    s_col = addsum(suma_col)
    solver.add(Implies(s_fila > 0, s_col == 0))
    solver.add(Implies(s_col > 0, s_fila == 0))
    solver.add(s_col <= 1)

    # Solo puede ser usada en una variable nueva
    # for e in range(exp + 1, num_expresiones - 1):
    #     for sig in range(exp + 1, e):
    #         solver.add(Implies(juntar[exp][e - exp - 1], Not(juntar[sig][e - sig - 1])))

    solver.add(Implies(expando[exp], Or(s_fila > 0, s_col > 0)))

    # Minimizar número de variables creadas
    solver.add_soft(s_fila == 0, 5, "min_vars")

if solver.check() == sat:
    modelo = solver.model()
    print("Solución encontrada:\n")

    expanden = [i for i in range(num_expresiones) if modelo.evaluate(expando[i]) == True]
    no_expand = [i for i in range(num_expresiones) if modelo.evaluate(expando[i]) == False]

    unificaciones = []

    for i in expanden:
        grupo = [i]
        for j in range(i + 1, num_expresiones):
            if modelo.evaluate(juntar[i][j - i - 1]) == True:
                grupo.append(j)
        if len(grupo) > 1:
            unificaciones.append(sorted(grupo))

    if unificaciones:
        for idx, grupo in enumerate(unificaciones):
            print(f"Fracción nueva {idx+1}: combinación de expresiones {grupo}")
            for g in grupo:
                num = expresiones[g]["values"][0]["signals"]
                den = expresiones[g]["values"][1]["signals"]
                print(f"      · Exp {g}: ({num}) \\ ({den})")
    else:
        print("No se han unificado fracciones.")

    if no_expand:
        print("\nFracciones originales que no se han expandido:")
        for i in no_expand:
            num = expresiones[i]["values"][0]["signals"]
            den = expresiones[i]["values"][1]["signals"]
            print(f"  - Expresión {i} → ({num}) \\ ({den})")
else:
    print("No se encontró una solución válida bajo las restricciones dadas.")