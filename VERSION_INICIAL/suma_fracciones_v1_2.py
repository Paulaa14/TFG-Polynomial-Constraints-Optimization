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
            join_exp.append(Bool("join_" + str(exp) + "_" + str(e)))
        
        join.append(join_exp) 

    for exp in range(num_expressions):
        for e in range(exp, num_expressions):     
            # Si se cumple esto, se pueden unir. Sino, obligatoriamente el booleano debe ir a false
            # solver.add(Implies(Or(Not(expando[exp]), Not(expando[e])), Not(join[exp][e - exp - 1])))

            # Si exp se conecta con e, la fila de e debe estar a false entera, incluido consigo misma
            if exp != e: # Cuando se junte consigo mismo no tiene que estar el resto de la fila a false
                for col in range(e, num_expressions):
                    solver.add(Implies(join[exp][e - exp], Not(join[e][col - e])))

            # La columna de e, debe estar a false si se junta exp con e. Las filas anteriores, excluyendo exp, deben tenerlo a false
            for row in range(e):
                if row != exp:
                    solver.add(Implies(join[exp][e - exp], Not(join[row][e - row])))

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
                solver.add(Not(join[exp][e - exp]))

                # for previous in range(exp): # AÑADIDO DESPUES
                #     solver.add(Implies(join[previous][exp - previous], Not(join[previous][e - previous])))
        
    # Comprobar que las expressions que se forman no superan el grado
    # for exp in range(num_expressions):
    #     curr_num = degrees_num[exp]
    #     curr_den = degrees_den[exp]

    #     for e in range(exp + 1, num_expressions):
    #         expr1 = curr_num + degrees_den[e]
    #         expr2 = curr_den + degrees_num[e]

    #         max_deg_exp = If(expr1 > expr2, expr1, expr2)

    #         curr_num = If(join[exp][e - exp], max_deg_exp, curr_num)
    #         curr_den = If(join[exp][e - exp], curr_den + degrees_den[e], curr_den)

    #     solver.add(curr_num <= maxDegNum)
    #     solver.add(curr_den <= maxDegDen)

    # Comprobar grado de las expresiones que se forman
    degs_num = []
    degs_den = []
    
    for exp in range(num_expressions):
        curr_den = []

        for e in range(exp, num_expressions):
            curr_den.append(If(join[exp][e - exp], degrees_den[e], 0))
        
        den_comun = addsum(curr_den)
        solver.add(den_comun <= maxDegDen)

        dg_num_list = []
        for e in range(exp, num_expressions):   
            dg_num = degrees_num[e] + (den_comun - degrees_den[e])
            solver.add(If(join[exp][e - exp], dg_num, 0) <= maxDegNum)
            dg_num_list.append(dg_num)
        
        degs_num.append(dg_num_list)
        degs_den.append(den_comun)

    # Variables que realmente cuentan
    for exp in range(num_expressions):
        add_row = []
        add_col = []
        for e in range(exp, num_expressions): # En la fila solo puede tener activos los siguientes, incluído él
            add_row.append(If(join[exp][e - exp], 1, 0))
        
        for e in range(0, exp + 1): # En la columna solo puede estar activo en los anteriores y en la suya
            add_col.append(If(join[e][exp - e], 1, 0))
        
        # Obligo a que se junte 100% con alguien, ya sea en fila o en columna
        # solver.add(Or(addsum(add_row) > 0, addsum(add_col) > 0))
        solver.add(addsum(add_col) == 1)
        
        # Minimizar número de variables creadas
        solver.add_soft(addsum(add_row) == 0, 1, "min_vars")

        # s_fila = addsum(add_row)
        # s_col = addsum(add_col)

        # Cada fracción únicamente está unificada 1 vez
        # solver.add(Implies(s_fila > 0, s_col == 0))
        # solver.add(Implies(s_col > 0, s_fila == 0))
        # solver.add(s_col <= 1)

        # Solo puede ser usada en una variable nueva
        # for e in range(exp + 1, num_expressions - 1):
        #     for sig in range(exp + 1, e):
        #         solver.add(Implies(join[exp][e - exp - 1], Not(join[sig][e - sig - 1])))

    if solver.check() == sat:
        modelo = solver.model()
        print("Solution found:\n")

        # # Mostrar matriz de variables join
        # print("Matriz de variables join (triángulo superior):")
        # print("-" * 60)
        # matriz_join = []
        # for exp in range(num_expressions):
        #     fila = []
        #     for e in range(exp, num_expressions):
        #         valor_z3 = modelo.evaluate(join[exp][e - exp])
        #         # Convertir Bool a 0/1 o Int directamente
        #         if str(valor_z3) == 'True':
        #             valor = 1
        #         elif str(valor_z3) == 'False':
        #             valor = 0
        #         else:
        #             valor = int(str(valor_z3))
        #         fila.append(valor)
        #     matriz_join.append(fila)
        
        # # Mostrar encabezado
        # print("   ", end="")
        # for j in range(num_expressions):
        #     print(f"  {j}", end="")
        # print()
        
        # # Mostrar matriz
        # for i, fila in enumerate(matriz_join):
        #     print(f"{i}: ", end="")
        #     # Espacios vacíos antes del triángulo
        #     for _ in range(i):
        #         print("  -", end="")
        #     # Valores del triángulo
        #     for valor in fila:
        #         print(f"  {valor}", end="")
        #     print()
        # print()

        grupos = []
        sum_id = 0
        usados = set()  # Para no repetir fracciones

        for i in range(num_expressions):
            if i in usados:
                continue

            # Construimos la lista de fracciones que se suman en este grupo
            grupo_actual = [original_indices[i]]
            usados.add(i)

            for j in range(i+1, num_expressions):
                if modelo.evaluate(join[i][j - i]):
                    grupo_actual.append(original_indices[j])
                    usados.add(j)

            grupos.append({"sum": sum_id, "fractions": grupo_actual})
            
            # Mostrar grados finales
            deg_num_i = modelo.evaluate(degs_num[i][0])
            deg_den_i = modelo.evaluate(degs_den[i])
            
            # print(f"Grupo {sum_id} (expresiones {grupo_actual}):")
            # print(f"  Grado numerador:   {deg_num_i}")
            # print(f"  Grado denominador: {deg_den_i}")
            
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