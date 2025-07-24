#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""

Versión similar a la de los monomios, donde se tienen tantos huecos como el grado máximo para formar las nuevas variables con las fracciones
que se expanden

Permitir que las variables se formen con VI de cualquier nivel, no solo del anterior, además de factores

"""

import itertools
import json
from z3 import *
import argparse
import time

def addsum(a):
    if len(a) == 0:
        return 0
    else:
        asum = a[0]
        for i in range(1,len(a)):
            asum = asum + a[i]
        return asum
    
def z3max(lst):
    if not lst:
        return IntVal(0)
    max_expr = lst[0]
    for elem in lst[1:]:
        max_expr = If(elem > max_expr, elem, max_expr)
    return max_expr

def expand_factors(factors): # [x_1, x_1, x_2]
    expanded = []

    for f in factors:
        var = 'x_' + str(f["signal"])
        expanded.extend([var] * f["degree"])
    return expanded

def generate_combinations(expanded, maxDeg):
    combinaciones = set() # Conjunto para que no se repitan los elementos

    for r in range(1, min(maxDeg, len(expanded)) + 1): # Para que solo saque expresiones como mucho de maxDeg, el resto no me sirven como variables intermedias
        # combinations(p, r) -> tuplas de longitud r ordenadas y no repetidas de los elementos en p
        for combo in itertools.combinations(expanded, r):
            combinaciones.add(combo)

    return combinaciones

parser = argparse.ArgumentParser()

parser.add_argument("filein", help=".json file",
                    type=str)

args=parser.parse_args()

f = open(args.filein)
data = json.load(f)

expresiones = data["expressions"]
num_expresiones = len(expresiones)
maxDeg = data["degree"]

candidatos = set()
cjto_variables = set()

for e in range(num_expresiones):
    # Tupla numerador + grado numerador + denominador + grado denominador
    candidatos.add((
        tuple(expresiones[e]["values"][0]["signals"]),
        expresiones[e]["values"][0]["degree"],
        tuple(expresiones[e]["values"][1]["signals"]),
        expresiones[e]["values"][1]["degree"]
    ))
    cjto_variables.add(tuple(expresiones[e]["values"][0]["signals"]))    
    cjto_variables.add(tuple(expresiones[e]["values"][1]["signals"]))

# if mayor_grado_polinomio <= maxDeg:
#     sys.exit("No es necesario añadir ninguna variable auxiliar.")

cjto_variables = sorted(list(cjto_variables))
lista_candidatos = list(candidatos) # sorted(list(candidatos), key=str) # Ordenar por el toString de la combinación
num_candidatos = len(lista_candidatos)

num_variables_expresion = []
# La expresión, cuántas variables de cada tiene
for var in cjto_variables:
    counts = 0
    for e in range(num_expresiones):
        if expresiones[e]["values"][0]["signals"] == var: counts += 1
        if expresiones[e]["values"][1]["signals"] == var: counts += 1

    num_variables_expresion.append(counts)
    
# Para cada expresión, cuántas variables de cada contiene
num_variables_por_expresion = []
for c in lista_candidatos:
    counts = []
    for var in cjto_variables:
        cuantas = 0
        if c[0] == var: cuantas += 1
        if c[2] == var: cuantas += 1
        counts.append(cuantas)

    num_variables_por_expresion.append(counts)

# Cada candidato, cuántas veces aparece para poder trabajar con los candidatos para crear las nuevas variables en función de si se expanden o no
# num_veces_candidato = []
# for c in lista_candidatos:
#     num = 0
#     for exp in range(num_expresiones):
#         if expresiones[exp]["values"][0]["signals"] == c[0] and expresiones[exp]["values"][1]["signals"] == c[2]: num += 1
    
#     num_veces_candidato.append(num)

print("Candidatos: " + str(lista_candidatos))
print("Variables expresión: " + str(num_variables_expresion))
print("Variables por expresión: " + str(num_variables_por_expresion))
print("Conjunto variables: " + str(cjto_variables))
solver = Solver()

##### PARAMETROS #####
num_niveles = 2 # max(1, int(math.ceil(math.log(mayor_grado_polinomio + 1, 2))))  # log base 2 del mayor grado del polinomio
num_variables_por_nivel = 6 # max(2, math.ceil(num_monomios))
max_intermedias = 11

inicio = time.time()

expando = []
for exp in range(num_candidatos):
    expando.append(Bool("expando_" + str(exp)))

# Declaración de los huecos de los que disponen las VI para formarse
def composicion_variables_intermedias(ocupacion_huecos_variables_v, ocupacion_huecos_variables_f):
    for nivel in range(num_niveles):
        huecos_nivel_v = []
        huecos_nivel_f = []
        for variable in range(num_variables_por_nivel):
            huecos_var_v = []
            huecos_var_f = []
            for hueco in range(maxDeg):
                ocupa_v = []
                ocupa_f = []
                
                for nivel_anterior in range(0, nivel):
                    ocupa_v_anterior = []
                    for variable_nivel_anterior in range(num_variables_por_nivel):
                        ocupa_v_anterior.append(Bool("ocupav_" + str(nivel) + "_" + str(variable) + "_" + str(hueco) + "_" + str(nivel_anterior) + "_" + str(variable_nivel_anterior)))

                    ocupa_v.append(ocupa_v_anterior)

                for factor in range(num_candidatos):
                    ocupa_f.append(Bool("ocupaf_" + str(nivel) + "_" + str(variable) + "_" + str(hueco) + "_" + str(factor)))
                
                huecos_var_v.append(ocupa_v)
                huecos_var_f.append(ocupa_f)
            
            huecos_nivel_v.append(huecos_var_v)
            huecos_nivel_f.append(huecos_var_f)
        
        ocupacion_huecos_variables_v.append(huecos_nivel_v)
        ocupacion_huecos_variables_f.append(huecos_nivel_f)

# Para todo hueco, los siguientes deben tener índice mayor. Todos los índices anteriores no deben estar activados. Primero aparecen otras VI y luego los factores
def orden_huecos_variables(ocupacion_huecos_variables_v, ocupacion_huecos_variables_f):
    for nivel in range(num_niveles):
        for variable in range(num_variables_por_nivel):
            for hueco in range(maxDeg):
                if nivel > 0:
                    for nivel_anterior in range(0, nivel): 
                        for variable_nivel_anterior in range(num_variables_por_nivel):
                            for hueco_sig in range(hueco + 1, maxDeg):
                                # Ninguna de ningún nivel anterior pueden tener dependencia en los siguientes huecos
                                for niveles_anteriores in range(0, nivel_anterior):
                                    for var in range(num_variables_por_nivel):
                                        solver.add(Implies(ocupacion_huecos_variables_v[nivel][variable][hueco][nivel_anterior][variable_nivel_anterior], Not(ocupacion_huecos_variables_v[nivel][variable][hueco_sig][niveles_anteriores][var])))
                                
                                # Las anteriores de su nivel tampoco pueden tener dependencia en los siguientes huecos
                                for variables_anteriores in range(0, variable_nivel_anterior):
                                    solver.add(Implies(ocupacion_huecos_variables_v[nivel][variable][hueco][nivel_anterior][variable_nivel_anterior], Not(ocupacion_huecos_variables_v[nivel][variable][hueco_sig][nivel_anterior][variables_anteriores])))

                    for factor in range(num_candidatos):
                        for hueco_sig in range(hueco + 1, maxDeg):
                            # Ninguna variable de un nivel anterior puede tener dependencia en los siguientes huecos
                            for nivel_anterior in range(0, nivel):
                                for var_nivel_anterior in range(num_variables_por_nivel):
                                    solver.add(Implies(ocupacion_huecos_variables_f[nivel][variable][hueco][factor], Not(ocupacion_huecos_variables_v[nivel][variable][hueco_sig][nivel_anterior][var_nivel_anterior])))

                            # La anteriores de su nivel tampoco pueden tener dependencia en los siguientes huecos
                            for variables_anteriores in range(0, num_variables_por_nivel):
                                solver.add(Implies(ocupacion_huecos_variables_f[nivel][variable][hueco][factor], Not(ocupacion_huecos_variables_v[nivel][variable][hueco_sig][nivel_anterior][variables_anteriores])))

                            for factores_anteriores in range(0, factor):
                                solver.add(Implies(ocupacion_huecos_variables_f[nivel][variable][hueco][factor], Not(ocupacion_huecos_variables_f[nivel][variable][hueco_sig][factores_anteriores])))
                        
                        # NUEVO - Solo se pueden utilizar candidatos que se haya decidido expandir
                        solver.add(Implies(ocupacion_huecos_variables_f[nivel][variable][hueco][factor], expando[factor]))
                else:   
                    for factor in range(num_candidatos):
                        for hueco_sig in range(hueco + 1, maxDeg):
                            for factores_anteriores in range(0, factor):
                                solver.add(Implies(ocupacion_huecos_variables_f[nivel][variable][hueco][factor], Not(ocupacion_huecos_variables_f[nivel][variable][hueco_sig][factores_anteriores])))
                    
                    solver.add(Implies(ocupacion_huecos_variables_f[nivel][variable][hueco][factor], expando[factor]))

# Dentro de un mismo nivel, primero aparecen las VI que contienen factores y luego las que no
def orden_variables_nivel(ocupacion_huecos_variables_f):
    for nivel in range(1, num_niveles): # El primer nivel siempre va a tener solo factores
        for variable in range(num_variables_por_nivel - 1):
            contiene_factores_actual = []
            contiene_factores_sig = []

            for hueco in range(maxDeg):
                for factor in range(num_candidatos):
                    contiene_factores_actual.append(If(ocupacion_huecos_variables_f[nivel][variable][hueco][factor], 1, 0))

            for hueco_var_sig in range(maxDeg):
                for factores_var_sig in range(num_candidatos):
                    contiene_factores_sig.append(If(ocupacion_huecos_variables_f[nivel][variable + 1][hueco_var_sig][factores_var_sig], 1, 0))

            solver.add(Implies(addsum(contiene_factores_actual) == 0, addsum(contiene_factores_sig) == 0))

# Se obliga a rellenar los huecos de arriba a abajo, si un hueco está vacío, todos los siguientes también
def rellenar_huecos_variables_en_orden(ocupacion_huecos_variables_v, ocupacion_huecos_variables_f, nivel, variable):

    for hueco in range(1, maxDeg):
        suma_actual = []
        suma_anterior = []
        for nivel_anterior in range(0, nivel):
            for var in ocupacion_huecos_variables_v[nivel][variable][hueco][nivel_anterior]:
                suma_actual.append(If(var, 1, 0))

        for fact in ocupacion_huecos_variables_f[nivel][variable][hueco]:
            suma_actual.append(If(fact, 1, 0))

        for nivel_anterior in range(0, nivel):
            for var in ocupacion_huecos_variables_v[nivel][variable][hueco - 1][nivel_anterior]:
                suma_anterior.append(If(var, 1, 0))

        for fact in ocupacion_huecos_variables_f[nivel][variable][hueco - 1]:
            suma_anterior.append(If(fact, 1, 0))

    solver.add(Implies(addsum(suma_actual) > 0, addsum(suma_anterior) > 0))

# Restricciones de ocupación de los huecos de las VI
def restricciones_huecos_v(ocupacion_huecos_variables_v, ocupacion_huecos_variables_f):
    for nivel in range(num_niveles):
        for variable in range(num_variables_por_nivel):
            cumple_grado = []
            variables_activas_por_var = []

            for hueco in range(maxDeg):
                variables_activas_por_hueco = []
                if nivel > 0:
                    for nivel_anterior in range(0, nivel):
                        for variable_nivel_anterior in range(num_variables_por_nivel):

                            # solver.add(Implies(ocupacion_huecos_variables_v[nivel][variable][hueco][nivel_anterior][variable_nivel_anterior], activas[nivel_anterior][variable_nivel_anterior]))

                            cumple_grado.append(If(ocupacion_huecos_variables_v[nivel][variable][hueco][nivel_anterior][variable_nivel_anterior], 1, 0))

                            variables_activas_por_hueco.append(If(ocupacion_huecos_variables_v[nivel][variable][hueco][nivel_anterior][variable_nivel_anterior], 1, 0))

                # La variable elem de nivel cuántas veces utiliza el factor fact
                grado_num = []
                grado_den = []
                for factor in range(num_candidatos):
                    grado_num.append(If(ocupacion_huecos_variables_f[nivel][variable][hueco][factor], lista_candidatos[factor][1], 0))
                    grado_den.append(If(ocupacion_huecos_variables_f[nivel][variable][hueco][factor], lista_candidatos[factor][3], 0))

                    variables_activas_por_hueco.append(If(ocupacion_huecos_variables_f[nivel][variable][hueco][factor], 1, 0))

                cumple_grado.append(z3max(grado_num) + z3max(grado_den))
                # Puede dejarse vacío o ocuparse por 1 único elemento, ya sea VI o factor
                solver.add(addsum(variables_activas_por_hueco) <= 1)
                variables_activas_por_var.append(addsum(variables_activas_por_hueco))

            rellenar_huecos_variables_en_orden(ocupacion_huecos_variables_v, ocupacion_huecos_variables_f, nivel, variable)
            
            # La suma del grado de todo lo que se utiliza para formar la variable debe ser menor o igual que el grado máximo
            solver.add(addsum(cumple_grado) <= maxDeg)

            # Eliminar variables que están formadas por una única variable intermedia/factor o por ninguna
            solver.add(addsum(variables_activas_por_var) > 1)
            # solver.add(Implies(addsum(variables_activas_por_var) == 0, Not(activas[nivel][variable])))

            # Todas las variables de un mismo nivel deben ser distintas, porque luego se da la opción de poder elegirla más de una vez en huecos distintos
            # variables_distintas_nivel(ocupacion_huecos_variables_v, ocupacion_huecos_variables_f, nivel)

# Cuántas variables originales cubre esta VI con los elementos que ocupan sus huecos
def cubre_variables_v(ocupacion_huecos_variables_v, ocupacion_huecos_variables_f, cuantas_variables):

    for nivel in range(num_niveles):
        cuantas_nivel = []
        for elem in range(num_variables_por_nivel):
            variables_elem = []
            for variable_original in range(len(cjto_variables)):
                variables_elem.append(Int("var_" + str(nivel) + "_" + str(elem) + "_" + str(variable_original)))
            
            cuantas_nivel.append(variables_elem)
        
        cuantas_variables.append(cuantas_nivel)

    for nivel in range(num_niveles):
        for elem in range(num_variables_por_nivel):
            for variable_original in range(len(cjto_variables)):
                conteo_var = []
                for hueco in range(maxDeg):
                    if nivel > 0:
                        for nivel_anterior in range(0, nivel):
                            for var in range(num_variables_por_nivel):
                                # Si se ha utilizado en esta VI aporta las variables que contenga
                                conteo_var.append(If(ocupacion_huecos_variables_v[nivel][elem][hueco][nivel_anterior][var], cuantas_variables[nivel_anterior][var][variable_original], 0))

                    for fact in range(num_candidatos):
                        conteo_var.append(If(ocupacion_huecos_variables_f[nivel][elem][hueco][fact], num_variables_por_expresion[fact][variable_original], 0))
                            
                solver.add(cuantas_variables[nivel][elem][variable_original] == addsum(conteo_var))

# Declaración de los huecos de los que dispone la expresión para formarse
def composicion_expresion(ocupacion_huecos_expresion_v, ocupacion_huecos_expresion_f):
    
    for hueco in range(maxDeg):
        ocupa_v = []
        ocupa_f = []

        # Puede coger VI de cualquier nivel
        for nivel in range(num_niveles):
            ocupa_v_nivel = []
            for variable in range(num_variables_por_nivel):                
                ocupa_v_nivel.append(Bool("ocupamv_" + str(hueco) + "_" + str(nivel) + "_" + str(variable))) 
            ocupa_v.append(ocupa_v_nivel)

        for factor in range(num_candidatos):
            ocupa_f.append(Bool("ocupamf_" + str(hueco) + "_" + str(factor)))
    
    ocupacion_huecos_expresion_v.append(ocupa_v)
    ocupacion_huecos_expresion_f.append(ocupa_f)

# Para todo hueco, los siguientes deben tener índice mayor. Todos los índices anteriores no deben estar activados. Se podría unificar en una función con la de las variables
def orden_huecos_expresion(ocupacion_huecos_expresion_v, ocupacion_huecos_expresion_f):
    for hueco in range(maxDeg):
        for nivel in range(num_niveles):
            for variable_nivel_anterior in range(num_variables_por_nivel): 
                for hueco_sig in range(hueco + 1, maxDeg):
                    for nivel_anterior in range(0, nivel):
                        for var_nivel_anterior in range(num_variables_por_nivel):
                            solver.add(Implies(ocupacion_huecos_expresion_v[hueco][nivel][variable_nivel_anterior], Not(ocupacion_huecos_expresion_v[hueco_sig][nivel_anterior][var_nivel_anterior])))
                    
                    for variables_anteriores in range(0, variable_nivel_anterior):
                        solver.add(Implies(ocupacion_huecos_expresion_v[hueco][nivel][variable_nivel_anterior], Not(ocupacion_huecos_expresion_v[hueco_sig][nivel][variables_anteriores])))

        for factor in range(num_candidatos):
            for hueco_sig in range(hueco + 1, maxDeg):
                for nivel_anterior in range(num_niveles):
                    for var_nivel_anterior in range(num_variables_por_nivel):
                        solver.add(Implies(ocupacion_huecos_expresion_f[hueco][factor], Not(ocupacion_huecos_expresion_v[hueco_sig][nivel_anterior][var_nivel_anterior])))
            
                for factores_anteriores in range(0, factor):
                    solver.add(Implies(ocupacion_huecos_expresion_f[hueco][factor], Not(ocupacion_huecos_expresion_f[hueco_sig][factores_anteriores])))

            solver.add(Implies(ocupacion_huecos_expresion_f[hueco][factor], Not(expando[factor])))
        else: 
            for factor in range(num_candidatos):
                for hueco_sig in range(hueco + 1, maxDeg):
                        for factores_anteriores in range(0, factor):
                            solver.add(Implies(ocupacion_huecos_expresion_f[hueco][factor], Not(ocupacion_huecos_expresion_f[hueco_sig][factores_anteriores])))
                
                solver.add(Implies(ocupacion_huecos_expresion_f[hueco][factor], Not(expando[factor])))

def rellenar_huecos_expresion_en_orden(ocupacion_huecos_expresion_v, ocupacion_huecos_expresion_f):

    for hueco in range(1, maxDeg):
        suma_actual = []
        suma_anterior = []

        # if degree[mon] > maxDeg:
        for nivel_anterior in range(num_niveles):
            for var in ocupacion_huecos_expresion_v[hueco][nivel_anterior]:
                suma_actual.append(If(var, 1, 0))

        for fact in ocupacion_huecos_expresion_f[hueco]:
            suma_actual.append(If(fact, 1, 0))

        # if degree[mon] > maxDeg:
        for nivel_anterior in range(num_niveles):
            for var in ocupacion_huecos_expresion_v[hueco - 1][nivel_anterior]:
                suma_anterior.append(If(var, 1, 0))

        for fact in ocupacion_huecos_expresion_f[hueco - 1]:
            suma_anterior.append(If(fact, 1, 0))

        solver.add(Implies(addsum(suma_actual) > 0, addsum(suma_anterior) > 0))

# Restricciones de ocupación de los huecos de los monomios
def restricciones_huecos_e(ocupacion_huecos_expresion_v, ocupacion_huecos_expresion_f):
    suma_grado = []
    for hueco in range(maxDeg):
        activos_hueco = []
        for nivel_anterior in range(num_niveles):
            for variable in range(num_variables_por_nivel):
                activos_hueco.append(If(ocupacion_huecos_expresion_v[hueco][nivel_anterior][variable], 1, 0))
                suma_grado.append(If(ocupacion_huecos_expresion_v[hueco][nivel_anterior][variable], 1, 0))

        for factor in range(num_candidatos):
            activos_hueco.append(If(ocupacion_huecos_expresion_f[hueco][factor], 1, 0))
            suma_grado.append(If(ocupacion_huecos_expresion_f[hueco][factor], 1, 0))
        
        solver.add(addsum(activos_hueco) <= 1)

        rellenar_huecos_expresion_en_orden(ocupacion_huecos_expresion_v, ocupacion_huecos_expresion_f, mon)

        # SUMA DE LAS LONGITUDES DE LAS EXPRESIONES DE LAS QUE DEPENDE. NO ES TRIVIAL por contrucción porque al poder meter factores, el grado aumenta
        solver.add(addsum(suma_grado) <= maxDeg) 

# Comprobación de que con los elementos que ocupan los huecos del monomio se cubren todas las variables originales que tenía en un inicio
def cubre_variables_e(ocupacion_huecos_expresion_v, ocupacion_huecos_expresion_f):
    for var in range(len(cjto_variables)):
        conteo_var = []
        for hueco in range(maxDeg):
            for nivel_anterior in range(num_niveles):
                for elem in range(num_variables_por_nivel):
                    conteo_var.append(If(ocupacion_huecos_expresion_v[hueco][nivel_anterior][elem], cuantas_variables[nivel_anterior][elem][var], 0))

            for fact in range(num_candidatos):
                conteo_var.append(If(ocupacion_huecos_expresion_f[hueco][fact], num_variables_por_expresion[fact][var], 0))

        solver.add(addsum(conteo_var) == num_variables_expresion[var])

# Qué variables realmente cuentan
def restricciones_cuentan(cuentan, suma_cuentan, ocupacion_huecos_variables_v, ocupacion_huecos_expresion_v):
    # Se utiliza en la variable y el número de huecos ocupados en dicha variable es mayor que 1
    for nivel in range(num_niveles):
        cuentan_nivel = []
        for elem in range(num_variables_por_nivel):
            cuentan_nivel.append(Bool("cuenta_" + str(nivel) + "_" + str(elem)))
        
        cuentan.append(cuentan_nivel)

    # Para monomios. Si utiliza una variable, dicha variable, cuenta
    for hueco in range(maxDeg):
        for nivel_anterior in range(num_niveles):
            for elem in range(num_variables_por_nivel):
                solver.add(Implies(ocupacion_huecos_expresion_v[hueco][nivel_anterior][elem], cuentan[nivel_anterior][elem]))

    # Para variables, propagar hacia atrás. Es decir, tienes las variables que se utilizan en los monomios(cuentan = true). Las VI que se utilicen para
    # rellenar los huecos de dicha VI usada en un monomio, son las que realmente cuentan. NO hay que tener en cuenta que se utilicen junto con 
    # otra variable / factor porque hay una restricción arriba que obliga a que las variables tengan más de 1 hueco ocupado

    for nivel in range(num_niveles - 1):
        for variable in range(num_variables_por_nivel):
            for nivel_siguiente in range(nivel + 1, num_niveles):
                for var_nivel_sig in range(num_variables_por_nivel):
                    for hueco in range(maxDeg):
                        solver.add(Implies(And(cuentan[nivel_siguiente][var_nivel_sig], ocupacion_huecos_variables_v[nivel_siguiente][var_nivel_sig][hueco][nivel][variable]), cuentan[nivel][variable]))

    for nivel in range(num_niveles):
        for elem in range(num_variables_por_nivel):
            usado_elem = []
            suma_cuentan.append(If(cuentan[nivel][elem], 1, 0))
            # solver.add_soft(Not(cuentan[nivel][elem]), 1, "cuentan")
            for hueco in range(maxDeg):
                usado_elem.append(If(ocupacion_huecos_expresion_v[hueco][nivel][elem], 1, 0))
        
            for nivel_siguiente in range(nivel + 1, num_niveles):
                for elem_nivel_sig in range(num_variables_por_nivel):
                    for hueco in range(maxDeg):
                        usado_elem.append(If(ocupacion_huecos_variables_v[nivel_siguiente][elem_nivel_sig][hueco][nivel][elem], 1, 0))

            solver.add(Implies(addsum(usado_elem) == 0, Not(cuentan[nivel][elem])))


#######################################################################################################################################

# Para cada hueco de cada variable, la variable i-ésima del nivel anterior lo ocupa o no - Booleano
ocupacion_huecos_variables_v = []

# Para cada hueco de cada variable, el factor i-ésimo lo ocupa o no - Booleano
ocupacion_huecos_variables_f = []

composicion_variables_intermedias(ocupacion_huecos_variables_v, ocupacion_huecos_variables_f)
orden_huecos_variables(ocupacion_huecos_variables_v, ocupacion_huecos_variables_f)
orden_variables_nivel(ocupacion_huecos_variables_f)

restricciones_huecos_v(ocupacion_huecos_variables_v, ocupacion_huecos_variables_f)                

# Cada variable, cuántas variables de cada una de las originales contiene - Entero
cuantas_variables = []
cubre_variables_v(ocupacion_huecos_variables_v, ocupacion_huecos_variables_f, cuantas_variables)

# Para cada hueco de cada monomio, la variable i-ésima del último nivel lo ocupa o no - Booleano
ocupacion_huecos_expresion_v = []

# Para cada hueco de cada monomio, el factor i-ésimo lo ocupa o no - Booleano
ocupacion_huecos_expresion_f = []

composicion_expresion(ocupacion_huecos_expresion_v, ocupacion_huecos_expresion_f)
orden_huecos_expresion(ocupacion_huecos_expresion_v, ocupacion_huecos_expresion_f)
restricciones_huecos_e(ocupacion_huecos_expresion_v, ocupacion_huecos_expresion_f)
cubre_variables_e(ocupacion_huecos_expresion_v, ocupacion_huecos_expresion_f)

# Para cada VI, cuenta realmente como VI o no, pese a estar activa -> Igual se puede ahorrar con no repetidas en un nivel???
cuentan = []
suma_cuentan = []
restricciones_cuentan(cuentan, suma_cuentan, ocupacion_huecos_variables_v, ocupacion_huecos_expresion_v)
solver.add(addsum(suma_cuentan) <= max_intermedias)

if solver.check() == sat:
    fin = time.time()

    print(f"Tiempo de ejecución: {fin - inicio:.5f} segundos")       
    m = solver.model()

    print("Resumen de expresiones expandibles y resultantes:\n")

    # Variables que se expanden
    expanden = [i for i in range(num_expresiones) if modelo.evaluate(expando[i]) == True]
    no_expand = [i for i in range(num_expresiones) if modelo.evaluate(expando[i]) == False]

    # Función para convertir fracción a texto
    def fraccion_a_texto(exp):
        num_signals = expresiones[exp]["values"][0]["signals"]
        den_signals = expresiones[exp]["values"][1]["signals"]
        return f"({'+'.join(map(str, num_signals))}) / ({'+'.join(map(str, den_signals))})"

    # 1. Mostrar por cada variable expandida, con qué se forma
    print("Variables EXPANDIDAS y sus unificaciones:")
    ya_vistas = set()
    expresiones_resultantes = []

    for i in expanden:
        grupo = [i]
        for j in range(num_expresiones):
            if i != j and modelo.evaluate(juntar[i][j]):
                grupo.append(j)
        grupo_set = frozenset(grupo)
        if len(grupo) > 1 and grupo_set not in ya_vistas:
            ya_vistas.add(grupo_set)
            expresiones_resultantes.append(sorted(grupo))
            print(f"- Expresión expandida {i} forma una nueva combinación con: {sorted(grupo)}")
            for g in sorted(grupo):
                print(f"    · {g}: {fraccion_a_texto(g)}")
        elif len(grupo) == 1:
            # Se expandió pero no se unió con nadie más
            print(f"- Expresión expandida {i} no se unificó con otras:")
            print(f"    · {i}: {fraccion_a_texto(i)}")

    # 2. Mostrar expresiones finales formadas
    print("\nExpresiones RESULTANTES formadas por unificaciones:")
    for idx, grupo in enumerate(expresiones_resultantes):
        print(f"· Expresión {idx + 1} formada por: {grupo}")
        for g in grupo:
            print(f"    · {g}: {fraccion_a_texto(g)}")

    # 3. Mostrar fracciones originales que NO se han expandido
    if no_expand:
        print("\nFracciones ORIGINALES no expandidas:")
        for i in no_expand:
            print(f"· {i}: {fraccion_a_texto(i)}")
    else:
        print("\nNo hay fracciones originales sin expandir.")

else:
    print("\n❌ No se ha encontrado una solución.")

# file.write(str(solver.assertions()))

# with open("debug_constraints.smt2", "w") as out:
#     out.write(solver.to_smt2())