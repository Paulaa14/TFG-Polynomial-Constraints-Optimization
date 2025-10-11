#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from z3 import *
import argparse

def addsum(a):
    if len(a) == 0:
        return IntVal(0)
    else:
        asum = a[0]
        for i in range(1,len(a)):
            asum = asum + a[i]
        return asum
    
# Meter variables que representan la fracción, cuántas variables se cogen en el numerador, y cuántas en el denominador

parser = argparse.ArgumentParser()

parser.add_argument("filein", type=str)
parser.add_argument("fileout", type=str)

args=parser.parse_args()

f = open(args.filein)
data = json.load(f)

file = open(args.fileout, "w")

# Grado del numerador original
degree_num = data["degree_num"]

# Grado del denominador original
degree_den = data["degree_den"]
maxDeg = data["degree"]

solver = Optimize()

##### PARAMETROS #####
max_intermedias = 8

# Cada variable, cuántas variables de las originales tiene del numerador, y cuántas del denominador. Cada variables es un nivel.
# Las variables del numerador se colocaraán en el numerador de la nueva variable y las del denominador en el denominador
num_variables_originales_var_num = []
num_variables_originales_var_den = []

for var in range(max_intermedias):
    num_variables_originales_var_num.append(Int("num_var_" + str(var)))
    num_variables_originales_var_den.append(Int("den_var_" + str(var)))

# Rango de las variables
for var in range(max_intermedias):
    solver.add(And(num_variables_originales_var_num[var] >= 0, num_variables_originales_var_num[var] <= maxDeg))
    solver.add(And(num_variables_originales_var_den[var] >= 0, num_variables_originales_var_den[var] <= maxDeg))

# Cada una de las variables intermedias, utiliza alguna de las variables intermedias anteriores o no. 
# La primera lógicamente no va a utilizar ninguna variable anterior, con el bucle interior ya se cubre ese caso
usa_var_anterior_num = []
usa_var_anterior_den = []

for var in range(max_intermedias): # Se podría poner como rango 1 - max_intermedias para ahorrar una vuelta
    cuales_usa_n = []
    cuales_usa_d = []

    for anterior in range(var):
        cuales_usa_n.append(Bool("var_" + str(var) + "_usan_" + str(anterior)))
        cuales_usa_d.append(Bool("var_" + str(var) + "_usad_" + str(anterior)))

    usa_var_anterior_num.append(cuales_usa_n)
    usa_var_anterior_den.append(cuales_usa_d)

# Para cada variable, cuántas variables originales realmente cubre teniendo en cuenta las originales que tiene de num_variables_originales_var + las que tiene cada variable anterior que contiene
cuantas_variables_cubre_num = []
cuantas_variables_cubre_den = []

for var in range(max_intermedias):
    cuantas_n = []
    cuantas_d = []
    cuantas_n.append(num_variables_originales_var_num[var])
    cuantas_d.append(num_variables_originales_var_den[var])

    # Si utiliza una variable anterior ahora cubre todas las que tuviera ella también + las suyas
    for anterior in range(var):
        cuantas_n.append(If(usa_var_anterior_num[var][anterior], cuantas_variables_cubre_num[anterior] + cuantas_variables_cubre_den[anterior], 0))
        cuantas_d.append(If(usa_var_anterior_den[var][anterior], cuantas_variables_cubre_num[anterior] + cuantas_variables_cubre_den[anterior], 0))

    cuantas_variables_cubre_num.append(addsum(cuantas_n))
    cuantas_variables_cubre_den.append(addsum(cuantas_d))

# Solo puede ocurrir o que la variable esté fomarda por n/n-1, n-1/n o que esté vacía tanto en numerador como denominador
for var in range(max_intermedias):
    n_num = And(cuantas_variables_cubre_num[var] == maxDeg, cuantas_variables_cubre_den[var] == maxDeg - 1)
    n_den = And(cuantas_variables_cubre_num[var] == maxDeg - 1, cuantas_variables_cubre_den[var] == maxDeg)
    zero = And(cuantas_variables_cubre_num[var] == 0, cuantas_variables_cubre_den[var] == 0)

    solver.add(Or(n_num, Or(n_den, zero)))

# Si la variable es de la forma n/(n - 1) se utilizará en el numerador y si tiene la forma (n - 1)/n se utilizará en el denominador
for var in range(max_intermedias):

    for anterior in range(var):
        solver.add(Implies(cuantas_variables_cubre_num[anterior] == maxDeg, Not(usa_var_anterior_den[var][anterior])))
        solver.add(Implies(cuantas_variables_cubre_den[anterior] == maxDeg, Not(usa_var_anterior_num[var][anterior])))
        solver.add(Implies(cuantas_variables_cubre_num[anterior] == 0, Not(Or(usa_var_anterior_num[var][anterior], usa_var_anterior_den[var][anterior]))))

# Grado de cada variable: el máximo entre el grado del numerador y del denominador
for var in range(max_intermedias):
    grado_num = []
    grado_den = []
    grado_num.append(num_variables_originales_var_num[var])
    grado_den.append(num_variables_originales_var_den[var])

    for anterior in range(var):
        # Si utiliza una variable anterior, aporta grado 1
        grado_num.append(If(usa_var_anterior_num[var][anterior], 1, 0))
        grado_den.append(If(usa_var_anterior_den[var][anterior], 1, 0))

    solver.add(And(addsum(grado_num) <= maxDeg, addsum(grado_den) <= maxDeg))

# Contar que se cubren todas las variables que había al inicio

# Orden en variables, si esta está vacía, todas las demás tmb


# Minimizar el número de variables
for var in range(max_intermedias):
    solver.add_soft(And(cuantas_variables_cubre_num[var] == 0, cuantas_variables_cubre_den[var] == 0), 1, "min_vars")

if solver.check() == sat:
    m = solver.model()
    print("Variables intermedias formadas:")

    for var in range(max_intermedias):
        num = m.eval(num_variables_originales_var_num[var], model_completion=True).as_long()
        den = m.eval(num_variables_originales_var_den[var], model_completion=True).as_long()
        cubre_num = m.eval(cuantas_variables_cubre_num[var], model_completion=True).as_long()
        cubre_den = m.eval(cuantas_variables_cubre_den[var], model_completion=True).as_long()

        deps_num = []
        deps_den = []

        for anterior in range(var):
            val_num = m.eval(usa_var_anterior_num[var][anterior], model_completion=True)
            val_den = m.eval(usa_var_anterior_den[var][anterior], model_completion=True)
            if is_true(val_num):
                deps_num.append(f"VI_{anterior}")
            if is_true(val_den):
                deps_den.append(f"VI_{anterior}")

        dep_str = ""
        if deps_num or deps_den:
            dep_str += " ("
            if deps_num:
                dep_str += f"num depende de: {', '.join(deps_num)}"
            if deps_den:
                if deps_num:
                    dep_str += "; "
                dep_str += f"den depende de: {', '.join(deps_den)}"
            dep_str += ")"

        print(f"VI_{var}: num = {num}, den = {den}, cubre {cubre_num} en num y {cubre_den} en den{dep_str}")

    # Identificar variables que podrían usarse en el producto final (opcional)
    usadas_num = []
    usadas_den = []

    for var in range(max_intermedias):
        cubre_num = m.eval(cuantas_variables_cubre_num[var], model_completion=True).as_long()
        cubre_den = m.eval(cuantas_variables_cubre_den[var], model_completion=True).as_long()

        # Suponemos que las del tipo n/(n-1) van al numerador, y (n-1)/n al denominador
        if cubre_num == maxDeg and cubre_den == maxDeg - 1:
            usadas_num.append(f"VI_{var}")
        elif cubre_num == maxDeg - 1 and cubre_den == maxDeg:
            usadas_den.append(f"VI_{var}")

    # Mostrar producto final estimado
    producto_str = " * ".join(usadas_num) if usadas_num else "1"
    producto_str_den = " * ".join(usadas_den) if usadas_den else "1"

    print(f"\nProducto final: ({producto_str}) / ({producto_str_den})")

else:
    print("No hay solución.")
