#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Conectar sumas con productos -> primero solucionar las que se pasan de grado y luego las sumas
# Pasar a js conectado
# Simetrías de variables
# Otra opción: quién me usa: booleana de si es usada por intermedia o final o no, y quien la usa. Si una tiene a falso los 2, las siguientes tmb
# Primero intermedias usadas por otras intermedias y luego las usadas por el final
# Las variables llenas al principio y medio llenas después
# Garantizar que no se pierden soluciones, cualquier cosa que quita repetidos, no elimina soluciones, solo evita que la misma solucion tenga varias representaciones
# Ir apuntando todo

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
max_intermedias = 10
# Usaremos variables intermedias vi_0, ... vi_{max_intermedias-1}

# Cada variable, cuántas variables de las originales tiene del numerador, y cuántas del denominador. Cada variables es un nivel.
# Las variables del numerador se colocarán en el numerador de la nueva variable y las del denominador en el denominador pero para el recuento final, es necesario saber cuántas eran originalmente del numerador
num_variables_originales_var_num = []
num_variables_originales_var_den = []

#num_var_i : número de variables originales de numerador que va a agrupar vi_i
#den_var_i : número de variables originales de denominador que va a agrupar vi_i
for var in range(max_intermedias):
    num_variables_originales_var_num.append(Int("num_var_" + str(var)))
    num_variables_originales_var_den.append(Int("den_var_" + str(var)))

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


# El producto final, qué variables intermedias utiliza
producto_usa_var_en_num = []
producto_usa_var_en_den = []

for var in range(max_intermedias):
    producto_usa_var_en_num.append(Bool("prodn_var_" + str(var)))
    producto_usa_var_en_den.append(Bool("prodd_var_" + str(var)))

# No puede usarse la misma variable para numerador y denominador
for var in range(max_intermedias):
    solver.add(Or(Not(producto_usa_var_en_num[var]), Not(producto_usa_var_en_den[var])))

# De las variables iniciales, cuáles hay en el producto final directamente
producto_usa_iniciales_en_num = Int("inic_prod_num")
solver.add(And(producto_usa_iniciales_en_num >= 0, producto_usa_iniciales_en_num <= maxDeg))

producto_usa_iniciales_en_den = Int("inic_prod_den")
solver.add(And(producto_usa_iniciales_en_den >= 0, producto_usa_iniciales_en_den <= maxDeg))

# Rango de las variables
for var in range(max_intermedias):
    solver.add(And(num_variables_originales_var_num[var] >= 0, num_variables_originales_var_num[var] <= maxDeg))
    solver.add(And(num_variables_originales_var_den[var] >= 0, num_variables_originales_var_den[var] <= maxDeg))


# Para cada variable, cuántas variables originales realmente cubre teniendo en cuenta las originales que tiene de num_variables_originales_var + las que tiene cada variable anterior que contiene
# Es decir, de las originales del numerador, cuántas contiene? Idem con denominador
cuantas_variables_cubre_num = []
cuantas_variables_cubre_den = []

for var in range(max_intermedias):
    cuantas_n = []
    cuantas_d = []
    cuantas_n.append(num_variables_originales_var_num[var])
    cuantas_d.append(num_variables_originales_var_den[var])

    # Si utiliza una variable anterior ahora cubre todas las que tuviera ella también + las suyas
    for anterior in range(var):
        cuantas_n.append(If(Or(usa_var_anterior_num[var][anterior], usa_var_anterior_den[var][anterior]), cuantas_variables_cubre_num[anterior], 0))
        cuantas_d.append(If(Or(usa_var_anterior_num[var][anterior], usa_var_anterior_den[var][anterior]), cuantas_variables_cubre_den[anterior], 0))
        # cuantas_n.append(If(usa_var_anterior_num[var][anterior], cuantas_variables_cubre_num[anterior] + cuantas_variables_cubre_den[anterior], 0))
        # cuantas_d.append(If(usa_var_anterior_den[var][anterior], cuantas_variables_cubre_num[anterior] + cuantas_variables_cubre_den[anterior], 0))

    cuantas_variables_cubre_num.append(addsum(cuantas_n))
    cuantas_variables_cubre_den.append(addsum(cuantas_d))

# Grado de cada variable: el máximo entre el grado del numerador y del denominador
grado_num_variables = []
grado_den_variables = []

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
    
    grado_num_variables.append(addsum(grado_num))
    grado_den_variables.append(addsum(grado_den))

# Solo puede ocurrir o que el grado de la variable sea n/n-1, n-1/n o que esté vacía tanto en numerador como denominador
for var in range(max_intermedias):
    n_num = And(grado_num_variables[var] == maxDeg, grado_den_variables[var] == maxDeg - 1)
    n_den = And(grado_num_variables[var] == maxDeg - 1, grado_den_variables[var] == maxDeg)
    zero = And(grado_num_variables[var] == 0, grado_den_variables[var] == 0)

    solver.add(Or(n_num, Or(n_den, zero)))

# Si la variable es de la forma n/(n - 1) se utilizará en el numerador, aportando grado 1 y si tiene la forma (n - 1)/n se utilizará en el denominador
for var in range(max_intermedias):

    for anterior in range(var):
        # Si tiene n en el numerador, no puede usarse en el denominador de ninguna variable y viceversa
        solver.add(Implies(grado_num_variables[anterior] == maxDeg, Not(usa_var_anterior_den[var][anterior])))
        solver.add(Implies(grado_den_variables[anterior] == maxDeg, Not(usa_var_anterior_num[var][anterior])))
        solver.add(Implies(grado_num_variables[anterior] == 0, Not(Or(usa_var_anterior_num[var][anterior], usa_var_anterior_den[var][anterior]))))

# Contar que se cubren todas las variables que había al inicio
vars_inic_num = []
vars_inic_den = []

# Si utiliza una variable, ya sea en numerador o denominador, ahora cubre las variables que ella cubriera
for var in range(max_intermedias):
    vars_inic_num.append(If(Or(producto_usa_var_en_num[var], producto_usa_var_en_den[var]), cuantas_variables_cubre_num[var], 0))
    vars_inic_den.append(If(Or(producto_usa_var_en_num[var], producto_usa_var_en_den[var]), cuantas_variables_cubre_den[var], 0))

solver.add(And(addsum(vars_inic_num) + producto_usa_iniciales_en_num == degree_num, addsum(vars_inic_den) + producto_usa_iniciales_en_den == degree_den))

# Si la variable es de la forma n/(n - 1) se utilizará en el numerador, aportando grado 1 y si tiene la forma (n - 1)/n se utilizará en el denominador
for var in range(max_intermedias):

    # Si tiene n en el numerador, no puede usarse en el denominador de ninguna variable y viceversa
    solver.add(Implies(grado_num_variables[var] == maxDeg, Not(producto_usa_var_en_den[var])))
    solver.add(Implies(grado_den_variables[var] == maxDeg, Not(producto_usa_var_en_num[var])))
    solver.add(Implies(grado_num_variables[var] == 0, Not(Or(producto_usa_var_en_num[var], producto_usa_var_en_den[var]))))

# Comprobar que no te pasas de grado en el producto final
grado_prod_n = []
grado_prod_d = []

for var in range(max_intermedias):
    grado_prod_n.append(If(producto_usa_var_en_num[var], 1, 0))
    grado_prod_d.append(If(producto_usa_var_en_den[var], 1, 0))

solver.add(And(addsum(grado_prod_n) + producto_usa_iniciales_en_num <= maxDeg, addsum(grado_prod_d) + producto_usa_iniciales_en_den <= maxDeg))

# Una misma variable no puede usarse en 2 variables intermedias, o en variable y producto. La suma de veces que es utilizada es <= 1.
for var in range(max_intermedias):
    usos = []

    for siguiente in range(var + 1, max_intermedias):
        usos.append(If(Or(usa_var_anterior_num[siguiente][var], usa_var_anterior_den[siguiente][var]), 1, 0))

    usos.append(If(Or(producto_usa_var_en_num[var], producto_usa_var_en_den[var]), 1, 0))

    solver.add(addsum(usos) <= 1)

# Orden en variables:

# Primero aparezcan las variables de la forma n/n-1, luego las de n-1/n y luego las vacías
for var in range(max_intermedias - 1):
    solver.add(grado_num_variables[var] >= grado_num_variables[var + 1])

# Primero las variables que utilicen otras variables anteriores y luego las que no
# Si una varibale utiliza una variable anterior, implica que o la siguiente tiene grado distinto en numerador, según el orden establecido antes
# o bien, si tiene el mismo grado en numerador, esa variable también utiliza una variable anterior porque primero se tienen que crear las variables simples y luego las compuestas
# Otra forma, mirarlo con si el grado es != del número de variables originales que utiliza implica que está utilizando una variable anterior
for var in range(max_intermedias - 1):
    depende_de_alguna_var = []
    siguiente_var_depende = []

    for anterior_a_var in range(var):
        depende_de_alguna_var.append(If(Or(usa_var_anterior_num[var][anterior_a_var], usa_var_anterior_den[var][anterior_a_var]), 1, 0))

    for anterior_a_sig in range(var + 1):
        siguiente_var_depende.append(If(Or(usa_var_anterior_num[var + 1][anterior_a_sig], usa_var_anterior_den[var + 1][anterior_a_sig]), 1, 0))
    
    solver.add(Implies(addsum(depende_de_alguna_var) > 0, Or(grado_num_variables[var] != grado_num_variables[var + 1], addsum(siguiente_var_depende) > 0)))

# Dentro de las variables que utilizan otras anteriores, deben aparecer primero aquellas que tengan un número de variables iniciales mayor
for var in range(max_intermedias - 1):
    solver.add(num_variables_originales_var_num[var] >= num_variables_originales_var_num[var + 1])
    solver.add(Implies(num_variables_originales_var_num[var] == num_variables_originales_var_num[var + 1], num_variables_originales_var_den[var] >= num_variables_originales_var_den[var + 1]))

# Minimizar el número de variables
# for var in range(max_intermedias):
#     solver.add_soft(And(grado_num_variables[var] == 0, grado_den_variables[var] == 0), 1, "min_vars")

print(f"Grado numerador: {degree_num}. Grado denominador: {degree_den}")
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
        usa_num = m.eval(producto_usa_var_en_num[var], model_completion=True)
        usa_den = m.eval(producto_usa_var_en_den[var], model_completion=True)

        inic_num = m.eval(producto_usa_iniciales_en_num, model_completion=True).as_long()
        inic_den = m.eval(producto_usa_iniciales_en_den, model_completion=True).as_long()

        if usa_num:
            usadas_num.append(f"VI_{var}")
        elif usa_den:
            usadas_den.append(f"VI_{var}")

    # Mostrar producto final estimado
    producto_str = " * ".join(usadas_num) if usadas_num else "1"
    producto_str_den = " * ".join(usadas_den) if usadas_den else "1"

    print(f"\nProducto final: ({producto_str}) / ({producto_str_den}). Usa {inic_num} iniciales en numerador y {inic_den} iniciales en denominador")

else:
    print("No hay solución.")
