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

# parser = argparse.ArgumentParser()

# parser.add_argument("filein", type=str)
# # parser.add_argument("fileout")

# args=parser.parse_args()

# f = open(args.filein)
# data = json.load(f)

# # file = open(args.fileout, "w")

# expresiones = data["expressions"]
# maxDeg = data["degree"]
# num_expresiones = len(expresiones)

# solver = Optimize()

# Para cada expresión, me la quedo tal cual o la expando. Si me la quedo significa que va a ser una "VI" final
# expando = []

# for exp in range(num_expresiones):
#     expando.append(Bool("exp_" + str(exp)))

#     # Minimiza el número de variables "originales"
#     solver.add_soft(expando[exp], 5, "keeps")
    
def suma_fracciones(maxDeg, expresiones):

    solver = Optimize()

    num_expresiones = len(expresiones)

    # Booleano que indica si se junta o no con la expresión i-ésima
    juntar = []

    # juntar_i_j : la expresión original i se junta o no con la expresión original j para formar una nueva expresión. Con j perteneciente a [exp, num_expresiones)
    for exp in range(num_expresiones):
        juntar_exp = []
        for e in range(exp, num_expresiones):
            juntar_exp.append(Bool("juntar_" + str(exp) + "_" + str(e)))
        
        juntar.append(juntar_exp) 

    for exp in range(num_expresiones):
        for e in range(exp + 1, num_expresiones):     
            # Si se cumple esto, se pueden unir. Sino, obligatoriamente el booleano debe ir a false
            # solver.add(Implies(Or(Not(expando[exp]), Not(expando[e])), Not(juntar[exp][e - exp - 1])))

            # Si exp se conecta con e, la fila de e debe estar a false entera, incluido consigo misma
            for col in range(e, num_expresiones):
                solver.add(Implies(juntar[exp][e - exp], Not(juntar[e][col - e])))

            # La columna de e, debe estar a false. Las filas anteriores, excluyendo exp, deben tenerlo a false
            for fila in range(e):
                if fila != exp:
                    solver.add(Implies(juntar[exp][e - exp], Not(juntar[fila][e - fila])))

            # Para que las relaciones entén en la primera fracción que forma la unión de fracciones y no contar el grado 2 veces
            # for anterior in range(0, e - exp - 1):
            #     solver.add(Implies(And(juntar[exp][e - exp - 1], juntar[exp][anterior]), Not(juntar[anterior][e - anterior - 1])))

        # Cuando la fracción por si sola forma un grupo, solo puede tener activa la 0, consigo misma
        for e in range(exp + 1, num_expresiones):
            solver.add(Implies(juntar[exp][0], Not(juntar[exp][e - exp])))

        # Lo mismo para la columna
        # for e in range(exp):
        #     solver.add(Implies(juntar[exp][0], Not(juntar[e][exp - e])))

    # Las variables que se juntan y pasan de grado obligatoriamente tienen que tener su juntar a false
    for exp in range(num_expresiones):
        grado_num_exp = expresiones[exp]["values"][0]["degree"]
        grado_den_exp = expresiones[exp]["values"][1]["degree"] 
        for e in range(exp + 1, num_expresiones):
            grado_num_e = expresiones[e]["values"][0]["degree"]
            grado_den_e = expresiones[e]["values"][1]["degree"]

            # Si se juntan se pasa de grado
            if grado_num_exp + grado_den_e > maxDeg or grado_num_e + grado_den_exp > maxDeg or grado_den_exp + grado_den_e > maxDeg:
                solver.add(Not(juntar[exp][e - exp]))

        # Si la expresión se pasa de grado obligatoriamente tiene que ir sola
        if grado_num_exp > maxDeg or grado_den_exp > maxDeg:
            solver.add(juntar[exp][0]) 
        
    # Comprobar que las expresiones que se forman no superan el grado
    for exp in range(num_expresiones):
        grado_num = [expresiones[exp]["values"][0]["degree"]]
        grado_den = [expresiones[exp]["values"][1]["degree"]]

        for e in range(exp + 1, num_expresiones):
            prev_grado_num = grado_num[-1]
            prev_grado_den = grado_den[-1]

            # max(numerador actual + denominador de e, numerador de e + denominador actual)
            expr1 = prev_grado_num + expresiones[e]["values"][1]["degree"]
            expr2 = prev_grado_den + expresiones[e]["values"][0]["degree"]

            nuevo_grado_num = If(juntar[exp][e - exp], If(expr1 > expr2, expr1, expr2), prev_grado_num)
            nuevo_grado_den = If(juntar[exp][e - exp], prev_grado_den + expresiones[e]["values"][1]["degree"], prev_grado_den)

            # for sig in range(e, num_expresiones):
            #     solver.add(Implies(Or(nuevo_grado_num > maxDeg, nuevo_grado_den > maxDeg), Not(juntar[exp][sig - exp])))

            grado_num.append(nuevo_grado_num)
            grado_den.append(nuevo_grado_den)

        grado_total = If(grado_num[-1] > grado_den[-1], grado_num[-1], grado_den[-1])

        solver.add(grado_total <= maxDeg)

    # Si se expande una expresión, obligatoriamente se tiene que unificar con otra. Variables que realmente cuentan
    for exp in range(num_expresiones):
        suma_fila = []
        suma_col = []
        for e in range(exp, num_expresiones): # En la fila solo puede tener activos los siguientes, incluído él
            suma_fila.append(If(juntar[exp][e - exp], 1, 0))
        
        for e in range(0, exp): # En la columna solo puede estar activo en los anteriores
            suma_col.append(If(juntar[e][exp - e], 1, 0))
        
        solver.add(Or(addsum(suma_fila) > 0, addsum(suma_col) > 0))
        
        # Minimizar número de variables creadas
        solver.add_soft(addsum(suma_fila) == 0, 5, "min_vars")

        # s_fila = addsum(suma_fila)
        # s_col = addsum(suma_col)

        # Cada fracción únicamente está unificada 1 vez
        # solver.add(Implies(s_fila > 0, s_col == 0))
        # solver.add(Implies(s_col > 0, s_fila == 0))
        # solver.add(s_col <= 1)

        # Solo puede ser usada en una variable nueva
        # for e in range(exp + 1, num_expresiones - 1):
        #     for sig in range(exp + 1, e):
        #         solver.add(Implies(juntar[exp][e - exp - 1], Not(juntar[sig][e - sig - 1])))

    if solver.check() == sat:
        modelo = solver.model()
        print("Solución encontrada:\n")

        numV = 1
        for i in range(num_expresiones):
            activos = []
            for j in range(i, num_expresiones):
                if modelo.evaluate(juntar[i][j - i]) == True:
                    activos.append(j)
            
            if len(activos) > 0:
                print(f"→ Fracción {numV}:")
                
                if modelo.evaluate(juntar[i][0] == False):
                    num = expresiones[i]["values"][0]["signals"]
                    den = expresiones[i]["values"][1]["signals"]
                    print(f"      · Exp {i}: ({num}) \\ ({den})")

                for j in activos:
                    num = expresiones[j]["values"][0]["signals"]
                    den = expresiones[j]["values"][1]["signals"]
                    print(f"      · Exp {j}: ({num}) \\ ({den})")
                
                numV += 1

        # print(f"\nNúmero de variables finales: {numV - 1}")
        return numV - 1

    else:
        print("No se encontró una solución válida bajo las restricciones dadas.")
        return 0
