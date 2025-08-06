#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import itertools
import json
from z3 import *
import argparse

"""
Para el caso particular de suma de fracciones

El grado de una suma de fracciones es el máximo entre todos los productos de los numeradores por el mínimo común múltiplo de los denominadores

Cuando se cambia por variables ya no son fracciones, el grado es el máximo grado de los operandos de la suma

Versión sin controlar fracciones repetidas. En vez de crear variables a partir de una fracción, se "rellenan huecos"

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

# cjto_variables = set()

# for exp in range(num_expresiones):

#     cjto_variables.add(expresiones[exp]["values"][0]["signals"])
#     cjto_variables.add(expresiones[exp]["values"][1]["signals"])

# cjto_variables = sorted(list(cjto_variables))

# variables_expresion = [] # Cada expresión, cuántas variables de cada contiene
# for exp in range(num_expresiones):
#     vars = []

#     for var in cjto_variables:
#         num = 0
#         if expresiones[exp]["values"][0]["signals"] == var: num += 1
#         if expresiones[exp]["values"][1]["signals"] == var: num += 1

#         vars.append(num)

#     variables_expresion.append(vars)

# variables_total = [] # La expresión inicial, cuántas variables de cada contiene
# for var in cjto_variables:
#     c = 0
#     for exp in range(num_expresiones):
#         if expresiones[exp]["values"][0]["signals"] == var: c += 1
#         if expresiones[exp]["values"][1]["signals"] == var: c += 1

#     variables_total.append(c)

solver = Optimize()

# Para cada expresión, me la quedo tal cual o la expando. Si me la quedo significa que va a ser una "VI" final
expando = []

for exp in range(num_expresiones):
    expando.append(Bool("exp_" + str(exp)))

    # Minimiza el número de variables "originales"
    solver.add_soft(expando[exp], 10, "keeps")

# Máximo hay num_expresiones variables nuevas, que es lo que hay que minimizar. Cada variable con qué expresiones está formada
variables_nuevas = [] 

for exp in range(num_expresiones):
    nuevas_exp = []
    for e in range(num_expresiones):
        nuevas_exp.append(Bool("nueva_" + str(exp) + "_" + str(e)))
    
    variables_nuevas.append(nuevas_exp)

for var in range(num_expresiones):
    for e in range(num_expresiones):
        solver.add(Implies(Not(expando[e]), Not(variables_nuevas[var][e])))

        # No se puede usar en más de una variable nueva
        for var_sig in range(var + 1, num_expresiones):
            solver.add(Implies(variables_nuevas[var][e], Not(variables_nuevas[var_sig][e])))

for var in range(num_expresiones - 1):
    usadas_var = []
    usadas_var_sig = []
    for e in range(num_expresiones):
        usadas_var.append(If(variables_nuevas[var][e], 1, 0))
        usadas_var_sig.append(If(variables_nuevas[var + 1][e], 1, 0))

    solver.add(Or(addsum(usadas_var) == 0, addsum(usadas_var) > 1))
    solver.add(Implies(addsum(usadas_var) == 0, addsum(usadas_var_sig) == 0))
    solver.add(addsum(usadas_var) >= addsum(usadas_var_sig))

    # Minimizar número de variables creadas
    solver.add_soft(addsum(usadas_var) == 0, 5, "min_vars")

# Comprobar que las expresiones que se forman no superan el grado
for var in range(num_expresiones):
    grado_num = [0]
    grado_den = [0]

    for e in range(num_expresiones):

        # Trabajo con el último elemento del array que tiene el grado acumulado
        prev_grado_num = grado_num[-1]
        prev_grado_den = grado_den[-1]

        # max(numerador actual * denominador de e, numerador de e * denominador actual)
        expr1 = prev_grado_num + expresiones[e]["values"][1]["degree"]
        expr2 = prev_grado_den + expresiones[e]["values"][0]["degree"]

        nuevo_grado_num = If(variables_nuevas[var][e], If(expr1 > expr2, expr1, expr2), prev_grado_num)
        nuevo_grado_den = If(variables_nuevas[var][e], prev_grado_den + expresiones[e]["values"][1]["degree"], prev_grado_den)

        grado_num.append(nuevo_grado_num)
        grado_den.append(nuevo_grado_den)

    final_num = grado_num[-1]
    final_den = grado_den[-1]
    grado_total = If(final_num > final_den, final_num, final_den)

    solver.add(grado_total <= maxDeg)
        
# La expresión final no supera el grado máximo
# grado_final = []
# for var in range(num_expresiones):
#     depende = []
#     for e in range(num_expresiones):
#         depende.append(If(variables_nuevas[var][e], 1, 0))

#     grado_final.append(If(addsum(depende) > 0, 1, 0))
#     # grado_final.append(If(And(expando[exp], addsum(depende) == 0), 0, 0))
#     # grado_final.append(If(Not(expando[exp]), 1, 0)) # If(exp1 > exp2, exp1, exp2), 0))

# for exp in range(num_expresiones):
#     grado_final.append(If(Not(expando[exp]), 1, 0))

# solver.add(addsum(grado_final) <= maxDeg)

# Si se expande una expresión, obligatoriamente se tiene que unificar con otra.
for exp in range(num_expresiones):
    usada = []
    for var in range(num_expresiones):
        usada.append(If(variables_nuevas[var][exp], 1, 0))

    solver.add(Implies(expando[exp], addsum(usada) > 0))

if solver.check() == sat:
    modelo = solver.model()
    print("Solución encontrada:\n")

    expanden = [i for i in range(num_expresiones) if modelo.evaluate(expando[i]) == True]
    no_expand = [i for i in range(num_expresiones) if modelo.evaluate(expando[i]) == False]

    unificaciones = []
    ya_vistas = set()

    # Crear grupos de unificación basados en variables nuevas usadas
    for i in expanden:
        grupo = [i]
        for j in range(num_expresiones):
            if i != j:
                # Chequear si existe alguna variable nueva que use ambas expresiones i y j
                unificado = False
                for var in range(num_expresiones):
                    if (modelo.evaluate(variables_nuevas[var][i]) == True and
                        modelo.evaluate(variables_nuevas[var][j]) == True):
                        unificado = True
                        break
                if unificado:
                    grupo.append(j)
        grupo_set = frozenset(grupo)
        if len(grupo) > 1 and grupo_set not in ya_vistas:
            unificaciones.append(sorted(grupo))
            ya_vistas.add(grupo_set)

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