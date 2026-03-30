#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from z3 import *
import json
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
    
def suma_fracciones(maxDegNum, maxDegDen, expressions, original_indices):

    solver = Optimize()

    num_expressions = len(expressions)

    # Booleano que indica si se junta o no con la expresión i-ésima
    join = []

    # join_i_j : la expresión original i se junta o no con la expresión original j para formar una nueva expresión. Con j perteneciente a [exp, num_expressions)
    for exp in range(num_expressions): # Sólo se define el triángulo superior
        join_exp = []
        for e in range(exp, num_expressions):
            join_exp.append(Int("join_" + str(exp) + "_" + str(e))) # Para controlar el número de variables creadas, en vez de booleanos, pongo enteros que indican el número de fracciones que se juntan en esa posición
        
        join.append(join_exp) 
    
    for exp in range(num_expressions):
        for e in range(exp, num_expressions):
            solver.add(Or(join[exp][e - exp] == 0, join[exp][e - exp] == 1)) 

        # La columna de e, debe estar a false si se junta exp con e. Las filas anteriores, excluyendo exp, deben tenerlo a false
        # for row in range(e):
        #     if row != exp:
        #         solver.add(Implies(join[exp][e - exp], Not(join[row][e - row])))

            # Para que las relaciones entén en la primera fracción que forma la unión de fracciones y no contar el grado 2 veces
            # for anterior in range(0, e - exp - 1):
            #     solver.add(Implies(And(join[exp][e - exp - 1], join[exp][anterior]), Not(join[anterior][e - anterior - 1])))

        # Cuando la fracción por si sola forma un grupo, solo puede tener activa la 0, consigo misma
        # for e in range(exp + 1, num_expressions):
        # solver.add(Implies(join[exp][0], Not(join[exp][e - exp])))

        # Lo mismo para la columna
        # for e in range(exp):
        #     solver.add(Implies(join[exp][0], Not(join[e][exp - e])))

    # Grados de numerador y denominador de las expresiones
    degrees_num = []
    degrees_den = []

    for exp in range(num_expressions):
        degrees_num.append(expressions[exp]["values"][0]["degree"])
        degrees_den.append(expressions[exp]["values"][1]["degree"])

    # Las variables que se juntan y pasan de grado obligatoriamente tienen que tener su join a false # OPTIMIZACIÓN DEL SOLVER
    for exp in range(num_expressions):
        for e in range(exp + 1, num_expressions):
            # Si se juntan se pasa de grado
            if degrees_num[exp] + degrees_den[e] > maxDegNum or degrees_num[e] + degrees_den[exp] > maxDegNum or degrees_den[exp] + degrees_den[e] > maxDegDen:
                solver.add(join[exp][e - exp] == 0)

    columnas = []
    for exp in range(num_expressions):
        col_exp = []
        for e in range(0, exp + 1): # En la columna solo puede estar activo en los anteriores
            col_exp.append(join[e][exp - e])
        
        columnas.append(col_exp)
    
    for exp in range(num_expressions):
        solver.add(addsum(columnas[exp]) == 1)  # Cada fracción EXACTAMENTE en 1 grupo

    # Comprobar que las expressions que se forman no superan el grado
    # for exp in range(num_expressions):
    #     # deg_num = []
    #     # deg_den = []
    #     # deg_num.append(degrees_num[exp] * join[exp][0]) # Si se junta consigo misma, el grado es el mismo, si no, 0
    #     # deg_den.append(degrees_den[exp] * join[exp][0])
    #     curr_num = degrees_num[exp]
    #     curr_den = degrees_den[exp]

    #     for e in range(exp + 1, num_expressions):
    #         expr1 = curr_num + degrees_den[e]
    #         expr2 = curr_den + degrees_num[e]

    #         max_deg_exp = If(expr1 > expr2, expr1, expr2)

    #         curr_num = If(join[exp][e - exp] == 1, max_deg_exp, curr_num)
    #         curr_den = If(join[exp][e - exp] == 1, curr_den + degrees_den[e], curr_den)

    #     solver.add(curr_num <= maxDegNum)
    #     solver.add(curr_den <= maxDegDen)

    # degs_num = []
    # degs_den = []
    for exp in range(num_expressions):
        # dg_num = []
        curr_den = []
        # curr_den.append(degrees_den[exp] * join[exp][0])

        for e in range(exp, num_expressions):
            curr_den.append(degrees_den[e] * join[exp][e - exp])

        den_comun = addsum(curr_den)
        solver.add(den_comun <= maxDegDen)

        for e in range(exp, num_expressions):
            # dg_num.append(degrees_num[e] + (den_comun - degrees_den[e] * join[exp][e - exp]))
            solver.add((den_comun + (degrees_num[e] - degrees_den[e]) * join[exp][e - exp]) <= maxDegNum)
        
        # degs_num.append(dg_num)
        # degs_den.append(den_comun)

    # Variables que realmente cuentan
    # for exp in range(num_expressions):
        # Obligo a que se junte 100% con alguien, ya sea en fila o en columna
        # solver.add(Or(addsum(join[exp]) > 0, addsum(columnas[exp]) > 0))  
    
    # Minimizar número de variables creadas --> Minimizar la suma de la diagonal
    diagonal = []
    for exp in range(num_expressions):
        diagonal.append(join[exp][0])
    solver.minimize(addsum(diagonal))

    # for exp in range(num_expressions):
    #     print(f"Grado numerador {original_indices[exp]}: {degrees_num[exp]}, grado denominador: {degrees_den[exp]}")

    if solver.check() == sat:
        modelo = solver.model()
        print(f"Solution found for degNum {maxDegNum} and degDen {maxDegDen}:\n")

        grupos = []
        sum_id = 0
        usados = set()  # Para no repetir fracciones

        for i in range(num_expressions):
            if i in usados:
                continue

            # Construimos la lista de fracciones que se suman en este grupo
            grupo_actual = [original_indices[i]]
            usados.add(i)
            # print(f"Grado num para {original_indices[i]}: {modelo.evaluate(degs_num[i][0])}, grado den {modelo.evaluate(degs_den[i])}")

            for j in range(i + 1, num_expressions):
                if modelo.evaluate(join[i][j - i]) == 1:
                    grupo_actual.append(original_indices[j])
                    # print(f"Grado num para {original_indices[j]} en {original_indices[i]}: {modelo.evaluate(degs_num[i][j - i])}, grado den {modelo.evaluate(degs_den[i])}")
                    usados.add(j)

            grupos.append({"sum": sum_id, "fractions": grupo_actual})
            sum_id += 1

        return grupos

    else:
        print("No se encontró una solución válida bajo las restricciones dadas.")
        return 0

# parser = argparse.ArgumentParser()
# parser.add_argument("input", help="Input JSON file")
# args = parser.parse_args()

# with open(args.input, "r") as f:
#     data = json.load(f)

# indices = []
# for exp in range(len(data["expressions"])):
#     indices.append(exp)

# resultado = suma_fracciones(data["degree"], data["degree"] - 1, data["expressions"], indices)
# print("\n--- Resultado de sumas ---")
# for g in resultado:
#     frs = g["fractions"]
#     cadena = " + ".join(f"fraction {f}" for f in frs)
#     print(f"sum{g['sum']} = {cadena}")