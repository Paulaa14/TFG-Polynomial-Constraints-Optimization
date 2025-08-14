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

parser = argparse.ArgumentParser()

parser.add_argument("filein", type=str)
parser.add_argument("fileout", type=str)

args=parser.parse_args()

f = open(args.filein)
data = json.load(f)

file = open(args.fileout, "w")

degree_num = data["degree_num"]
degree_den = data["degree_den"]
maxDeg = data["degree"]

solver = Optimize()

##### PARAMETROS #####
max_intermedias = 5

# Cada variable intermedia nueva que se crea, cuántas variables tiene en el numerador y cuántas en el denominador
num_variables_num = []
num_variables_den = []

# Cada variable, cuántas variables del inicio cubre, teniendo en cuenta las que contienen otras VI que pueda contener
cuantas_variables_num = []
cuantas_variables_den = []

# Cada variable intermedia nueva que se crea, utiliza alguna variable creada anteriormente o no
variables_anteriores = []

for variable in range(max_intermedias):
    num_variables_num.append(Int("num_" + str(variable)))
    num_variables_den.append(Int("den_" + str(variable)))

    cuantas_variables_num.append(Int("variables_num_" + str(variable)))
    cuantas_variables_den.append(Int("variables_den_" + str(variable)))

    vars = []
    for anterior in range(variable):
        vars.append(Bool("var_anterior_" + str(anterior)))
    variables_anteriores.append(vars)

numero_anteriores_var_num = []
numero_anteriores_var_den = []

for variable in range(max_intermedias):
    num = []
    den = []
    cuantas_num = []
    cuantas_den = []

    for anterior in range(variable):
        num.append(If(And(variables_anteriores[variable][anterior], num_variables_num[anterior] == maxDeg), 1, 0))
        den.append(If(And(variables_anteriores[variable][anterior], num_variables_den[anterior] == maxDeg), 1, 0))

        cuantas_num.append(If(And(variables_anteriores[variable][anterior], num_variables_num[anterior] == maxDeg), cuantas_variables_num[anterior], 0))
        cuantas_den.append(If(And(variables_anteriores[variable][anterior], num_variables_den[anterior] == maxDeg), cuantas_variables_den[anterior], 0))

    numero_anteriores_var_num.append(addsum(num))
    numero_anteriores_var_den.append(addsum(den))

    solver.add(cuantas_variables_num[variable] == addsum(cuantas_num) + num_variables_num[variable])
    solver.add(cuantas_variables_den[variable] == addsum(cuantas_den) + num_variables_den[variable])

grado_num_var = []
grado_den_var = []

for variable in range(max_intermedias):
    grado_num_var.append(num_variables_num[variable] + numero_anteriores_var_num[variable])
    grado_den_var.append(num_variables_den[variable] + numero_anteriores_var_den[variable])

# Dominio de las variables
for variable in range(max_intermedias):
    # solver.add(num_variables_num[variable] >= 0)
    # solver.add(num_variables_den[variable] >= 0)
    # solver.add(num_variables_num[variable] <= maxDeg)
    # solver.add(num_variables_den[variable] <= maxDeg)
    
    solver.add(Implies(grado_num_var[variable] == maxDeg, grado_den_var[variable] == maxDeg - 1))
    solver.add(Implies(grado_den_var[variable] == maxDeg, grado_num_var[variable] == maxDeg - 1))
    solver.add(Or(And(grado_num_var[variable] == maxDeg, grado_den_var[variable] == maxDeg - 1), And(grado_den_var[variable] == maxDeg, grado_num_var[variable] == maxDeg - 1)))
    # También permitir variables vacías


    # for anterior in range(variable):
    #     solver.add(variables_anteriores[variable][anterior] >= 0)
    #     solver.add(variables_anteriores[variable][anterior] <= maxDeg)

# for variable in range(max_intermedias):
#     grado_num = []
#     grado_den = []
#     grado_num.append(num_variables_num[variable])
#     grado_den.append(num_variables_den[variable])

#     # for anterior in range(variable):
#     #     grado_num.append(If(num_variables_num[anterior] == maxDeg, variables_anteriores[variable][anterior], 0))
#     #     grado_den.append(If(num_variables_den[anterior] == maxDeg, variables_anteriores[variable][anterior], 0))

#     solver.add(addsum(grado_num) <= maxDeg)
#     solver.add(addsum(grado_den) <= maxDeg)

# El producto final, utiliza la variable nueva iésima o no
producto_final_vars_num = []
producto_final_vars_den = []

for variable in range(max_intermedias):
    producto_final_vars_num.append(Bool("final_var_num_" + str(variable)))
    producto_final_vars_den.append(Bool("final_var_den_" + str(variable)))

    # No pueden ser ambas ciertas a la vez
    solver.add(Not(And(producto_final_vars_num[variable], producto_final_vars_den[variable])))

producto_final_ini_num = Int("final_num")
producto_final_ini_den = Int("final_den")

solver.add(producto_final_ini_num >= 0)
solver.add(producto_final_ini_den >= 0)
solver.add(producto_final_ini_num <= maxDeg)
solver.add(producto_final_ini_den <= maxDeg)

grado_final_num = []
grado_final_den = []

for variable in range(max_intermedias):
    grado_final_num.append(If(And(grado_num_var[variable] == maxDeg, producto_final_vars_num[variable]), 1, 0))
    grado_final_den.append(If(And(grado_den_var[variable] == maxDeg, producto_final_vars_den[variable]), 1, 0))

solver.add(addsum(grado_final_num) + producto_final_ini_num <= maxDeg)
solver.add(addsum(grado_final_den) + producto_final_ini_den <= maxDeg)

# Cubre variables
cubre_num = []
cubre_den = []

for variable in range(max_intermedias):
    cubre_num.append(If(producto_final_vars_num[variable], cuantas_variables_num[variable], 0))
    cubre_den.append(If(producto_final_vars_den[variable], cuantas_variables_den[variable], 0))

solver.add(addsum(cubre_num) + producto_final_ini_num == degree_num)
solver.add(addsum(cubre_den) + producto_final_ini_den == degree_den)

for variable in range(max_intermedias):
    solver.add_soft(Not(Or(producto_final_vars_num[variable], producto_final_vars_den[variable])), 1, "min_vars")


if solver.check() == sat:
    m = solver.model()
    print("Variables intermedias formadas:")
    for variable in range(max_intermedias):
        num = m.eval(grado_num_var[variable], model_completion=True).as_long()
        den = m.eval(grado_den_var[variable], model_completion=True).as_long()
        print(f"VI_{variable}: Numerador = {num}, Denominador = {den}")

    # print("\nVariables utilizadas en el producto final (numerador):")
    usadas_num = []
    for variable in range(max_intermedias):
        val = m.eval(producto_final_vars_num[variable], model_completion=True)
        if is_true(val):
            num = m.eval(grado_num_var[variable], model_completion=True).as_long()
            # print(f"VI_{variable}")
            usadas_num.append(f"VI_{variable}")

    # print("\nVariables utilizadas en el producto final (denominador):")
    usadas_den = []
    for variable in range(max_intermedias):
        val = m.eval(producto_final_vars_den[variable], model_completion=True)
        if is_true(val):
            den = m.eval(grado_den_var[variable], model_completion=True).as_long()
            # print(f"VI_{variable}")
            usadas_den.append(f"VI_{variable}")

    ini_num = m.eval(producto_final_ini_num, model_completion=True).as_long()
    ini_den = m.eval(producto_final_ini_den, model_completion=True).as_long()

    partes_num = []
    partes_den = []
    if ini_num > 0:
        partes_num.append(f"{ini_num} iniciales")
    if ini_den > 0:
        partes_den.append(f"{ini_den} iniciales")
    partes_num += usadas_num
    partes_den += usadas_den

    producto_str = " * ".join(partes_num) if partes_num else "1"
    producto_str_den = " * ".join(partes_den) if partes_den else "1"
    print(f"\nProducto final: ({producto_str}) / ({producto_str_den})")
else:
    print("No hay solución.")