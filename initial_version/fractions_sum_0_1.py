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
    
def print_solution(model, join, degs_num, degs_den, original_indices, num_expressions, maxDegNum, maxDegDen):
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
        
        # Grados de la expresión en i
        deg_num_i = model.evaluate(degs_num[i][0])
        deg_den_i = model.evaluate(degs_den[i])

        for j in range(i + 1, num_expressions):
            if model.evaluate(join[i][j - i]) == 1:
                grupo_actual.append(original_indices[j])
                usados.add(j)

        grupos.append({"sum": sum_id, "fractions": grupo_actual})
        
        # Mostrar grados finales
        # print(f"Grupo {sum_id} (expresiones {grupo_actual}):")
        # print(f"  Grado numerador:   {deg_num_i}")
        # print(f"  Grado denominador: {deg_den_i}")
        
        sum_id += 1

    return grupos
    
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

    # Si una fraccion tiene su variable [exp][0] a 0, el resto de la fila tiene que ser 0
    for exp in range(num_expressions):
        for e in range(exp + 1, num_expressions):
            # solver.add(Implies(join[exp][0] == 0, join[exp][e - exp] == 0))
            solver.add(join[exp][e - exp] <= join[exp][0])

    columnas = []
    for exp in range(num_expressions):
        col_exp = []
        for e in range(0, exp + 1): # En la columna solo puede estar activo en los anteriores
            col_exp.append(join[e][exp - e])
        
        columnas.append(col_exp)
        solver.add(addsum(columnas[exp]) == 1)  # Cada fracción EXACTAMENTE en 1 grupo
    
    degs_num = []
    degs_den = []
    for exp in range(num_expressions):
        dg_num = []
        curr_den = []

        for e in range(exp, num_expressions):
            curr_den.append(degrees_den[e] * join[exp][e - exp])

        den_comun = addsum(curr_den)
        solver.add(den_comun <= maxDegDen)

        for e in range(exp, num_expressions):
            dg_num.append((degrees_num[e] + den_comun - degrees_den[e]) * join[exp][e - exp])
            solver.add((den_comun + degrees_num[e] - degrees_den[e]) * join[exp][e - exp] <= maxDegNum)
        
        degs_num.append(dg_num)
        degs_den.append(den_comun)
    
    # Minimizar número de variables creadas --> Minimizar la suma de la diagonal
    diagonal = []
    for exp in range(num_expressions):
        diagonal.append(join[exp][0])
    
    # Minimize es muy lento con casos grande, se hace búsqueda incremental para encontrar el mínimo número de variables intermedias
    # solver.minimize(addsum(diagonal))

    for k in range(1, num_expressions + 1):
        solver.push()
        solver.add(addsum(diagonal) <= k)
        
        if solver.check() == sat:
            model = solver.model()
            
            return print_solution(model, join, degs_num, degs_den, original_indices, num_expressions, maxDegNum, maxDegDen)
        
        solver.pop()
    
    print("No se encontró una solución válida bajo las restricciones dadas.")
    return 0