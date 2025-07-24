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

expresiones_iguales = []
cjto_variables = set()

for exp in range(num_expresiones):
    expresiones_iguales.append([])
    iguales_exp = []

    cjto_variables.add(expresiones[exp]["values"][0]["signals"][0])
    cjto_variables.add(expresiones[exp]["values"][1]["signals"][0])

    for e in range(num_expresiones):
        if exp < e and expresiones[exp]["values"][0]["signals"] == expresiones[e]["values"][0]["signals"]:
            if expresiones[exp]["values"][0]["degree"] == expresiones[e]["values"][0]["degree"]:
                if expresiones[exp]["values"][1]["signals"] == expresiones[e]["values"][1]["signals"] :
                    if expresiones[exp]["values"][1]["degree"] == expresiones[e]["values"][1]["degree"]:
                        igual = 0
                        for anteriores in range(0, exp):
                            if e in expresiones_iguales[anteriores]: igual += 1
                        
                        if igual == 0: iguales_exp.append(e)
    
    expresiones_iguales[exp] = iguales_exp

cjto_variables = sorted(list(cjto_variables))

variables_expresion = []
for exp in range(num_expresiones):
    vars = []

    for var in cjto_variables:
        num = 0
        if expresiones[exp]["values"][0]["signals"][0] == var: num += 1
        if expresiones[exp]["values"][1]["signals"][0] == var: num += 1

        vars.append(num)

    variables_expresion.append(vars)

variables_total = []
for var in cjto_variables:
    c = 0
    for exp in range(num_expresiones):
        if expresiones[exp]["values"][0]["signals"][0] == var: c += 1
        if expresiones[exp]["values"][1]["signals"][0] == var: c += 1

    variables_total.append(c)

solver = Optimize()

# Para cada expresión, me la quedo tal cual o la expando. Si me la quedo significa que va a ser un "VI" final
expando = []

for exp in range(num_expresiones):
    expando.append(Bool("exp_" + str(exp)))

    # Minimiza el número de variables "originales"
    solver.add_soft(expando[exp], 1, "keeps")
    
# Para cada expresión que ha sido expandida, booleano que indica si se junta o no con la expresión i-ésima
juntar = []

for exp in range(num_expresiones):
    juntar_exp = []
    for e in range(num_expresiones):
        juntar_exp.append(Bool("juntar_" + str(exp) + "_" + str(e)))
    
    juntar.append(juntar_exp)

for exp in range(num_expresiones):
    for e in range(num_expresiones):
        if exp == e:  # No juntar una expresión consigo misma
            solver.add(Not(juntar[exp][e]))
            solver.add(Not(juntar[e][exp]))

        elif exp > e:
            solver.add(Not(juntar[exp][e]))
        else:
            # Si se cumple esto, se pueden unir. Sino, obligatoriamente el booleano debe ir a false
            solver.add(Implies(Not(And(expando[exp], expando[e])), Not(juntar[exp][e])))
            # solver.add(Implies(Not(And(expando[exp], expando[e])), Not(juntar[e][exp])))
            # solver.add(Implies(juntar[exp][e], Not(juntar[e][exp]))) # Porque sabes que estás en el caso exp < e

            # Para que las relaciones entén en la primera fracción que forma la unión de fracciones y no contar el grado 2 veces
            for anterior in range(0, e):
                solver.add(Implies(And(juntar[exp][e], juntar[exp][anterior]), Not(juntar[anterior][e])))
                # La implicación de no juntar anterior con exp se cumple trivial porque e > anterior, entrará en el elif

# Comprobar que las expresiones que se forman no superan el grado
for exp in range(num_expresiones):
    grado_num = [If(expando[exp], expresiones[exp]["values"][0]["degree"], 0)]
    grado_den = [If(expando[exp], expresiones[exp]["values"][1]["degree"], 0)]

    for e in range(num_expresiones):

        # Trabajo con el último elemento del array que tiene el grado acumulado
        prev_grado_num = grado_num[-1]
        prev_grado_den = grado_den[-1]

        # max(numerador actual * denominador de e, numerador de e * denominador actual)
        expr1 = prev_grado_num + expresiones[e]["values"][1]["degree"]
        expr2 = prev_grado_den + expresiones[e]["values"][0]["degree"]

        nuevo_grado_num = If(juntar[exp][e], If(expr1 > expr2, expr1, expr2), prev_grado_num)
        nuevo_grado_den = If(juntar[exp][e], prev_grado_den + expresiones[e]["values"][1]["degree"], prev_grado_den)

        grado_num.append(nuevo_grado_num)
        grado_den.append(nuevo_grado_den)

    final_num = grado_num[-1]
    final_den = grado_den[-1]
    grado_total = If(expando[exp], If(final_num > final_den, final_num, final_den), 0)

    solver.add(grado_total <= maxDeg)
        
# La expresión final no supera el grado máximo
grado_final = []
for exp in range(num_expresiones):
    depende = []
    for e in range(num_expresiones):
        depende.append(If(juntar[exp][e], 1, 0)) # Para no contar más de una vez las fracciones que forman una nueva VI tras expandirse

    if exp == 0:
        grado_act = 1 
    else:
        grado_act = grado_final[-1]

    mayor = If(grado_act > 1, grado_act, 1)
    grado_final.append(If(Or(Not(expando[exp]), addsum(depende) > 0), mayor, grado_act))
    # grado_final.append(If(And(expando[exp], addsum(depende) == 0), 0, 0))
    # grado_final.append(If(Not(expando[exp]), 1, 0)) # If(exp1 > exp2, exp1, exp2), 0))

solver.add(grado_final[-1] <= maxDeg)

# Numero de señales que contiene cada variable nueva
cuantas_variables = []
for exp in range(num_expresiones):
    c = []
    for var in range(len(cjto_variables)):
        c.append(Int("cuantas_" + str(exp) + "_" + str(var)))
        solver.add(c[var] >= 0)
        solver.add(c[var] <= variables_total[var])
    
    cuantas_variables.append(c)

for exp in range(num_expresiones):
    for var in range(len(cjto_variables)):
        cuantas = []
        cuantas.append(variables_expresion[e][var])
        for e in range(num_expresiones):
            cuantas.append(If(juntar[exp][e], variables_expresion[e][var], 0))
        
        solver.add(cuantas_variables[exp][var] == addsum(cuantas))

cuentan = []
for exp in range(num_expresiones):
    cuentan.append(Bool("cuenta_" + str(exp)))

# Si se expande una expresión, obligatoriamente se tiene que unificar con otra. Variables que realmente cuentan
fila_exp = []
for exp in range(num_expresiones):
    suma_fila = []
    suma_col = []
    for e in range(num_expresiones):
        suma_fila.append(If(juntar[exp][e], 1, 0))
        suma_col.append(If(juntar[e][exp], 1, 0))
    
    fila_exp.append(suma_fila)

    # num_var_iguales = []
    for e in range(exp + 1, num_expresiones): # Para todas las siguientes     
        cuantas_iguales = []

        # Las señales de las que está formada son iguales
        for var in range(len(cjto_variables)):
            cuantas_iguales.append(If(cuantas_variables[exp][var] == cuantas_variables[e][var], 1, 0))
        
        # Coinciden en todas las variables
        # num_var_iguales.append(If(addsum(cuantas_iguales) == len(cjto_variables), 1, 0))
        solver.add(Implies(addsum(cuantas_iguales) == len(cjto_variables), Or(Not(cuentan[exp]), Not(cuentan[e]))))

    # Solo cuenta si está formando una nueva variable y no existe otra variable exactamente igual
    # solver.add(cuentan[exp] == And(addsum(suma_fila) > 0, addsum(num_var_iguales) == 0))            

    solver.add(Implies(expando[exp], Or(addsum(suma_fila) > 0, addsum(suma_col) > 0)))
    
    # Cada fracción unicamente está unificada 1 vez
    solver.add(Implies(addsum(suma_fila) > 0, addsum(suma_col) == 0))
    solver.add(Implies(addsum(suma_col) > 0, addsum(suma_fila) == 0))
    solver.add(addsum(suma_col) <= 1)

    # Minimizar número de variables creadas
    solver.add_soft(Not(cuentan[exp]), 1, "cuentan")

# Se cubren todas las variables que había al principio
for var in range(len(cjto_variables)):
    c = []
    for exp in range(num_expresiones):
        c.append(If(expando[exp], cuantas_variables[exp][var], variables_expresion[exp][var]))
        # c.append(cuantas_variables[exp][var])
    
    solver.add(addsum(c) == variables_total[var])

if solver.check() == sat:
    modelo = solver.model()
    print("Solución encontrada:\n")

    expanden = [i for i in range(num_expresiones) if modelo.evaluate(expando[i]) == True]
    no_expand = [i for i in range(num_expresiones) if modelo.evaluate(expando[i]) == False]
    cuentan_final = [i for i in range(num_expresiones) if modelo.evaluate(cuentan[i]) == True]

    def fraccion_a_texto(exp):
        num_signals = expresiones[exp]["values"][0]["signals"]
        den_signals = expresiones[exp]["values"][1]["signals"]
        return f"({'+'.join(map(str, num_signals))}) / ({'+'.join(map(str, den_signals))})"

    def clave_combinacion(grupo):
        claves = []
        for idx in sorted(grupo):
            num = tuple(sorted(expresiones[idx]["values"][0]["signals"]))
            den = tuple(sorted(expresiones[idx]["values"][1]["signals"]))
            grado_num = expresiones[idx]["values"][0]["degree"]
            grado_den = expresiones[idx]["values"][1]["degree"]
            claves.append((num, grado_num, den, grado_den))
        return tuple(sorted(claves))

    estructuras_vistas = set()
    unificaciones = []

    for i in cuentan_final:
        grupo = [i]
        for j in range(num_expresiones):
            if i != j and modelo.evaluate(juntar[i][j]) == True:
                grupo.append(j)

        clave = clave_combinacion(grupo)
        if clave not in estructuras_vistas:
            estructuras_vistas.add(clave)
            unificaciones.append(sorted(grupo))

    if unificaciones:
        print("Fracciones unificadas en nuevas variables intermedias (solo las que cuentan):")
        for idx, grupo in enumerate(unificaciones):
            print(f"  - VI {idx+1}: combinación de expresiones {grupo}")
            for g in grupo:
                print(f"      · {fraccion_a_texto(g)}")
    else:
        print("No se han generado fracciones nuevas únicas (VI).")

    if no_expand:
        print("\nFracciones originales que no se han expandido y se conservan:")
        for i in no_expand:
            print(f"  - Expresión {i}: {fraccion_a_texto(i)}")
else:
    print("No se encontró una solución válida bajo las restricciones dadas.")
