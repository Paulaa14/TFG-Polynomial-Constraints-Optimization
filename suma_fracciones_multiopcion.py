#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from z3 import *
import json
import argparse

def addsum(a):
    if len(a) == 0:
        return IntVal(0)
    else:
        asum = a[0]
        for i in range(1,len(a)):
            asum = asum + a[i]
        return asum
    
def suma_fracciones_multiopcion(maxDegNum, maxDegDen, expressions):

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

    options = []
    # Para cada expresion, qué opción se usa
    for exp in range(num_expressions):
        options.append(Int("used_option_in_exp_" + str(exp)))
    
    for exp in range(num_expressions):
        solver.add(And(options[exp] >= 0, options[exp] < len(expressions[exp])))

    for exp in range(num_expressions):
        for e in range(exp + 1, num_expressions):     
            # Si se cumple esto, se pueden unir. Sino, obligatoriamente el booleano debe ir a false
            # solver.add(Implies(Or(Not(expando[exp]), Not(expando[e])), Not(join[exp][e - exp - 1])))

            # Si exp se conecta con e, la fila de e debe estar a false entera, incluido consigo misma
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
            solver.add(Implies(join[exp][0], Not(join[exp][e - exp])))

        # Lo mismo para la columna
        # for e in range(exp):
        #     solver.add(Implies(join[exp][0], Not(join[e][exp - e])))

    # Grados de numerador y denominador de las expresiones y sus opciones (matriz)
    degrees_num = []
    degrees_den = []

    for exp in range(num_expressions):
        degrees_num_exp = []
        degrees_den_exp = []

        # Opciones
        for option in range(len(expressions[exp])):
            degrees_num_exp.append(expressions[exp][option]["values"][0]["degree"])
            degrees_den_exp.append(expressions[exp][option]["values"][1]["degree"])

        degrees_num.append(degrees_num_exp)
        degrees_den.append(degrees_den_exp)

    # Las variables que se juntan y pasan de grado obligatoriamente tienen que tener su join a false # OPTIMIZACIÓN DEL SOLVER
    for exp in range(num_expressions):
        for e in range(exp + 1, num_expressions):
            # Si se juntan se pasa de grado
            for opc_exp in range(len(expressions[exp])):
                for opc_e in range(len(expressions[e])):
                    if degrees_num[exp][opc_exp] + degrees_den[e][opc_e] > maxDegNum or degrees_num[e][opc_e] + degrees_den[exp][opc_exp] > maxDegNum or degrees_den[exp][opc_exp] + degrees_den[e][opc_e] > maxDegDen:
                        solver.add(Implies(And(options[exp] == opc_exp, options[e] == opc_e), Not(join[exp][e - exp])))

            # for previous in range(exp): # AÑADIDO DESPUES
            #     solver.add(Implies(join[previous][exp - previous], Not(join[previous][e - previous])))

        # Si la expresión se pasa de grado obligatoriamente tiene que ir sola
        # if degree_num_exp > maxDeg or degree_den_exp > maxDeg:
        #     solver.add(join[exp][0]) 
        
    # Comprobar que las expressions que se forman no superan el grado
    for exp in range(num_expressions):

        for option_exp in range(len(expressions[exp])):
            curr_num_exp = If(options[exp] == option_exp, degrees_num[exp][option_exp], 0)
            curr_den_exp = If(options[exp] == option_exp, degrees_den[exp][option_exp], 0)

            for e in range(exp + 1, num_expressions):

                for option_e in range(len(expressions[e])):

                    curr_num_e = If(options[e] == option_e, degrees_num[e][option_e], 0)
                    curr_den_e = If(options[e] == option_e, degrees_den[e][option_e], 0)

                    expr1 = curr_num_exp + curr_den_e
                    expr2 = curr_den_exp + curr_num_e

                    max_deg_exp = If(expr1 > expr2, expr1, expr2)

                    curr_num_exp = If(join[exp][e - exp], max_deg_exp, curr_num_exp)
                    curr_den_exp = If(join[exp][e - exp], curr_den_exp + curr_den_e, curr_den_exp)

            solver.add(curr_num_exp <= maxDegNum)
            solver.add(curr_den_exp <= maxDegDen)

    # Variables que realmente cuentan
    for exp in range(num_expressions):
        add_row = []
        add_col = []
        for e in range(exp, num_expressions): # En la fila solo puede tener activos los siguientes, incluído él
            add_row.append(If(join[exp][e - exp], 1, 0))
        
        for e in range(0, exp): # En la columna solo puede estar activo en los anteriores
            add_col.append(If(join[e][exp - e], 1, 0))
        
        # Obligo a que se junte 100% con alguien, ya sea en fila o en columna
        solver.add(Or(addsum(add_row) > 0, addsum(add_col) > 0))
        
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

        grupos = []
        sum_id = 1
        usados = set()  # Para no repetir fracciones

        for i in range(num_expressions):
            if i in usados:
                continue

            # Construimos la lista de fracciones que se suman en este grupo
            grupo_actual = [i]
            usados.add(i)

            for j in range(i+1, num_expressions):
                if modelo.evaluate(join[i][j - i]):
                    grupo_actual.append(j)
                    usados.add(j)

            grupos.append({"sum": sum_id, "fractions": grupo_actual})
            sum_id += 1

        # Información de options y grados de numerador/denominador para cada expresión
        options_info = []
        for i in range(num_expressions):
            opt = modelo.evaluate(options[i]).as_long()
            grado_num = degrees_num[i][opt]
            grado_den = degrees_den[i][opt]
            options_info.append({
                "expression": i,
                "selected_option": opt,
                "degree_num": grado_num,
                "degree_den": grado_den
            })

        # Imprimir por pantalla los options y grados seleccionados para cada expresión
        print("Opciones seleccionadas y grados por expresión:")
        for info in options_info:
            print(f"Expresión {info['expression']}: opción {info['selected_option']}, grado_num={info['degree_num']}, grado_den={info['degree_den']}")

        resultado = {
            "groups": grupos,
            "options": options_info
        }

        print("Resultado JSON:")
        print(resultado)

        return resultado

    else:
        print("No se encontró una solución válida bajo las restricciones dadas.")
        return 0
    
parser = argparse.ArgumentParser()
parser.add_argument("input", help="Input JSON file")
args = parser.parse_args()

with open(args.input, "r") as f:
    data = json.load(f)

suma_fracciones_multiopcion(data["degree"], data["degree"] - 1, data["expressions"])
