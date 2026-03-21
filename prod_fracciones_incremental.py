#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Simetrías de variables
# Otra opción: quién me usa: booleana de si es usada por intermedia/final o no, y quien la usa. Si una tiene a falso los 2, las siguientes también
# Primero intermedias usadas por otras intermedias y luego las usadas por el final (hecho). 
# DEntro de las que se usan en intermedias, que se utilicen en orden
# Las variables llenas al principio y medio llenas después
# Garantizar que no se pierden soluciones, cualquier cosa que quita repetidos, no elimina soluciones, solo evita que la misma solucion tenga varias representaciones --> Demostrar
# Ir apuntando todo
# Determinar máximo de max_intermediate

#PARA max_intermediate
# Sumar g_n/g + r dividiendo entre g todo el rato hasta que el grado sea menor que g e igual para denominador porque coges variables
# que solo tienen de uno de ambos

# Otra forma: el que tenga mayor grado coges g, iterar n/g y d/(g-1) o viceversa hasta que ambos queden menor de g. maximo de lo que salga en num y den
# Búsqueda incremental. Si pones un numero muy grande de variables escala mal

# Entre el maximo que se calcula con lo previous y el que yo tenia puesto de // metes tantos pushes y en el bucle se va haciendo pop
# medir tiempos con cada vez más variables

import json
from z3 import *

def addsum(a):
    if len(a) == 0:
        return IntVal(0)
    else:
        asum = a[0]
        for i in range(1,len(a)):
            asum = asum + a[i]
        return asum
    
def fun_max_intermediate(degree_num, degree_den, maxDeg): #Demostrar que no me quedo corta como para que peuda dar unsat
    resto = 0
    intermediate_num = 0

    while degree_num > maxDeg:
        intermediate_num += degree_num // maxDeg
        resto = degree_num % maxDeg
        degree_num = (degree_num // maxDeg) + resto

    resto = 0
    intermediate_den = 0

    while degree_den > maxDeg:
        intermediate_den += degree_den // maxDeg
        resto = degree_den % maxDeg
        degree_den = (degree_den // maxDeg) + resto

    return max(intermediate_num, intermediate_den)

def print_solucion(id, m, max_intermediate, num_original_variables_var_num, num_original_variables_var_den, variables_covered_num, variables_covered_den,
    var_uses_previous_num, var_uses_previous_den, product_uses_var_in_num, product_uses_var_in_den, degree_num_variables, degree_den_variables, product_uses_initials_in_num, 
    product_uses_initials_in_den, degree_prod_num, degree_prod_den):

        dependencias = {}

        # Variables intermedias
        for var in range(max_intermediate):
            num = m.eval(num_original_variables_var_num[var], model_completion=True).as_long()
            den = m.eval(num_original_variables_var_den[var], model_completion=True).as_long()
            cubre_num = m.eval(variables_covered_num[var], model_completion=True).as_long()
            cubre_den = m.eval(variables_covered_den[var], model_completion=True).as_long()

            deps_num = []
            deps_den = []

            for previous in range(var):
                val_num = m.eval(var_uses_previous_num[var][previous], model_completion=True)
                val_den = m.eval(var_uses_previous_den[var][previous], model_completion=True)
                if is_true(val_num):
                    deps_num.append(previous) # f"VI_{id}_{previous}")
                if is_true(val_den):
                    deps_den.append(previous) # f"VI_{id}_{previous}")

            print(f"VI_{id}_{var}: num = {num}, den = {den}, cubre {cubre_num} en num y {cubre_den} en den")

            dependencias[var] = {"num": deps_num, "den": deps_den}

        # Variables usadas en el producto final
        usadas_num = []
        usadas_den = []

        for var in range(max_intermediate):
            usa_num = m.eval(product_uses_var_in_num[var], model_completion=True)
            usa_den = m.eval(product_uses_var_in_den[var], model_completion=True)
            if is_true(usa_num):
                usadas_num.append(var) # f"VI_{id}_{var}")
            elif is_true(usa_den):
                usadas_den.append(var) # f"VI_{id}_{var}")

        # inic_num = m.eval(product_uses_initials_in_num, model_completion=True).as_long()
        # inic_den = m.eval(product_uses_initials_in_den, model_completion=True).as_long()

        # producto_str_num = " * ".join(usadas_num) if usadas_num else "1"
        # producto_str_den = " * ".join(usadas_den) if usadas_den else "1"

        # print(f"\nProducto final: ({producto_str_num} * forig_{id}_n_{inic_num}) / ({producto_str_den} * forig_{id}_d_{inic_den})")

        # Construir JSON final
        vi_detalles = []
        for var in range(max_intermediate):

            gr_num = int(m.eval(degree_num_variables[var], model_completion=True).as_long())
            gr_den = int(m.eval(degree_den_variables[var], model_completion=True).as_long())

            if gr_num == 0 and gr_den == 0:
                continue

            deps_num = dependencias[var]["num"]
            deps_den = dependencias[var]["den"]

            num_orig = int(m.eval(num_original_variables_var_num[var], model_completion=True).as_long())
            den_orig = int(m.eval(num_original_variables_var_den[var], model_completion=True).as_long())

            # comp_num = []
            # comp_den = []

            # comp_num.extend(deps_num)
            # comp_den.extend(deps_den)

            # if num_orig > 0:
            #     comp_num.append(f"forig_{id}_n_{num_orig}")
            # if den_orig > 0:
            #     comp_den.append(f"forig_{id}_d_{den_orig}")

            usada_en_otra_var = False

            for sig in range(var + 1, max_intermediate):
                if var in dependencias[sig]["den"]: usada_en_otra_var = True # var in dependencias[sig]["num"] or 

            # si esta VI aparece en el denominador final hay que invertir
            if var in usadas_den or usada_en_otra_var:

                detalles_num = {
                    "intermediate": deps_den,
                    "orig_num": 0,
                    "orig_den": den_orig
                }

                detalles_den = {
                    "intermediate": deps_num,
                    "orig_num": num_orig,
                    "orig_den": 0
                }

                # comp_num, comp_den = comp_den, comp_num
            else:

                detalles_num = {
                    "intermediate": deps_num,
                    "orig_num": num_orig,
                    "orig_den": 0
                }

                detalles_den = {
                    "intermediate": deps_den,
                    "orig_num": 0,
                    "orig_den": den_orig
                }

            vi_detalles.append({
                "numerator": detalles_num,
                "denominator": detalles_den
            })

        inic_num_val = m.eval(product_uses_initials_in_num, model_completion=True).as_long()
        inic_den_val = m.eval(product_uses_initials_in_den, model_completion=True).as_long()

        vars_num = []        

        for v in usadas_num:
            # numerador_detalle.append(v)
            vars_num.append(v)

        # if inic_num_val > 0: numerador_detalle.append(f"forig_{id}_n_{inic_num_val}")

        numerador_detalle = {
            "intermediate": vars_num,
            "orig_num": inic_num_val,
            "orig_den": 0
        }

        # denominador_detalle = []
        vars_den = []

        for v in usadas_den:
            vars_den.append(v)

        # if inic_den_val > 0: denominador_detalle.append(f"forig_{id}_d_{inic_den_val}")

        denominador_detalle = {
            "intermediate": vars_den,
            "orig_num": 0,
            "orig_den": inic_den_val
        }

        # numerador_detalle = {
        #     "componentes": componentes_detalle(usadas_num),
        #     "variables_originales": inic_num_val,
        # }

        # denominador_detalle = {
        #     "componentes": componentes_detalle(usadas_den),
        #     "variables_originales": inic_den_val,
        # }

        output_data = {
            "op": "frac",
            "product": {
                "numerator": numerador_detalle,
                "denominator": denominador_detalle
            },
            "intermediate_variables": vi_detalles,
            "degree_numerator": int(m.eval(addsum(degree_prod_num), model_completion=True).as_long()),
            "degree_denominator": int(m.eval(addsum(degree_prod_den), model_completion=True).as_long())
        }

        print(output_data)

        with open("prod.json", "w") as fout:
            json.dump(output_data, fout, indent=4)

        print("\nResult exported to prod.json")


# Meter variables que representan la fracción, cuántas variables se cogen en el numerador, y cuántas en el denominador
def reducir_grado_producto(maxDeg, degree_num, degree_den, id):

    ###### DECLARACIÓN DE VARIABLES ######
    solver = Optimize()

    # Usaremos variables intermedias vi_0, ... vi_{max_intermediate-1}
    max_intermediate = fun_max_intermediate(degree_num, degree_den, maxDeg) # max(degree_num, degree_den) // 2 # maxDeg) + 1 # DEMOSTRAR

    # Cada variable, cuántas variables de las originales tiene del numerador, y cuántas del denominador. Cada variables es un nivel.
    # Las variables del numerador se colocarán en el numerador de la nueva variable y las del denominador en el denominador pero para el recuento final, es necesario saber cuántas eran originalmente del numerador
    num_original_variables_var_num = []
    num_original_variables_var_den = []

    # num_var_i : número de variables originales de numerador que va a agrupar vi_i
    # den_var_i : número de variables originales de denominador que va a agrupar vi_i
    for var in range(max_intermediate):
        num_original_variables_var_num.append(Int("num_var_" + str(var)))
        num_original_variables_var_den.append(Int("den_var_" + str(var)))

    # Cada una de las variables intermedias, utiliza alguna de las variables intermedias previouses o no. 
    # La primera lógicamente no va a utilizar ninguna variable previous, con el bucle interior ya se cubre ese caso
    var_uses_previous_num = []
    var_uses_previous_den = []

    # var_i_usan_j : la variable vi_i utiliza o no vi_j en el numerador para formarse, con j perteneciente a [0, i) 
    # var_i_usad_j : la variable vi_i utiliza o no vi_j en el denominador para formarse, con j perteneciente a [0, i) 
    for var in range(max_intermediate): # Se podría poner como rango 1 - max_intermediate para ahorrar una vuelta
        which_uses_num = []
        which_uses_den = []

        for previous in range(var):
            which_uses_num.append(Bool("var_" + str(var) + "_usan_" + str(previous)))
            which_uses_den.append(Bool("var_" + str(var) + "_usad_" + str(previous)))

        var_uses_previous_num.append(which_uses_num)
        var_uses_previous_den.append(which_uses_den)

    # El producto final, qué variables intermedias utiliza
    product_uses_var_in_num = []
    product_uses_var_in_den = []

    # prodn_var_i : el producto final contiene a la variable vi_i en el numerador
    # prodd_var_i : el producto final contiene a la variable vi_i en el denominador
    for var in range(max_intermediate):
        product_uses_var_in_num.append(Bool("prodn_var_" + str(var)))
        product_uses_var_in_den.append(Bool("prodd_var_" + str(var)))

    # inic_prod_num : número de variables originales de numerador, que no están contenidas en ninguna vi, que agrupa el producto final
    product_uses_initials_in_num = Int("inic_prod_num")

    # inic_prod_den : número de variables originales de denominador, que no están contenidas en ninguna vi, que agrupa el producto final
    product_uses_initials_in_den = Int("inic_prod_den")

    ###### CONSTRAINTS ######

    for var in range(max_intermediate):
        solver.add(And(num_original_variables_var_num[var] >= 0, num_original_variables_var_num[var] <= maxDeg))
        solver.add(And(num_original_variables_var_den[var] >= 0, num_original_variables_var_den[var] <= maxDeg))

    # Para cada variable, cuántas variables originales realmente cubre teniendo en cuenta las originales que tiene de num_variables_originales_var + las que tiene cada variable previous que contiene
    # Es decir, de las originales del numerador, cuántas contiene? Idem con denominador
    variables_covered_num = []
    variables_covered_den = []

    for var in range(max_intermediate): # OK
        cuantas_n = []
        cuantas_d = []
        cuantas_n.append(num_original_variables_var_num[var])
        cuantas_d.append(num_original_variables_var_den[var])

        # Si utiliza una variable previous ahora cubre todas las que tuviera ella también + las suyas
        for previous in range(var):
            cuantas_n.append(If(Or(var_uses_previous_num[var][previous], var_uses_previous_den[var][previous]), variables_covered_num[previous], 0))
            cuantas_d.append(If(Or(var_uses_previous_num[var][previous], var_uses_previous_den[var][previous]), variables_covered_den[previous], 0))

        variables_covered_num.append(addsum(cuantas_n))
        variables_covered_den.append(addsum(cuantas_d))

    # Grado de cada variable: el máximo entre el grado del numerador y del denominador
    degree_num_variables = []
    degree_den_variables = []

    for var in range(max_intermediate): # OK
        degree_n = []
        degree_d = []
        degree_n.append(num_original_variables_var_num[var])
        degree_d.append(num_original_variables_var_den[var])

        for previous in range(var):
            # Si utiliza una variable previous, aporta grado 1
            degree_n.append(If(var_uses_previous_num[var][previous], 1, 0))
            degree_d.append(If(var_uses_previous_den[var][previous], 1, 0))

        solver.add(And(addsum(degree_n) <= maxDeg, addsum(degree_d) <= maxDeg))
        
        degree_num_variables.append(addsum(degree_n))
        degree_den_variables.append(addsum(degree_d))

    # Solo puede ocurrir o que el grado de la variable sea n/n-1, n-1/n o que esté vacía tanto en numerador como denominador
    for var in range(max_intermediate): # OK
        # n_num = And(degree_num_variables[var] == maxDeg, Or(degree_den_variables[var] == 0, degree_den_variables[var] == maxDeg - 1))
        # n_den = And(Or(degree_num_variables[var] == 0, degree_num_variables[var] == maxDeg - 1), degree_den_variables[var] == maxDeg)
        # n_num = And(degree_num_variables[var] == maxDeg, degree_den_variables[var] == (maxDeg - 1))
        # n_den = And(degree_num_variables[var] == (maxDeg - 1), degree_den_variables[var] == maxDeg)

        n_num = degree_num_variables[var] == maxDeg
        n_den = degree_den_variables[var] == maxDeg
        zero = And(degree_num_variables[var] == 0, degree_den_variables[var] == 0)

        solver.add(Or(n_num, Or(n_den, zero)))

    # Si la variable es de la forma n/(n - 1) se utilizará en el numerador, aportando grado 1 y si tiene la forma (n - 1)/n se utilizará en el denominador
    for var in range(max_intermediate): # OK
        for previous in range(var):
            # Si tiene n en el numerador, no puede usarse en el denominador de ninguna variable y viceversa
            solver.add(Implies(degree_num_variables[previous] == maxDeg, Not(var_uses_previous_den[var][previous])))
            solver.add(Implies(degree_den_variables[previous] == maxDeg, Not(var_uses_previous_num[var][previous])))
            solver.add(Implies(And(degree_num_variables[previous] == 0, degree_den_variables[previous] == 0), And(Not(var_uses_previous_num[var][previous]), Not(var_uses_previous_den[var][previous]))))

    solver.add(And(product_uses_initials_in_num >= 0, product_uses_initials_in_num <= maxDeg))
    solver.add(And(product_uses_initials_in_den >= 0, product_uses_initials_in_den <= maxDeg))

    # No puede usarse la misma variable para numerador y denominador
    # for var in range(max_intermediate):
    #     solver.add(Or(Not(product_uses_var_in_num[var]), Not(product_uses_var_in_den[var])))

    # Contar que se cubren todas las variables que había al inicio
    vars_inic_num = []
    vars_inic_den = []

    # Si utiliza una variable, ya sea en numerador o denominador, ahora cubre las variables que ella cubriera
    for var in range(max_intermediate):
        vars_inic_num.append(If(Or(product_uses_var_in_num[var], product_uses_var_in_den[var]), variables_covered_num[var], 0))
        vars_inic_den.append(If(Or(product_uses_var_in_num[var], product_uses_var_in_den[var]), variables_covered_den[var], 0))

    solver.add(And(addsum(vars_inic_num) + product_uses_initials_in_num == degree_num, addsum(vars_inic_den) + product_uses_initials_in_den == degree_den))

    # Si la variable es de la forma n/(n - 1) se utilizará en el numerador, aportando grado 1 y si tiene la forma (n - 1)/n se utilizará en el denominador
    for var in range(max_intermediate): # OK
        # Si tiene n en el numerador, no puede usarse en el denominador de ninguna variable y viceversa
        solver.add(Implies(degree_num_variables[var] == maxDeg, Not(product_uses_var_in_den[var])))
        solver.add(Implies(degree_den_variables[var] == maxDeg, Not(product_uses_var_in_num[var])))
        solver.add(Implies(And(degree_num_variables[var] == 0, degree_den_variables[var] == 0), And(Not(product_uses_var_in_num[var]), Not(product_uses_var_in_den[var]))))

    # Comprobar que no te pasas de grado en el producto final
    degree_prod_num = [] # OK
    degree_prod_den = []

    degree_prod_num.append(product_uses_initials_in_num)
    degree_prod_den.append(product_uses_initials_in_den)

    for var in range(max_intermediate):
        degree_prod_num.append(If(product_uses_var_in_num[var], 1, 0))
        degree_prod_den.append(If(product_uses_var_in_den[var], 1, 0))

    solver.add(And(addsum(degree_prod_num) <= maxDeg, addsum(degree_prod_den) <= maxDeg))

    # Una misma variable no puede usarse en 2 variables intermedias, o en variable y producto. La suma de veces que es utilizada es <= 1. Se puede reformular con not de ors
    for var in range(max_intermediate): # OK
        uses = []

        for next in range(var + 1, max_intermediate):
            uses.append(If(Or(var_uses_previous_num[next][var], var_uses_previous_den[next][var]), 1, 0))

        uses.append(If(product_uses_var_in_num[var], 1, 0))
        uses.append(If(product_uses_var_in_den[var], 1, 0))

        solver.add(addsum(uses) <= 1)

    ###### ORDEN VARIABLES ######

    # Primero aparezcan las variables de la forma n/n-1, luego las de n-1/n y luego las vacías
    for var in range(max_intermediate - 1): # OK
        solver.add(degree_num_variables[var] >= degree_num_variables[var + 1])
        solver.add(Implies(degree_num_variables[var] == degree_num_variables[var + 1], degree_den_variables[var] >= degree_den_variables[var + 1]))

    # Primero las variables que utilicen otras variables previouses y luego las que no
    # Si una varibale utiliza una variable previous, implica que o la siguiente tiene grado distinto en numerador, según el orden establecido antes
    # o bien, si tiene el mismo grado en numerador, esa variable también utiliza una variable previous porque primero se tienen que crear las variables simples y luego las compuestas
    # Otra forma, mirarlo con si el grado es != del número de variables originales que utiliza implica que está utilizando una variable previous
    for var in range(max_intermediate - 1):
        depends_of_previous_variable = []
        next_var_depends_of_me = []

        for previous_to_var in range(var):
            depends_of_previous_variable.append(If(Or(var_uses_previous_num[var][previous_to_var], var_uses_previous_den[var][previous_to_var]), 1, 0))

        for previous_to_sig in range(var + 1):
            next_var_depends_of_me.append(If(Or(var_uses_previous_num[var + 1][previous_to_sig], var_uses_previous_den[var + 1][previous_to_sig]), 1, 0))
        
        solver.add(Implies(addsum(depends_of_previous_variable) > 0, Or(degree_num_variables[var] != degree_num_variables[var + 1], addsum(next_var_depends_of_me) > 0)))

        product_uses_var = Or(product_uses_var_in_num[var], product_uses_var_in_den[var])
        product_uses_sig_var = Or(product_uses_var_in_num[var + 1], product_uses_var_in_den[var + 1])
        var_sig_empty = And(degree_num_variables[var + 1] == 0, degree_den_variables[var + 1] == 0)

        # Si var es utilizada por el producto, var + 1 tambien
        solver.add(Implies(product_uses_var, Or(product_uses_sig_var, var_sig_empty))) #REVISAR NO SÉ SI PUEDE DAR UNSAT

    # Dentro de las variables que utilizan otras previouses, deben aparecer primero aquellas que tengan un número de variables iniciales mayor
    for var in range(max_intermediate - 1): # OK
        solver.add(num_original_variables_var_num[var] >= num_original_variables_var_num[var + 1])
        solver.add(Implies(num_original_variables_var_num[var] == num_original_variables_var_num[var + 1], num_original_variables_var_den[var] >= num_original_variables_var_den[var + 1]))

    # Dentro de las que se usan en intermedias, que se utilicen en orden
    for var in range(max_intermediate): # OK
        for previous_used in range(var):
            for previous in range(previous_used):
                for next_to_var in range(var + 1, max_intermediate):
                    var_uses_previous_used = Or(var_uses_previous_num[var][previous_used], var_uses_previous_den[var][previous_used])
                    next_uses_previous_to_used = Or(var_uses_previous_num[next_to_var][previous], var_uses_previous_den[next_to_var][previous])

                    # Si una variable utiliza una previous, las siguientes variables no pueden utilizar las variables previouses a la usada
                    solver.add(Implies(var_uses_previous_used, Not(next_uses_previous_to_used)))

    # Las variables llenas al principio y medio llenas después


    # Minimizar el número de variables --> Orden lexicografico
    for var in range(max_intermediate): # OK
        solver.add_soft(And(degree_num_variables[var] == 0, degree_den_variables[var] == 0), 1, "min_vars")

    # Minimizar grado final --> Maximizar las variables que si tienen elementos en numerador, tengan también en denominador y viceversa 
    # --> Ralentiza mucho pero reduce bastante el número de VI finales tras la suma #REVISAR si lo quito puede llegar a no dar solucion
    for var in range(max_intermediate): 
        solver.add_soft(And(degree_num_variables[var] > 0, degree_den_variables[var] > 0), 1, "min_grado_final")

    # Minimizar número de variables usadas en denominador, es decir, minimizar variables de la forma (n-1)/n --> Ralentiza algo menos que la previous pero tmb
    for var in range(max_intermediate):
        solver.add_soft(degree_num_variables[var] == maxDeg, 1, "min_vars_den")
    
    # INCREMENTALIDAD

    # Cota optimista con una aproximación mía
    optimistic_intermediate = max(degree_num, degree_den) // maxDeg
    print(f"Max intermediate realistic: {max_intermediate} ")
    print(f"Max intermediate optimistic: {optimistic_intermediate} ")

    for var in range(max_intermediate - 1, optimistic_intermediate - 1, -1):
        solver.push()
        print("push")
        solver.add(degree_num_variables[var] == 0)
        solver.add(degree_den_variables[var] == 0)

    # solver.push()
    # solver.add(degree_num_variables[max_intermediate - 1] == 0)
    # solver.add(degree_den_variables[max_intermediate - 1] == 0)

    print(f"Grado numerador: {degree_num}. Grado denominador: {degree_den}")
    if solver.check() == sat:
        m = solver.model()
        print("Variables intermedias formadas:")

        print_solucion(id, m, max_intermediate, num_original_variables_var_num, num_original_variables_var_den, variables_covered_num, variables_covered_den, 
        var_uses_previous_num, var_uses_previous_den, product_uses_var_in_num, product_uses_var_in_den, degree_num_variables, degree_den_variables, product_uses_initials_in_num,
        product_uses_initials_in_den, degree_prod_num, degree_prod_den)

    else:
        print(f"No existe solución con " + str(optimistic_intermediate) + " variables intermedias")

        for var in range(optimistic_intermediate + 1, max_intermediate + 1):
            solver.pop()
            if solver.check() == sat:
                m = solver.model()

                print("Existe solución con " + str(var) + " variables intermedias.")
                print_solucion(id, m, max_intermediate, num_original_variables_var_num, num_original_variables_var_den, variables_covered_num, variables_covered_den, 
                var_uses_previous_num, var_uses_previous_den, product_uses_var_in_num, product_uses_var_in_den, degree_num_variables, degree_den_variables, product_uses_initials_in_num,
                product_uses_initials_in_den, degree_prod_num, degree_prod_den)
            else: 
                print("No hay solución con " + str(var) + " variables intermedias.")
                with open("prod.json", "w") as fout:
                    json.dump({}, fout)
    
# reducir_grado_producto(2, 3, 2, 0)