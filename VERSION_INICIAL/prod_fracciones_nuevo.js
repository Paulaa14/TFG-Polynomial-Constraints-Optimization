const z3s = require("z3-solver")
const init = z3s.init;

async function reducir_grado_producto(maxDeg, degree_num, degree_den) { // max_intermedias 
  let { Context } = await init();
  let z3 = Context('main');

  function addsum(arr) {
    if (arr.length === 0) return z3.Int.val(0);
    let asum = arr[0];
    for (let i = 1; i < arr.length; i++) {
        asum = asum.add(arr[i]);
    }
    return asum;
  }

  const solver = new z3.Optimize();

  max_intermedias = (Math.floor(Math.max(degree_num, degree_den) / maxDeg)) + 1; // DEMOSTRAR

  // DECLARACIÓN DE VARIABLES

  let num_variables_originales_var_num = [];
  let num_variables_originales_var_den = [];

  // num_var_i : número de variables originales de numerador que va a agrupar vi_i
  // den_var_i : número de variables originales de denominador que va a agrupar vi_i
  for (let variable = 0; variable < max_intermedias; variable++) {
    let num_var = z3.Int.const(`num_var_${variable}`);
    num_variables_originales_var_num.push(num_var);

    let den_var = z3.Int.const(`den_var_${variable}`);
    num_variables_originales_var_den.push(den_var);
  }

  let usa_var_anterior_num = [];
  let usa_var_anterior_den = [];

  // var_i_usan_j : la variable vi_i utiliza o no vi_j en el numerador para formarse, con j perteneciente a [0, i) 
  // var_i_usad_j : la variable vi_i utiliza o no vi_j en el denominador para formarse, con j perteneciente a [0, i) 
  for (let variable = 0; variable < max_intermedias; variable++) {
    let cuales_usa_n = [];
    let cuales_usa_d = [];

    for (let anterior = 0; anterior < variable; anterior++) {
        let v_n = z3.Bool.const(`var_${variable}_usan_${anterior}`);
        cuales_usa_n.push(v_n);

        let v_d = z3.Bool.const(`var_${variable}_usad_${anterior}`);
        cuales_usa_d.push(v_d);
    }

    usa_var_anterior_num.push(cuales_usa_n);
    usa_var_anterior_den.push(cuales_usa_d);
  }

  let producto_usa_var_en_num = [];
  let producto_usa_var_en_den = [];

  // prodn_var_i : el producto final contiene a la variable vi_i en el numerador
  // prodd_var_i : el producto final contiene a la variable vi_i en el denominador
  for (let variable = 0; variable < max_intermedias; variable++) {
    let p_n = z3.Bool.const(`prodn_var_${variable}`);
    producto_usa_var_en_num.push(p_n);

    let p_d = z3.Bool.const(`prodd_var_${variable}`);
    producto_usa_var_en_den.push(p_d);
  }

  // inic_prod_num : número de variables originales de numerador, que no están contenidas en ninguna vi, que agrupa el producto final
  let producto_usa_iniciales_en_num = z3.Int.const(`inic_prod_num`);

  // inic_prod_den : número de variables originales de denominador, que no están contenidas en ninguna vi, que agrupa el producto final
  let producto_usa_iniciales_en_den = z3.Int.const(`inic_prod_den`);

  // CONSTRAINTS

  for (let variable = 0; variable < max_intermedias; variable++) {
    solver.add(z3.And(num_variables_originales_var_num[variable].gt(0), num_variables_originales_var_num[variable].le(maxDeg)));
    solver.add(z3.And(num_variables_originales_var_den[variable].gt(0), num_variables_originales_var_den[variable].le(maxDeg)));
  }

  let cuantas_variables_cubre_num = [];
  let cuantas_variables_cubre_den = [];

  for (let variable = 0; variable < max_intermedias; variable++) {
    let cuantas_n = [];
    let cuantas_d = [];

    cuantas_n.push(num_variables_originales_var_num[variable]);
    cuantas_d.push(num_variables_originales_var_den[variable]);

    for (let anterior = 0; anterior < variable; anterior++) {
        cuantas_n.push(z3.If(z3.Or(usa_var_anterior_num[variable][anterior], usa_var_anterior_den[variable][anterior]), cuantas_variables_cubre_num[anterior], 0));
        cuantas_d.push(z3.If(z3.Or(usa_var_anterior_num[variable][anterior], usa_var_anterior_den[variable][anterior]), cuantas_variables_cubre_den[anterior], 0));
    }

    cuantas_variables_cubre_num.push(addsum(cuantas_n));
    cuantas_variables_cubre_den.push(addsum(cuantas_d));
  }

  let grado_num_variables = [];
  let grado_den_variables = [];

  for (let variable = 0; variable < max_intermedias; variable++) {
    let grado_num = [];
    let grado_den = [];

    grado_num.push(num_variables_originales_var_num[variable]);
    grado_den.push(num_variables_originales_var_den[variable]);

    for (let anterior = 0; anterior < variable; anterior++) {
        grado_num.push(z3.If(usa_var_anterior_num[variable][anterior], 1, 0));
        grado_den.push(z3.If(usa_var_anterior_den[variable][anterior], 1, 0));
    }

    solver.add(z3.And(addsum(grado_num).le(maxDeg), addsum(grado_den).le(maxDeg)));

    grado_num_variables.push(addsum(grado_num));
    grado_den_variables.push(addsum(grado_den));
  }

  for (let variable = 0; variable < max_intermedias; variable++) {
    let n_num = z3.And(grado_num_variables[variable].eq(maxDeg), z3.Or(grado_den_variables[variable].eq(0), grado_den_variables[variable].eq(maxDeg - 1)));
    let n_den = z3.And(z3.Or(grado_num_variables[variable].eq(0), grado_num_variables[variable].eq(maxDeg - 1)), grado_den_variables[variable].eq(maxDeg));
    let zero = z3.And(grado_num_variables[variable].eq(0), grado_den_variables[variable].eq(0));

    solver.add(z3.Or(n_num, z3.Or(n_den, zero)));
  }

  for (let variable = 0; variable < max_intermedias; variable++) {
    for (let anterior = 0; anterior < variable; anterior++) {
        solver.add(z3.Implies(grado_num_variables[anterior].eq(maxDeg), z3.Not(usa_var_anterior_den[variable][anterior])));
        solver.add(z3.Implies(grado_den_variables[anterior].eq(maxDeg), z3.Not(usa_var_anterior_num[variable][anterior])));
        solver.add(z3.Implies(z3.And(grado_num_variables[anterior].eq(0), grado_den_variables[anterior].eq(0)), z3.And(z3.Not(usa_var_anterior_num[variable][anterior]), z3.Not(usa_var_anterior_den[variable][anterior]))));
    }
  }

  solver.add(z3.And(producto_usa_iniciales_en_num.ge(0), producto_usa_iniciales_en_num.le(maxDeg)));
  solver.add(z3.And(producto_usa_iniciales_en_num.ge(0), producto_usa_iniciales_en_num.le(maxDeg)));

  for (let variable = 0; variable < max_intermedias; variable++) {
    solver.add(z3.Or(z3.Not(producto_usa_var_en_num[variable]), z3.Not(producto_usa_var_en_den[variable])));
  }

  let vars_inic_num = [];
  let vars_inic_den = [];

  for (let variable = 0; variable < max_intermedias; variable++) {
    vars_inic_num.push(z3.If(z3.Or(producto_usa_var_en_num[variable], producto_usa_var_en_den[variable]), cuantas_variables_cubre_num[variable], 0));
    vars_inic_den.push(z3.If(z3.Or(producto_usa_var_en_num[variable], producto_usa_var_en_den[variable]), cuantas_variables_cubre_den[variable], 0));
  }

    // ????????????
  let sum1 = addsum(vars_inic_num) + producto_usa_iniciales_en_num;
  let sum2 = addsum(vars_inic_den) + producto_usa_iniciales_en_den;
  solver.add(z3.And(sum1 == degree_num, sum2 == degree_den));

  for (let variable = 0; variable < max_intermedias; variable++) {
    solver.add(z3.Implies(grado_num_variables[variable].eq(maxDeg), z3.Not(producto_usa_var_en_den[variable])));
    solver.add(z3.Implies(grado_den_variables[variable].eq(maxDeg), z3.Not(producto_usa_var_en_num[variable])));
    solver.add(z3.Implies(z3.And(grado_num_variables[variable].eq(0), grado_den_variables[variable].eq(0)), z3.And(z3.Not(producto_usa_var_en_num[variable]), z3.Not(producto_usa_var_en_den[variable]))));
  }

  let grado_prod_n = [];
  let grado_prod_d = [];

  grado_prod_n.push(producto_usa_iniciales_en_num);
  grado_prod_d.push(producto_usa_iniciales_en_den);

  for (let variable = 0; variable < max_intermedias; variable++) {
    grado_prod_n.push(z3.If(producto_usa_var_en_num[variable], 1, 0));
    grado_prod_d.push(z3.If(producto_usa_var_en_den[variable], 1, 0));
  }

  solver.add(z3.And(addsum(grado_prod_n).le(maxDeg), addsum(grado_prod_d).le(maxDeg)));

  for (let variable = 0; variable < max_intermedias; variable++) {
    let usos = [];

    for (let siguiente = variable + 1; siguiente < max_intermedias; siguiente++) {
        usos.push(z3.If(z3.Or(usa_var_anterior_num[siguiente][variable], usa_var_anterior_den[siguiente][variable]), 1, 0));
    }

    usos.push(z3.If(z3.Or(producto_usa_var_en_num[variable], producto_usa_var_en_den[variable]), 1, 0));

    solver.add((addsum(usos).le(1)));
  }

  // ORDEN VARIABLES
  for (let variable = 0; variable < max_intermedias - 1; variable++) {
    solver.add(grado_num_variables[variable].ge(grado_num_variables[variable + 1]));
  }

  for (let variable = 0; variable < max_intermedias - 1; variable++) {
    let depende_de_alguna_var = [];
    siguiente_var_depende = [];

    for (let anterior_a_var = 0; anterior_a_var < variable; anterior_a_var++) {
        depende_de_alguna_var.push(z3.If(z3.Or(usa_var_anterior_num[variable][anterior_a_var], usa_var_anterior_den[variable][anterior_a_var]), 1, 0));
    }

    for (let anterior_a_sig = 0; anterior_a_sig < variable + 1; anterior_a_sig++) {
        siguiente_var_depende.push(z3.If(z3.Or(usa_var_anterior_num[variable + 1][anterior_a_sig], usa_var_anterior_den[variable + 1][anterior_a_sig]), 1, 0));
    }

    solver.add(z3.Implies(addsum(depende_de_alguna_var).gt(0), z3.Or(grado_num_variables[variable] != grado_num_variables[variable + 1], addsum(siguiente_var_depende).gt(0))));
  }

  for (let variable = 0; variable < max_intermedias - 1; variable++) {
    solver.add(num_variables_originales_var_num[variable].ge(num_variables_originales_var_num[variable + 1]));
    solver.add(z3.Implies(num_variables_originales_var_num[variable].eq(num_variables_originales_var_num[variable + 1]), num_variables_originales_var_den[variable].ge(num_variables_originales_var_den[variable + 1])));
  }

  for (let variable = 0; variable < max_intermedias; variable++) {
    solver.addSoft(z3.And(grado_num_variables[variable].eq(0), grado_den_variables[variable].eq(0)), 1, "min_vars");
  }

  for (let variable = 0; variable < max_intermedias; variable++) {
    solver.addSoft(z3.And(grado_num_variables[variable].gt(0), grado_den_variables[variable].gt(0)), 1, "min_grado_final");
  }

  let result = await solver.check();
  console.log(`Grado numerador: ${degree_num}. Grado denominador: ${degree_den}`);

  if (result == 'sat') {
    let model = solver.model();

    console.log("\nVariables intermedias formadas: ");

    const dependencias = [];

    for (let variable = 0; variable < max_intermedias; variable++) {
      const num = model.eval(num_variables_originales_var_num[variable]);
      const den = model.eval(num_variables_originales_var_den[variable]);
      const cubre_num = model.eval(cuantas_variables_cubre_num[variable]);
      const cubre_den = model.eval(cuantas_variables_cubre_den[variable]);

      const deps_num = [];
      const deps_den = [];

      for (let anterior = 0; anterior < variable; anterior++) {
        const val_num = model.eval(usa_var_anterior_num[variable][anterior]);
        const val_den = model.eval(usa_var_anterior_den[variable][anterior]);

        if (val_num == "true") deps_num.push(`VI_${anterior}`);
        if (val_den == "true") deps_den.push(`VI_${anterior}`);
      }

      let dep_str = "";

      if (deps_num.length > 0 || deps_den.length > 0) {
        dep_str += " (";
        if (deps_num.length > 0) {
          dep_str += `num depende de: ${deps_num.join(", ")}`;
        }
        if (deps_den.length > 0) {
          if (deps_num.length > 0) dep_str += "; ";
          dep_str += `den depende de: ${deps_den.join(", ")}`;
        }
        dep_str += ")";
      }

      console.log(
        `VI_${variable}: num = ${num}, den = ${den}, cubre ${cubre_num} en num y ${cubre_den} en den${dep_str}`
      );

      dependencias[`VI_${variable}`] = { num: deps_num, den: deps_den };
    }

    const usadas_num = [];
    const usadas_den = [];

    for (let variable = 0; variable < max_intermedias; variable++) {
      const usa_num = model.eval(producto_usa_var_en_num[variable]);
      const usa_den = model.eval(producto_usa_var_en_den[variable]);

      if (usa_num == "true") {
        usadas_num.push(`VI_${variable}`);
      }
      if (usa_den == "true") {
        usadas_den.push(`VI_${variable}`);
      }
    }

    const inic_num = model.eval(producto_usa_iniciales_en_num);
    const inic_den = model.eval(producto_usa_iniciales_en_den);

    const producto_str_num = usadas_num.length > 0 ? usadas_num.join(" * ") : "1";
    const producto_str_den = usadas_den.length > 0 ? usadas_den.join(" * ") : "1";

    console.log(`\nProducto final: (${producto_str_num}) / (${producto_str_den}). Usa ${inic_num} iniciales en numerador y ${inic_den} iniciales en denominador`);

    // JSON de salida

    const vi_detalles = {};

    for (let variable = 0; variable < max_intermedias; variable++) {
      const vi_name = `VI_${variable}`;
      const gr_num = parseInt(model.eval(grado_num_variables[variable]));
      const gr_den = parseInt(model.eval(grado_den_variables[variable]));

      if (gr_num > 0 || gr_den > 0) {
        vi_detalles[vi_name] = {
          formada_por: {
            num_originales: parseInt(model.eval(num_variables_originales_var_num[variable])),
            den_originales: parseInt(model.eval(num_variables_originales_var_den[variable])),
            num_depende_de: dependencias[vi_name]["num"],
            den_depende_de: dependencias[vi_name]["den"]
          },
          grado_num: gr_num,
          grado_den: gr_den,
          grado_total: parseInt(Math.max(gr_num, gr_den))
        };
      }
    }

    const inic_num_val = model.eval(producto_usa_iniciales_en_num);
    const inic_den_val = model.eval(producto_usa_iniciales_en_den);

    const componentes_detalle = (lista_vars) => {
      const comp = [];
      for (const v of lista_vars) {
        if (vi_detalles[v]) {
          const vi_info = vi_detalles[v];
          comp.push({
            nombre: v,
            formada_por: vi_info["formada_por"],
            grado_num: vi_info["grado_num"],
            grado_den: vi_info["grado_den"],
            grado_total: vi_info["grado_total"]
          });
        }
      }
      return comp;
    };

    const numerador_detalle = {
      componentes: componentes_detalle(usadas_num),
      variables_originales: inic_num_val,
      grado_total: parseInt(model.eval(addsum(grado_prod_n))),
    };

    const denominador_detalle = {
      componentes: componentes_detalle(usadas_den),
      variables_originales: inic_den_val,
      grado_total: parseInt(model.eval(addsum(grado_prod_d))),
    };

    const output_data = {
      op: "frac",
      producto: {
        numerador: numerador_detalle,
        denominador: denominador_detalle,
      },
      variables_intermedias: vi_detalles,
      grado_numerador_total: numerador_detalle["grado_total"],
      grado_denominador_total: denominador_detalle["grado_total"]
    };

    console.log(output_data);

    // Guardar JSON (en Node.js)
    const fs = require("fs");
    fs.writeFileSync("prod.json", JSON.stringify(output_data, null, 4));

    console.log(`\nResultado exportado en prod.json`);
  }
  else {
    console.log(`\n❌ No se ha encontrado una solución.`);
  }
}

reducir_grado_producto(3, 22, 20);