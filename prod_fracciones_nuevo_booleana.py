#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Simetrías de variables
# Otra opción: quién me usa: booleana de si es usada por intermedia/final o no, y quien la usa. Si una tiene a falso los 2, las siguientes también
# Primero intermedias usadas por otras intermedias y luego las usadas por el final
# Las variables llenas al principio y medio llenas después
# Garantizar que no se pierden soluciones, cualquier cosa que quita repetidos, no elimina soluciones, solo evita que la misma solucion tenga varias representaciones --> Demostrar
# Ir apuntando todo
# Determinar máximo de max_intermediate como: máximo grado de la fraccion ((max(num, den)) / maxDeg) + 1 --> Demostrar

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
    
# Meter variables que representan la fracción, cuántas variables se cogen en el numerador, y cuántas en el denominador

##### PARAMETROS #####
# Usaremos variables intermedias vi_0, ... vi_{max_intermediate-1}
# max_intermediate = 5

def reducir_grado_producto(maxDeg, degree_num, degree_den): # max_intermediate

    ###### DECLARACIÓN DE VARIABLES ######
    solver = Optimize()

    max_intermediate = (max(degree_num, degree_den) // maxDeg) + 1 # DEMOSTRAR

    # Cada variable, cuántas variables de las originales tiene del numerador, y cuántas del denominador. Cada variables es un nivel.
    # Las variables del numerador se colocarán en el numerador de la nueva variable y las del denominador en el denominador pero para el recuento final, es necesario saber cuántas eran originalmente del numerador
    num_original_variables_var_num = []
    num_original_variables_var_den = []

    # num_var_i : número de variables originales de numerador que va a agrupar vi_i
    # den_var_i : número de variables originales de denominador que va a agrupar vi_i
    for var in range(max_intermediate):
        num_original_variables_var_num.append(Int("num_var_" + str(var)))
        num_original_variables_var_den.append(Int("den_var_" + str(var)))

    # Cada una de las variables intermedias, utiliza alguna de las variables intermedias anteriores o no. 
    # La primera lógicamente no va a utilizar ninguna variable anterior, con el bucle interior ya se cubre ese caso
    var_uses_previous_num = []
    var_uses_previous_den = []

    # var_i_usan_j : la variable vi_i utiliza o no vi_j en el numerador para formarse, con j perteneciente a [0, i) 
    # var_i_usad_j : la variable vi_i utiliza o no vi_j en el denominador para formarse, con j perteneciente a [0, i) 
    for var in range(max_intermediate): # Se podría poner como rango 1 - max_intermediate para ahorrar una vuelta
        which_uses_num = []
        which_uses_den = []

        for previous in range(var):
            which_uses_num.append(Bool("var_" + str(var) + "_usesn_" + str(previous)))
            which_uses_den.append(Bool("var_" + str(var) + "_usesd_" + str(previous)))

        var_uses_previous_num.append(which_uses_num)
        var_uses_previous_den.append(which_uses_den)

    # El producto final, qué variables intermedias utiliza
    product_uses_var_in_num = []
    product_uses_var_in_den = []

    # prodn_var_i : el producto final contiene a la variable vi_i en el numerador
    # prodd_var_i : el producto final contiene a la variable vi_i en el denominador
    for var in range(max_intermediate):
        product_uses_var_in_num.append(Bool("prod_uses_n_var_" + str(var)))
        product_uses_var_in_den.append(Bool("prod_uses_d_var_" + str(var)))

    # inic_prod_num : número de variables originales de numerador, que no están contenidas en ninguna vi, que agrupa el producto final
    product_uses_initials_in_num = Int("init_prod_num")

    # inic_prod_den : número de variables originales de denominador, que no están contenidas en ninguna vi, que agrupa el producto final
    product_uses_initials_in_den = Int("init_prod_den")

    ###### CONSTRAINTS ######

    for var in range(max_intermediate):
        solver.add(And(num_original_variables_var_num[var] >= 0, num_original_variables_var_num[var] <= maxDeg))
        solver.add(And(num_original_variables_var_den[var] >= 0, num_original_variables_var_den[var] <= maxDeg))

    # Para cada variable, cuántas variables originales realmente cubre teniendo en cuenta las originales que tiene de num_variables_originales_var + las que tiene cada variable previous que contiene
    # Es decir, de las originales del numerador, cuántas contiene? Idem con denominador
    variables_covered_num = []
    variables_covered_den = []

    for var in range(max_intermediate):
        covered_num = []
        covered_den = []
        covered_num.append(num_original_variables_var_num[var])
        covered_den.append(num_original_variables_var_den[var])

        # Si utiliza una variable previous ahora cubre todas las que tuviera ella también + las suyas
        for previous in range(var):
            covered_num.append(If(Or(var_uses_previous_num[var][previous], var_uses_previous_den[var][previous]), variables_covered_num[previous], 0))
            covered_den.append(If(Or(var_uses_previous_num[var][previous], var_uses_previous_den[var][previous]), variables_covered_den[previous], 0))

        variables_covered_num.append(addsum(covered_num))
        variables_covered_den.append(addsum(covered_den))

    # Grado de cada variable: el máximo entre el grado del numerador y del denominador
    degree_num_variables = []
    degree_den_variables = []

    for var in range(max_intermediate):
        degree_num = []
        degree_den = []
        degree_num.append(num_original_variables_var_num[var])
        degree_den.append(num_original_variables_var_den[var])

        for previous in range(var):
            # Si utiliza una variable previous, aporta grado 1
            degree_num.append(If(var_uses_previous_num[var][previous], 1, 0))
            degree_den.append(If(var_uses_previous_den[var][previous], 1, 0))

        solver.add(And(addsum(degree_num) <= maxDeg, addsum(degree_den) <= maxDeg))
        
        degree_num_variables.append(addsum(degree_num))
        degree_den_variables.append(addsum(degree_den))

    # Solo puede ocurrir o que el grado de la variable sea n/n-1, n-1/n o que esté vacía tanto en numerador como denominador
    for var in range(max_intermediate):
        n_num = And(degree_num_variables[var] == maxDeg, Or(degree_den_variables[var] == 0, degree_den_variables[var] == maxDeg - 1))
        n_den = And(Or(degree_num_variables[var] == 0, degree_num_variables[var] == maxDeg - 1), degree_den_variables[var] == maxDeg)
        zero = And(degree_num_variables[var] == 0, degree_den_variables[var] == 0)

        solver.add(Or(n_num, Or(n_den, zero)))

    # Si la variable es de la forma n/(n - 1) se utilizará en el numerador, aportando grado 1 y si tiene la forma (n - 1)/n se utilizará en el denominador
    for var in range(max_intermediate):
        for previous in range(var):
            # Si tiene n en el numerador, no puede usarse en el denominador de ninguna variable y viceversa
            solver.add(Implies(degree_num_variables[previous] == maxDeg, Not(var_uses_previous_den[var][previous])))
            solver.add(Implies(degree_den_variables[previous] == maxDeg, Not(var_uses_previous_num[var][previous])))
            solver.add(Implies(And(degree_num_variables[previous] == 0, degree_den_variables[previous] == 0), And(Not(var_uses_previous_num[var][previous]), Not(var_uses_previous_den[var][previous]))))

    solver.add(And(product_uses_initials_in_num >= 0, product_uses_initials_in_num <= maxDeg))
    solver.add(And(product_uses_initials_in_den >= 0, product_uses_initials_in_den <= maxDeg))

    # No puede usarse la misma variable para numerador y denominador
    for var in range(max_intermediate):
        solver.add(Or(Not(product_uses_var_in_num[var]), Not(product_uses_var_in_den[var])))

    # Contar que se cubren todas las variables que había al inicio
    vars_inic_num = []
    vars_inic_den = []

    # Si utiliza una variable, ya sea en numerador o denominador, ahora cubre las variables que ella cubriera
    for var in range(max_intermediate):
        vars_inic_num.append(If(Or(product_uses_var_in_num[var], product_uses_var_in_den[var]), variables_covered_num[var], 0))
        vars_inic_den.append(If(Or(product_uses_var_in_num[var], product_uses_var_in_den[var]), variables_covered_den[var], 0))

    solver.add(And(addsum(vars_inic_num) + product_uses_initials_in_num == degree_num, addsum(vars_inic_den) + product_uses_initials_in_den == degree_den))

    # Si la variable es de la forma n/(n - 1) se utilizará en el numerador, aportando grado 1 y si tiene la forma (n - 1)/n se utilizará en el denominador
    for var in range(max_intermediate):
        # Si tiene n en el numerador, no puede usarse en el denominador de ninguna variable y viceversa
        solver.add(Implies(degree_num_variables[var] == maxDeg, Not(product_uses_var_in_den[var])))
        solver.add(Implies(degree_den_variables[var] == maxDeg, Not(product_uses_var_in_num[var])))
        solver.add(Implies(And(degree_num_variables[var] == 0, degree_den_variables[var] == 0), And(Not(product_uses_var_in_num[var]), Not(product_uses_var_in_den[var]))))

    # Comprobar que no te pasas de grado en el producto final
    degree_prod_num = []
    degree_prod_den = []

    degree_prod_num.append(product_uses_initials_in_num)
    degree_prod_den.append(product_uses_initials_in_den)

    for var in range(max_intermediate):
        degree_prod_num.append(If(product_uses_var_in_num[var], 1, 0))
        degree_prod_den.append(If(product_uses_var_in_den[var], 1, 0))

    solver.add(And(addsum(degree_prod_num) <= maxDeg, addsum(degree_prod_den) <= maxDeg))

    # Una misma variable no puede usarse en 2 variables intermedias, o en variable y producto. La suma de veces que es utilizada es <= 1. Se puede reformular con not de ors
    for var in range(max_intermediate):
        uses = []

        for siguiente in range(var + 1, max_intermediate):
            uses.append(If(Or(var_uses_previous_num[siguiente][var], var_uses_previous_den[siguiente][var]), 1, 0))

        uses.append(If(Or(product_uses_var_in_num[var], product_uses_var_in_den[var]), 1, 0))

        solver.add(addsum(uses) <= 1)

    ###### ORDEN VARIABLES ######

    # Primero aparezcan las variables de la forma n/n-1, luego las de n-1/n y luego las vacías
    for var in range(max_intermediate - 1):
        solver.add(degree_num_variables[var] >= degree_num_variables[var + 1])

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

    # Dentro de las variables que utilizan otras previouses, deben aparecer primero aquellas que tengan un número de variables iniciales mayor
    for var in range(max_intermediate - 1):
        solver.add(num_original_variables_var_num[var] >= num_original_variables_var_num[var + 1])
        solver.add(Implies(num_original_variables_var_num[var] == num_original_variables_var_num[var + 1], num_original_variables_var_den[var] >= num_original_variables_var_den[var + 1]))

    # Minimizar el número de variables
    for var in range(max_intermediate):
        solver.add_soft(And(degree_num_variables[var] == 0, degree_den_variables[var] == 0), 1, "min_vars")

    # Minimizar grado final --> Maximizar las variables que si tienen elementos en numerador, tengan también en denominador y viceversa
    for var in range(max_intermediate):
        solver.add_soft(And(degree_num_variables[var] > 0, degree_den_variables[var] > 0), 1, "min_grado_final")

    print(f"Grado numerador: {degree_num}. Grado denominador: {degree_den}")
    if solver.check() == sat:
        m = solver.model()
        print("Variables intermedias formadas:")

        dependencias = {}

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
                    deps_num.append(f"VI_{previous}")
                if is_true(val_den):
                    deps_den.append(f"VI_{previous}")

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

            dependencias[f"VI_{var}"] = {"num": deps_num, "den": deps_den}

        # Identificar variables usadas en el producto final
        usadas_num = []
        usadas_den = []

        for var in range(max_intermediate):
            usa_num = m.eval(product_uses_var_in_num[var], model_completion=True)
            usa_den = m.eval(product_uses_var_in_den[var], model_completion=True)
            if is_true(usa_num):
                usadas_num.append(f"VI_{var}")
            elif is_true(usa_den):
                usadas_den.append(f"VI_{var}")

        inic_num = m.eval(product_uses_initials_in_num, model_completion=True).as_long()
        inic_den = m.eval(product_uses_initials_in_den, model_completion=True).as_long()

        # Mostrar producto final estimado
        producto_str_num = " * ".join(usadas_num) if usadas_num else "1"
        producto_str_den = " * ".join(usadas_den) if usadas_den else "1"

        print(f"\nProducto final: ({producto_str_num}) / ({producto_str_den}). Usa {inic_num} iniciales en numerador y {inic_den} iniciales en denominador")

        # --- Generar JSON de salida ---

        # Construir detalles de cada VI
        vi_detalles = {}
        for var in range(max_intermediate):
            vi_name = f"VI_{var}"
            gr_num = int(m.eval(degree_num_variables[var], model_completion=True).as_long())
            gr_den = int(m.eval(degree_den_variables[var], model_completion=True).as_long())

            # Solo meter las VI que se utilizan, como se está minimizando, son solo las que son != 0 tanto num como den
            if gr_num > 0 or gr_den > 0:
                vi_detalles[vi_name] = {
                    "formada_por": {
                        "num_originales": int(m.eval(num_original_variables_var_num[var], model_completion=True).as_long()),
                        "den_originales": int(m.eval(num_original_variables_var_den[var], model_completion=True).as_long()),
                        "num_depende_de": dependencias[vi_name]["num"],
                        "den_depende_de": dependencias[vi_name]["den"]
                    },
                    "degree_num": gr_num,
                    "degree_den": gr_den,
                    "grado_total": int(max(gr_num, gr_den))
                }

        inic_num_val = m.eval(product_uses_initials_in_num, model_completion=True).as_long()
        inic_den_val = m.eval(product_uses_initials_in_den, model_completion=True).as_long()

        def componentes_detalle(lista_vars):
            comp = []
            for v in lista_vars:
                if v in vi_detalles:
                    vi_info = vi_detalles[v]
                    comp.append({
                        "nombre": v,
                        "formada_por": vi_info["formada_por"],
                        "degree_num": vi_info["degree_num"],
                        "degree_den": vi_info["degree_den"],
                        "grado_total": vi_info["grado_total"]
                    })
            return comp

        numerador_detalle = {
            "componentes": componentes_detalle(usadas_num),
            "variables_originales": inic_num_val,
            "grado_total": int(m.eval(addsum(degree_prod_num), model_completion=True).as_long())
        }

        denominador_detalle = {
            "componentes": componentes_detalle(usadas_den),
            "variables_originales": inic_den_val, 
            "grado_total": int(m.eval(addsum(degree_prod_den), model_completion=True).as_long())
        }

        output_data = {
            "op": "frac",
            "producto": {
                "numerador": numerador_detalle,
                "denominador": denominador_detalle
            },
            "variables_intermedias": vi_detalles,
            "degree_numerador_total": numerador_detalle["grado_total"],
            "degree_denominador_total": denominador_detalle["grado_total"]
        }

        print(output_data)

        with open("prod.json", "w") as fout:
            json.dump(output_data, fout, indent=4)

        print(f"\nResultado exportado en {"prod.json"}")



    else:
        print("No hay solución.")
        with open("prod.json", "w") as fout:
            json.dump({}, fout)