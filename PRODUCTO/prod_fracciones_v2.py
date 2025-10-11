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

degree_num = data["degree_num"]
degree_den = data["degree_den"]
maxDeg = data["degree"]

solver = Optimize()

##### PARAMETROS #####
max_intermedias = 8

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

# Cuántas variables de un nivel anterior, tiene en numerador y denominador
numero_anteriores_var_num = []
numero_anteriores_var_den = []

for variable in range(max_intermedias):
    num = []
    den = []
    cuantas_num = []
    cuantas_den = []

    for anterior in range(variable):
        # Si se utiliza para crear "variable" y el grado de su numerador es n, entonces aporta grado 1 al numerador. Idem con el denominador.
        num.append(If(And(variables_anteriores[variable][anterior], num_variables_num[anterior] == maxDeg), 1, 0))
        den.append(If(And(variables_anteriores[variable][anterior], num_variables_den[anterior] == maxDeg), 1, 0))

        cuantas_num.append(If(And(variables_anteriores[variable][anterior], num_variables_num[anterior] == maxDeg), cuantas_variables_num[anterior], 0))
        cuantas_den.append(If(And(variables_anteriores[variable][anterior], num_variables_den[anterior] == maxDeg), cuantas_variables_den[anterior], 0))
        
        # Como no hay repetidos, cada VI solo puede utilizarse en una VI
        for siguientes in range(variable + 1, max_intermedias):
            solver.add(Implies(variables_anteriores[variable][anterior], Not(variables_anteriores[siguientes][anterior])))

    numero_anteriores_var_num.append(addsum(num))
    numero_anteriores_var_den.append(addsum(den))

    # La nueva variable tiene todas las variables iniciales que contenga + las variables que contengan otras variables anteriores.
    solver.add(cuantas_variables_num[variable] == addsum(cuantas_num) + num_variables_num[variable])
    solver.add(cuantas_variables_den[variable] == addsum(cuantas_den) + num_variables_den[variable])

grado_num_var = []
grado_den_var = []

# Válido porque solo se añaden las variables que se utilizan en numerador/denominador y que tienen grado n, en numerador/denominador, según corresponda
# REVISAR, no sé si habría que contarlo siempre que se utilice, independientemente de si el numerador o el denominador tiene grado n, si se usa, aporta 1
for variable in range(max_intermedias):
    grado_num_var.append(num_variables_num[variable] + numero_anteriores_var_num[variable])
    grado_den_var.append(num_variables_den[variable] + numero_anteriores_var_den[variable])

# Dominio de las variables REVISAR
for variable in range(max_intermedias):    
    solver.add(Implies(grado_num_var[variable] == maxDeg, grado_den_var[variable] == maxDeg - 1))
    solver.add(Implies(grado_den_var[variable] == maxDeg, grado_num_var[variable] == maxDeg - 1))
    solver.add(Or(And(grado_num_var[variable] == maxDeg, grado_den_var[variable] == maxDeg - 1), And(grado_den_var[variable] == maxDeg, grado_num_var[variable] == maxDeg - 1), And(grado_den_var[variable] == 0, grado_num_var[variable] == 0)))

# El producto final, utiliza la variable nueva iésima o no
producto_final_vars_num = []
producto_final_vars_den = []

for variable in range(max_intermedias):
    producto_final_vars_num.append(Bool("final_var_num_" + str(variable)))
    producto_final_vars_den.append(Bool("final_var_den_" + str(variable)))

    # No pueden ser ambas ciertas a la vez. O se usa en el numerador o se usa en el denominador
    solver.add(Not(And(producto_final_vars_num[variable], producto_final_vars_den[variable])))

# De las variables iniciales, cuántas tiene en bruto el producto final, que no están en ninguna variable intermedia.
producto_final_ini_num = Int("final_num")
producto_final_ini_den = Int("final_den")

solver.add(producto_final_ini_num >= 0)
solver.add(producto_final_ini_den >= 0)
solver.add(producto_final_ini_num <= maxDeg)
solver.add(producto_final_ini_den <= maxDeg)

grado_final_num = []
grado_final_den = []

# Sólo la coges para sustituir donde tenga grado n
for variable in range(max_intermedias):
    grado_final_num.append(If(And(grado_num_var[variable] == maxDeg, producto_final_vars_num[variable]), 1, 0))
    grado_final_den.append(If(And(grado_den_var[variable] == maxDeg, producto_final_vars_den[variable]), 1, 0))

# Los grados obtenidos eligiendo todas las variables + el número de variables inicales debe ser menor que el grado máximo
solver.add(addsum(grado_final_num) + producto_final_ini_num <= maxDeg)
solver.add(addsum(grado_final_den) + producto_final_ini_den <= maxDeg)

# Cubre variables
cubre_num = []
cubre_den = []

for variable in range(max_intermedias):
    # REVISAR si la variable se coge para numerador o denominador
    cubre_num.append(If(producto_final_vars_num[variable], cuantas_variables_num[variable], 0))
    cubre_num.append(If(producto_final_vars_den[variable], cuantas_variables_num[variable], 0))
    cubre_den.append(If(producto_final_vars_num[variable], cuantas_variables_den[variable], 0))
    cubre_den.append(If(producto_final_vars_den[variable], cuantas_variables_den[variable], 0))

# No sobra porque la restricción que hay arriba de que las variables intermedias + las iniciales deben ser <= maxDeg, con esto garantizas que la suma se == maxDeg
solver.add(addsum(cubre_num) + producto_final_ini_num == degree_num)
solver.add(addsum(cubre_den) + producto_final_ini_den == degree_den)

# Minimizar el número de variables
for variable in range(max_intermedias):
    solver.add_soft(And(cuantas_variables_num[variable] == 0, cuantas_variables_den[variable] == 0), 1, "min_vars")

if solver.check() == sat:
    m = solver.model()
    print("Variables intermedias formadas:")
    for variable in range(max_intermedias):
        num = m.eval(num_variables_num[variable], model_completion=True).as_long()
        den = m.eval(num_variables_den[variable], model_completion=True).as_long()
        cubre_num = m.eval(cuantas_variables_num[variable], model_completion=True).as_long()
        cubre_den = m.eval(cuantas_variables_den[variable], model_completion=True).as_long()
        deps = []
        for anterior in range(variable):
            val = m.eval(variables_anteriores[variable][anterior], model_completion=True)
            if is_true(val):
                deps.append(f"VI_{anterior}")
        dep_str = f", depende de: {', '.join(deps)}" if deps else ""
        print(f"VI_{variable}: Numerador = {num}, Denominador = {den}, cubre {cubre_num} originales en num y {cubre_den} en den{dep_str}")

    usadas_num = []
    for variable in range(max_intermedias):
        val = m.eval(producto_final_vars_num[variable], model_completion=True)
        if is_true(val):
            num = m.eval(num_variables_num[variable], model_completion=True).as_long()
            usadas_num.append(f"VI_{variable}")

    usadas_den = []
    for variable in range(max_intermedias):
        val = m.eval(producto_final_vars_den[variable], model_completion=True)
        if is_true(val):
            den = m.eval(num_variables_den[variable], model_completion=True).as_long()
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