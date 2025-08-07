#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from z3 import *
import argparse
import time

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

productos = data["productos"]
maxDeg = data["degree"]
num_productos = len(productos)

factores_num = []
factores_den = []

grados_prod = [] # Cada producto de fracciones qué grado tiene

cjto_variables = set()

solver = Optimize()

for p in range(num_productos):
    exp = productos[p]["expressions"]
    grado_num = 0
    grado_den = 0

    for e in exp:

        cjto_variables.add(e["values"][0]["signals"])
        cjto_variables.add(e["values"][1]["signals"])
        
        grado_num += e["values"][0]["degree"]
        grado_den += e["values"][1]["degree"]

        if grado_num > maxDeg:
            factores_num.append(e["values"][0]["signals"])

        if grado_den > maxDeg:
            factores_den.append(e["values"][1]["signals"])

    grados_prod.append(max(grado_num, grado_den))

num_factores_num = len(factores_num)
num_factores_den = len(factores_den)

# Para cada producto, cuántas variables de cada contiene
num_variables_por_producto = []

for prod in productos:
    counts = []
    for var in cjto_variables:
        c_num = 0
        c_den = 0
        for exp in prod["expressions"]:
            if exp["values"][0]["signals"] == var: c_num += exp["values"][0]["degree"]
            if exp["values"][1]["signals"] == var: c_den += exp["values"][1]["degree"]
        
        counts.append(c_num + c_den)

    num_variables_por_producto.append(counts)

print(num_variables_por_producto)
print(list(cjto_variables))

num_variables_por_factor_num = []
num_variables_por_factor_den = []

solver = Optimize()

##### PARAMETROS #####
max_intermedias = 10

inicio = time.time()

# Declaración de los huecos de los que disponen las VI para formarse
def composicion_variables_intermedias(ocupacion_huecos_variables_v_num, ocupacion_huecos_variables_f_num, ocupacion_huecos_variables_den):

    for variable in range(max_intermedias):
        huecos_var_v_num = []
        huecos_var_f_num = []
        huecos_var_den = [] # En el denominador solo puede haber factores

        for hueco_num in range(maxDeg):
            ocupa_v_num = []
            ocupa_f_num = []
            
            for variable_anterior in range(0, variable):
                ocupa_v_num.append(Bool("ocupavn_" + str(variable) + "_" + str(hueco_num) + "_" + str(variable_anterior)))

            for factor in range(num_factores_num):
                ocupa_f_num.append(Bool("ocupafn_" + str(variable) + "_" + str(hueco_num) + "_" + str(factor)))

            huecos_var_v_num.append(ocupa_v_num)
            huecos_var_f_num.append(ocupa_f_num)
        
        for hueco_den in range(maxDeg):
            ocupa_f_d = []  
            for factor in range(num_factores_den):
                ocupa_f_d.append(Bool("ocupafd_" + str(variable) + "_" + str(hueco_den) + "_" + str(factor)))

            huecos_var_den.append(ocupa_f_d)
    
        ocupacion_huecos_variables_v_num.append(huecos_var_v_num)
        ocupacion_huecos_variables_f_num.append(huecos_var_f_num)
        ocupacion_huecos_variables_den.append(huecos_var_den)

# Para todo hueco, los siguientes deben tener índice mayor. Todos los índices anteriores no deben estar activados. Primero aparecen otras VI y luego los factores
def orden_huecos_variables(ocupacion_huecos_variables_v_num, ocupacion_huecos_variables_f_num, ocupacion_huecos_variables_den):
    for variable in range(max_intermedias):
        for hueco_num in range(maxDeg):
            for variable_anterior in range(0, variable):
                for hueco_sig in range(hueco_num + 1, maxDeg):
                    for vars_anteriores in range(0, variable_anterior):
                        solver.add(Implies(ocupacion_huecos_variables_v_num[variable][hueco_num][variable_anterior], Not(ocupacion_huecos_variables_v_num[variable][hueco_sig][vars_anteriores])))

            for factor in range(num_factores_num):
                for hueco_sig in range(hueco_num + 1, maxDeg):
                    for var_anterior in range(0, variable):
                        solver.add(Implies(ocupacion_huecos_variables_f_num[variable][hueco_num][factor], Not(ocupacion_huecos_variables_v_num[variable][hueco_sig][var_anterior])))

                    for factores_anteriores in range(0, factor):
                        solver.add(Implies(ocupacion_huecos_variables_f_num[variable][hueco_num][factor], Not(ocupacion_huecos_variables_f_num[variable][hueco_sig][factores_anteriores])))

        for hueco_den in range(maxDeg):
            for factor in range(num_factores_den):
                for factores_anteriores in range(0, factor):
                        solver.add(Implies(ocupacion_huecos_variables_den[variable][hueco_den][factor], Not(ocupacion_huecos_variables_den[variable][hueco_sig][factores_anteriores])))


# Se obliga a rellenar los huecos de arriba a abajo, si un hueco está vacío, todos los siguientes también
def rellenar_huecos_variables_en_orden(ocupacion_huecos_variables_v_num, ocupacion_huecos_variables_f_num, ocupacion_huecos_variables_den, variable):

    for hueco_num in range(1, maxDeg):
        suma_actual = []
        suma_anterior = []
        for var in ocupacion_huecos_variables_v_num[variable][hueco_num]:
            suma_actual.append(If(var, 1, 0))

        for fact in ocupacion_huecos_variables_f_num[variable][hueco_num]:
            suma_actual.append(If(fact, 1, 0))

        for var in ocupacion_huecos_variables_v_num[variable][hueco_num - 1]:
            suma_anterior.append(If(var, 1, 0))

        for fact in ocupacion_huecos_variables_f_num[variable][hueco_num - 1]:
            suma_anterior.append(If(fact, 1, 0))

        solver.add(Implies(addsum(suma_actual) > 0, addsum(suma_anterior) > 0))

    for hueco_den in range(1, maxDeg):
        suma_actual = []
        suma_anterior = []

        for fact in ocupacion_huecos_variables_den[variable][hueco_den]:
            suma_actual.append(If(fact, 1, 0))

        for fact in ocupacion_huecos_variables_den[variable][hueco_den - 1]:
            suma_anterior.append(If(fact, 1, 0))

        solver.add(Implies(addsum(suma_actual) > 0, addsum(suma_anterior) > 0))

# Restricciones de ocupación de los huecos de las VI
def restricciones_huecos_v(ocupacion_huecos_variables_v_num, ocupacion_huecos_variables_f_num, ocupacion_huecos_variables_den):

    for variable in range(max_intermedias):
        cumple_grado_num = []
        cumple_grado_den = []
        huecos_ocupados = []

        for hueco_num in range(maxDeg):
            variables_activas_por_hueco = []
            for variable_anterior in range(0, variable):
                cumple_grado_num.append(If(ocupacion_huecos_variables_v_num[variable][hueco_num][variable_anterior], 1, 0))

                variables_activas_por_hueco.append(If(ocupacion_huecos_variables_v_num[variable][hueco_num][variable_anterior], 1, 0))

            for factor in range(num_factores_num):
                cumple_grado_num.append(If(ocupacion_huecos_variables_f_num[variable][hueco_num][factor], 1, 0))

                variables_activas_por_hueco.append(If(ocupacion_huecos_variables_f_num[variable][hueco_num][factor], 1, 0))

            # Puede dejarse vacío o ocuparse por 1 único elemento, ya sea VI o factor
            solver.add(addsum(variables_activas_por_hueco) <= 1)
            huecos_ocupados.append(addsum(variables_activas_por_hueco))

        for hueco_den in range(maxDeg):
            variables_activas_por_hueco = []

            for factor in range(num_factores_den):
                cumple_grado_den.append(If(ocupacion_huecos_variables_den[variable][hueco_den][factor], 1, 0))

                variables_activas_por_hueco.append(If(ocupacion_huecos_variables_den[variable][hueco_den][factor], 1, 0))

            # Puede dejarse vacío o ocuparse por 1 único elemento, ya sea VI o factor
            solver.add(addsum(variables_activas_por_hueco) <= 1)
            huecos_ocupados.append(addsum(variables_activas_por_hueco))

        rellenar_huecos_variables_en_orden(ocupacion_huecos_variables_v_num, ocupacion_huecos_variables_f_num, ocupacion_huecos_variables_den, variable)
        
        # La suma del grado de todo lo que se utiliza para formar la variable debe ser menor o igual que el grado máximo
        solver.add(addsum(cumple_grado_num) <= maxDeg)
        solver.add(addsum(cumple_grado_den) <= maxDeg)

        # Eliminar variables que están formadas por una única variable intermedia/factor
        solver.add(And(addsum(huecos_ocupados) != 1, addsum(huecos_ocupados) <= maxDeg)) # , addsum(variables_activas_por_var) > 1))

# Las variables se rellenan en el array de izq a derecha, a la derecha pueden quedar variables sin usar
# def variables_en_orden()

# Cuántas variables originales cubre esta VI con los elementos que ocupan sus huecos
def cubre_variables_v(ocupacion_huecos_variables_v_num, ocupacion_huecos_variables_f_num, ocupacion_huecos_variables_den, cuantas_variables):

    for elem in range(max_intermedias):
        variables_elem = []
        for variable_original in range(len(cjto_variables)):
            variables_elem.append(Int("var_" + str(elem) + "_" + str(variable_original)))
            
        cuantas_variables.append(variables_elem)

    for elem in range(max_intermedias):
        var_orig = 0
        for variable_original in cjto_variables:
            conteo_var = []
            for hueco_num in range(maxDeg):
                for var in range(0, elem):
                    conteo_var.append(If(ocupacion_huecos_variables_v_num[elem][hueco_num][var], cuantas_variables[var][var_orig], 0))

                for fact in range(num_factores_num):
                    if variable_original == factores_num[fact]:
                        conteo_var.append(If(ocupacion_huecos_variables_f_num[elem][hueco_num][fact], 1, 0))
                        
            for hueco_den in range(maxDeg):
                for fact in range(num_factores_den):
                    if variable_original == factores_den[fact]:
                        conteo_var.append(If(ocupacion_huecos_variables_den[elem][hueco_den][fact], 1, 0))

            solver.add(cuantas_variables[elem][var_orig] == addsum(conteo_var))
            var_orig += 1

# Declaración de los huecos de los que disponen los productos para formarse
def composicion_productos(ocupacion_huecos_prod_v_num, ocupacion_huecos_prod_f_num, ocupacion_huecos_prod_den):
    for prod in range(num_productos):
        huecos_prod_v_num = []
        huecos_prod_f_num = []
        huecos_prod_den = []

        for hueco_num in range(maxDeg):
            ocupa_v = []
            ocupa_f = []

            for variable in range(max_intermedias):                
                ocupa_v.append(Bool("ocupapvn_" + str(prod) + "_" + str(hueco_num) + "_" + str(variable))) 
                if grados_prod[prod] <= maxDeg: solver.add(Not(ocupa_v[variable]))

            for factor in range(num_factores_num):
                ocupa_f.append(Bool("ocupapfn_" + str(prod) + "_" + str(hueco_num) + "_" + str(factor)))
                if grados_prod[prod] <= maxDeg: solver.add(Not(ocupa_f[factor]))

            huecos_prod_v_num.append(ocupa_v)
            huecos_prod_f_num.append(ocupa_f)
        
        for hueco_den in range(maxDeg):
            ocupa_f = []

            for factor in range(num_factores_den):
                ocupa_f.append(Bool("ocupapfd_" + str(prod) + "_" + str(hueco_den) + "_" + str(factor)))
                if grados_prod[prod] <= maxDeg: solver.add(Not(ocupa_f[factor]))

            huecos_prod_den.append(ocupa_f)
        
        ocupacion_huecos_prod_v_num.append(huecos_prod_v_num)
        ocupacion_huecos_prod_f_num.append(huecos_prod_f_num)
        ocupacion_huecos_prod_den.append(huecos_prod_den)

# Para todo hueco, los siguientes deben tener índice mayor. Todos los índices anteriores no deben estar activados
def orden_huecos_productos(ocupacion_huecos_prod_v_num, ocupacion_huecos_prod_f_num, ocupacion_huecos_prod_den):
    for prod in range(num_productos):
        for hueco_num in range(maxDeg):
            if grados_prod[prod] > maxDeg: # Sino no habría que hacer nada
                for var in range(max_intermedias): 
                    for hueco_sig in range(hueco_num + 1, maxDeg):
                        for var_anterior in range(0, var):
                            solver.add(Implies(ocupacion_huecos_prod_v_num[prod][hueco_num][var], Not(ocupacion_huecos_prod_v_num[prod][hueco_sig][var_anterior])))

                for factor in range(num_factores_num):
                    for hueco_sig in range(hueco_num + 1, maxDeg):
                        for var_anterior in range(max_intermedias):
                            solver.add(Implies(ocupacion_huecos_prod_f_num[prod][hueco_num][factor], Not(ocupacion_huecos_prod_v_num[prod][hueco_sig][var_anterior])))
                
                        for factores_anteriores in range(0, factor):
                            solver.add(Implies(ocupacion_huecos_prod_f_num[prod][hueco_num][factor], Not(ocupacion_huecos_prod_f_num[prod][hueco_sig][factores_anteriores])))

        for hueco_den in range(maxDeg):
            for factor in range(num_factores_den):
                for hueco_sig in range(hueco_den + 1, maxDeg):
                        for factores_anteriores in range(0, factor):
                            solver.add(Implies(ocupacion_huecos_prod_den[prod][hueco_den][factor], Not(ocupacion_huecos_prod_den[prod][hueco_sig][factores_anteriores])))

def rellenar_huecos_productos_en_orden(ocupacion_huecos_prod_v_num, ocupacion_huecos_prod_f_num, ocupacion_huecos_prod_den, prod):

    if grados_prod[prod] > maxDeg:
        for hueco_num in range(1, maxDeg):
            suma_actual = []
            suma_anterior = []

            for var in ocupacion_huecos_prod_v_num[prod][hueco_num]:
                suma_actual.append(If(var, 1, 0))

            for fact in ocupacion_huecos_prod_f_num[prod][hueco_num]:
                suma_actual.append(If(fact, 1, 0))

            for var in ocupacion_huecos_prod_v_num[prod][hueco_num - 1]:
                suma_anterior.append(If(var, 1, 0))

            for fact in ocupacion_huecos_prod_f_num[prod][hueco_num - 1]:
                suma_anterior.append(If(fact, 1, 0))

            solver.add(Implies(addsum(suma_actual) > 0, addsum(suma_anterior) > 0))

        for hueco_den in range(1, maxDeg):
            suma_actual = []
            suma_anterior = []

            for fact in ocupacion_huecos_prod_den[prod][hueco_den]:
                suma_actual.append(If(fact, 1, 0))

            for fact in ocupacion_huecos_prod_den[prod][hueco_den - 1]:
                suma_anterior.append(If(fact, 1, 0))

            solver.add(Implies(addsum(suma_actual) > 0, addsum(suma_anterior) > 0))

# Restricciones de ocupación de los huecos de los productos
def restricciones_huecos_p(ocupacion_huecos_prod_v_num, ocupacion_huecos_prod_f_num, ocupacion_huecos_prod_den):
    for prod in range(num_productos):
        de_cuantas_depende_num = []
        de_cuantas_depende_den = []

        if grados_prod[prod] > maxDeg:
            for hueco_num in range(maxDeg):
                activos_hueco = []
                for variable in range(max_intermedias):
                    de_cuantas_depende_num.append(If(ocupacion_huecos_prod_v_num[prod][hueco_num][variable], 1, 0))
                    activos_hueco.append(If(ocupacion_huecos_prod_v_num[prod][hueco_num][variable], 1, 0))

                for factor in range(num_factores_num):
                    de_cuantas_depende_num.append(If(ocupacion_huecos_prod_f_num[prod][hueco_num][factor], 1, 0))
                    activos_hueco.append(If(ocupacion_huecos_prod_f_num[prod][hueco_num][factor], 1, 0))
                
                solver.add(addsum(activos_hueco) <= 1)

            for hueco_den in range(maxDeg):
                activos_hueco = []

                for factor in range(num_factores_den):
                    de_cuantas_depende_den.append(If(ocupacion_huecos_prod_den[prod][hueco_den][factor], 1, 0))
                    activos_hueco.append(If(ocupacion_huecos_prod_den[prod][hueco_den][factor], 1, 0))
                
                solver.add(addsum(activos_hueco) <= 1)

            rellenar_huecos_productos_en_orden(ocupacion_huecos_prod_v_num, ocupacion_huecos_prod_f_num, ocupacion_huecos_prod_den, prod)

            solver.add(addsum(de_cuantas_depende_num) + addsum(de_cuantas_depende_den) <= maxDeg) 

# Comprobación de que con los elementos que ocupan los huecos del monomio se cubren todas las variables originales que tenía en un inicio
def cubre_variables_p(ocupacion_huecos_prod_v_num, ocupacion_huecos_prod_f_num, ocupacion_huecos_prod_den, cuantas_variables):
    for prod in range(num_productos):
        if grados_prod[prod] > maxDeg:
            var_orig = 0
            for var in cjto_variables:
                conteo_var = []
                for hueco_num in range(maxDeg):
                    for elem in range(max_intermedias):
                        conteo_var.append(If(ocupacion_huecos_prod_v_num[prod][hueco_num][elem], cuantas_variables[elem][var_orig], 0))

                    for fact in range(num_factores_num):
                        if var == factores_num[fact]:
                            conteo_var.append(If(ocupacion_huecos_prod_f_num[prod][hueco_num][fact], 1, 0))

                for hueco_den in range(maxDeg):
                    for fact in range(num_factores_den):
                        if var == factores_den[fact]:
                            conteo_var.append(If(ocupacion_huecos_prod_den[prod][hueco_den][fact], 1, 0))

                solver.add(addsum(conteo_var) == num_variables_por_producto[prod][var_orig])
                var_orig += 1

def restricciones_cuentan(ocupacion_huecos_variables_v_num, ocupacion_huecos_variables_f_num, ocupacion_huecos_variables_den):

    for elem in range(max_intermedias):
        huecos_ocupados = []
        for hueco_num in range(maxDeg):
            for aux in range(0, elem):
                huecos_ocupados.append(If(ocupacion_huecos_variables_v_num[elem][hueco_num][aux], 1, 0))

            for fact in range(num_factores_num):
                huecos_ocupados.append(If(ocupacion_huecos_variables_f_num[elem][hueco_num][fact], 1, 0))

        for hueco_den in range(maxDeg):
            for fact in range(num_factores_den):
                huecos_ocupados.append(If(ocupacion_huecos_variables_den[elem][hueco_den][fact], 1, 0))

        solver.add_soft(addsum(huecos_ocupados) == 0, 1, "min_vars")

#######################################################################################################################################

# Para cada hueco de cada variable, la variable i-ésima del nivel anterior lo ocupa o no - Booleano
ocupacion_huecos_variables_v_num = []

# Para cada hueco de cada variable, el factor i-ésimo lo ocupa o no - Booleano
ocupacion_huecos_variables_f_num = []

ocupacion_huecos_variables_den = []

composicion_variables_intermedias(ocupacion_huecos_variables_v_num, ocupacion_huecos_variables_f_num, ocupacion_huecos_variables_den)
orden_huecos_variables(ocupacion_huecos_variables_v_num, ocupacion_huecos_variables_f_num, ocupacion_huecos_variables_den)
# orden_variables_nivel(ocupacion_huecos_variables_v_num, ocupacion_huecos_variables_v_num, ocupacion_huecos_variables_v_num)

restricciones_huecos_v(ocupacion_huecos_variables_v_num, ocupacion_huecos_variables_f_num, ocupacion_huecos_variables_den)                

# Cada variable, cuántas variables de cada una de las originales contiene - Entero
cuantas_variables = []
cubre_variables_v(ocupacion_huecos_variables_v_num, ocupacion_huecos_variables_f_num, ocupacion_huecos_variables_den, cuantas_variables)

# Para cada hueco de cada monomio, la variable i-ésima del último nivel lo ocupa o no - Booleano
ocupacion_huecos_prod_v_num = []

# Para cada hueco de cada monomio, el factor i-ésimo lo ocupa o no - Booleano
ocupacion_huecos_prod_f_num = []

ocupacion_huecos_prod_den = []

composicion_productos(ocupacion_huecos_prod_v_num, ocupacion_huecos_prod_f_num, ocupacion_huecos_prod_den)
orden_huecos_productos(ocupacion_huecos_prod_v_num, ocupacion_huecos_prod_f_num, ocupacion_huecos_prod_den)
restricciones_huecos_p(ocupacion_huecos_prod_v_num, ocupacion_huecos_prod_f_num, ocupacion_huecos_prod_den)
cubre_variables_p(ocupacion_huecos_prod_v_num, ocupacion_huecos_prod_f_num, ocupacion_huecos_prod_den, cuantas_variables)

restricciones_cuentan(ocupacion_huecos_variables_v_num, ocupacion_huecos_variables_f_num, ocupacion_huecos_variables_den)

if solver.check() == sat:
    m = solver.model()
    
    print("\n=== COMPOSICIÓN DE VARIABLES INTERMEDIAS ===")
    for var in range(max_intermedias):
        partes_num = []
        partes_den = []
        
        # Numerador
        for hueco_num in range(maxDeg):
            # Variables anteriores
            for prev_var in range(var):
                if m.eval(ocupacion_huecos_variables_v_num[var][hueco_num][prev_var]):
                    partes_num.append(f"VI_{prev_var}")
            # Factores numerador
            for fact in range(num_factores_num):
                if m.eval(ocupacion_huecos_variables_f_num[var][hueco_num][fact]):
                    partes_num.append(f"Fnum_{fact}")
        
        # Denominador
        for hueco_den in range(maxDeg):
            # Factores denominador
            for fact in range(num_factores_den):
                if m.eval(ocupacion_huecos_variables_den[var][hueco_den][fact]):
                    partes_den.append(f"Fden_{fact}")
        
        if partes_den:
            print(f"VI_{var} = ({' * '.join(partes_num)}) / ({' * '.join(partes_den)})")
        else:
            print(f"VI_{var} = {' * '.join(partes_num)}")
    
    print("\n=== COMPOSICIÓN DE PRODUCTOS ===")
    for prod in range(num_productos):
        if grados_prod[prod] <= maxDeg:
            print(f"Producto {prod}: NO pasa de grado ({grados_prod[prod]} ≤ {maxDeg})")
        else:
            partes_num = []
            partes_den = []
            
            # Numerador: VI y factores
            for hueco_num in range(maxDeg):
                for var in range(max_intermedias):
                    if m.eval(ocupacion_huecos_prod_v_num[prod][hueco_num][var]):
                        partes_num.append(f"VI_{var}")
                for fact in range(num_factores_num):
                    if m.eval(ocupacion_huecos_prod_f_num[prod][hueco_num][fact]):
                        partes_num.append(f"Fnum_{fact}")

            # Denominador: factores
            for hueco_den in range(maxDeg):
                for fact in range(num_factores_den):
                    if m.eval(ocupacion_huecos_prod_den[prod][hueco_den][fact]):
                        partes_den.append(f"Fden_{fact}")

            if partes_den:
                print(f"Producto {prod}: grado {grados_prod[prod]} > {maxDeg}")
                print(f"   = ({' * '.join(partes_num)}) / ({' * '.join(partes_den)})")
            else:
                print(f"Producto {prod}: grado {grados_prod[prod]} > {maxDeg}")
                print(f"   = {' * '.join(partes_num)}")

else:
    print("\n❌ No se ha encontrado una solución.")

# file.write(str(solver.assertions()))

# with open("debug_constraints.smt2", "w") as out:
#     out.write(solver.to_smt2())