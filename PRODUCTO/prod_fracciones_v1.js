const z3s = require("z3-solver")
const init = z3s.init;
const fs = require("fs");
const path = require("path");

async function main() {
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

  const args = process.argv.slice(2);
  if (args.length < 1) {
    console.error('Uso: node script.js <filein>');
    process.exit(1);
  }
  const filein = args[0];

  let data;
  try {
    const raw = fs.readFileSync(path.resolve(filein), 'utf8');
    data = JSON.parse(raw);
  } catch (err) {
    console.error(`Error al leer el archivo ${filein}:`, err.message);
    process.exit(1);
  }

  let productos = data["productos"];
  let maxDeg = data["degree"];
  let num_productos = productos.length;

  let factores_num_signal = [];
  let factores_num_degree = [];
  let factores_den_signal = [];
  let factores_den_degree = [];

  let grados_prod = [];
  let cjto_variables = new Set();

  for (let p = 0; p < num_productos; p++) {
    let exp = productos[p]["expressions"];
    let grado_num = 0;
    let grado_den = 0;

    for (let e = 0; e < exp.length; e++) {
        grado_num += exp[e]["values"][0]["degree"];
        grado_den += exp[e]["values"][1]["degree"];
    }

    grados_prod.push(Math.max(grado_num, grado_den));
  }

  for (let p = 0; p < num_productos; p++) {
    let exp = productos[p]["expressions"];
    let grado = grados_prod[p];

    for (let e = 0; e < exp.length; e++) {
        if (grado > maxDeg) {
            cjto_variables.add(exp[e]["values"][0]["signals"]);
            cjto_variables.add(exp[e]["values"][1]["signals"]);

            factores_num_signal.push(exp[e]["values"][0]["signals"]);
            factores_num_degree.push(1); //exp[e]["values"][0]["degree"]);
            factores_den_signal.push(exp[e]["values"][1]["signals"]);
            factores_den_degree.push(1); // exp[e]["values"][1]["degree"]);
        }
    }
  }

  let num_factores_num = factores_num_signal.length;
  let num_factores_den = factores_den_signal.length;

  cjto_variables = Array.from(cjto_variables);
  cjto_variables.sort((a, b) => String(a).localeCompare(String(b), 'es'));
  
  let num_variables_por_producto = [];
  for (let prod = 0; prod < num_productos; prod++) {
    let counts = [];

    for (let v = 0; v < cjto_variables.length; v++) {
        let c_num = 0;
        let c_den = 0;

        for (let exp = 0; exp < productos[prod]["expressions"].length; exp++) {
            if (productos[prod]["expressions"][exp]["values"][0]["signals"] == cjto_variables[v]) {
                c_num += productos[prod]["expressions"][exp]["values"][0]["degree"];
            }
            if (productos[prod]["expressions"][exp]["values"][1]["signals"] == cjto_variables[v]) {
                c_den += productos[prod]["expressions"][exp]["values"][1]["degree"];
            }
        }

        counts.push(c_num + c_den);
    }

    num_variables_por_producto.push(counts);
  }

  let max_intermedias = 9;


  let ocupacion_huecos_variables_v_num = [];
  let ocupacion_huecos_variables_f_num = [];
  let ocupacion_huecos_variables_den = [];

  // composicion_variables_intermedias
  for (let variable = 0; variable < max_intermedias; variable++) {
    let huecos_var_v_num = [];
    let huecos_var_f_num = [];
    let huecos_var_den = [];

    for (let hueco_num = 0; hueco_num < maxDeg; hueco_num++) {
        let ocupa_v_num = [];
        let ocupa_f_num = [];

        for (let variable_anterior = 0; variable_anterior < variable; variable_anterior++) {
            let varBool = z3.Bool.const(`ocupavn_${variable}_${hueco_num}_${variable_anterior}`);
            ocupa_v_num.push(varBool);
        }

        for (let factor = 0; factor < num_factores_num; factor++) {
            let varBool = z3.Bool.const(`ocupafn_${variable}_${hueco_num}_${factor}`);
            ocupa_f_num.push(varBool);
        }

        huecos_var_v_num.push(ocupa_v_num);
        huecos_var_f_num.push(ocupa_f_num);
    }

    for (let hueco_den = 0; hueco_den < maxDeg; hueco_den++) {
        let ocupa_f_d = [];

        for (let factor = 0; factor < num_factores_den; factor++) {
            let varBool = z3.Bool.const(`ocupafd_${variable}_${hueco_den}_${factor}`);
            ocupa_f_d.push(varBool);
        }

        huecos_var_den.push(ocupa_f_d);
    }

    ocupacion_huecos_variables_v_num.push(huecos_var_v_num);
    ocupacion_huecos_variables_f_num.push(huecos_var_f_num);
    ocupacion_huecos_variables_den.push(huecos_var_den);
  }

  // orden_huecos_variables
  for (let variable = 0; variable < max_intermedias; variable++) {
    for (let hueco_num = 0; hueco_num < maxDeg; hueco_num++) {
        for (let variable_anterior = 0; variable_anterior < variable; variable_anterior++) {
            for (let hueco_sig = hueco_num + 1; hueco_sig < maxDeg; hueco_sig++) {
                for (let vars_anteriores = 0; vars_anteriores < variable_anterior; vars_anteriores++) {
                    solver.add(z3.Implies(ocupacion_huecos_variables_v_num[variable][hueco_num][variable_anterior], z3.Not(ocupacion_huecos_variables_v_num[variable][hueco_sig][vars_anteriores])));
                }
            }
        }

        for (let factor = 0; factor < num_factores_num; factor++) {
            for (let hueco_sig = hueco_num + 1; hueco_sig < maxDeg; hueco_sig++) {
                for (let var_anterior = 0; var_anterior < variable; var_anterior++) {
                    solver.add(z3.Implies(ocupacion_huecos_variables_f_num[variable][hueco_num][factor], z3.Not(ocupacion_huecos_variables_v_num[variable][hueco_sig][var_anterior])));
                }

                for (let factores_anteriores = 0; factores_anteriores < factor; factores_anteriores++) {
                    solver.add(z3.Implies(ocupacion_huecos_variables_f_num[variable][hueco_num][factor], z3.Not(ocupacion_huecos_variables_f_num[variable][hueco_sig][factores_anteriores])));
                }
            }
        }
    }

    for (let hueco_den = 0; hueco_den < maxDeg; hueco_den++) {
        for (let factor = 0; factor < num_factores_den; factor++) {
            for (let hueco_sig = hueco_den + 1; hueco_sig < maxDeg; hueco_sig++) {
                for (let factores_anteriores = 0; factores_anteriores < factor; factores_anteriores++) {
                    solver.add(z3.Implies(ocupacion_huecos_variables_den[variable][hueco_den][factor], z3.Not(ocupacion_huecos_variables_den[variable][hueco_sig][factores_anteriores])));
                }
            }
        }
    }
  }

  // rellenar_huecos_variables_en_orden 
  for (let variable = 0; variable < max_intermedias; variable++) {
    for (let hueco_num = 1; hueco_num < maxDeg; hueco_num++) {
        let suma_actual = [];
        let suma_anterior = [];

        for (let v = 0; v < variable; v++) {
            suma_actual.push(z3.If(ocupacion_huecos_variables_v_num[variable][hueco_num][v], 1, 0));
            suma_anterior.push(z3.If(ocupacion_huecos_variables_v_num[variable][hueco_num - 1][v], 1, 0));
        }

        for (let fact = 0; fact < num_factores_num; fact++) {
            suma_actual.push(z3.If(ocupacion_huecos_variables_f_num[variable][hueco_num][fact], 1, 0));
            suma_anterior.push(z3.If(ocupacion_huecos_variables_f_num[variable][hueco_num - 1][fact], 1, 0));
        }

        solver.add(z3.Implies(addsum(suma_actual).gt(0), addsum(suma_anterior).gt(0)));
    }

    for (let hueco_den = 1; hueco_den < maxDeg; hueco_den++) {
        let suma_actual = [];
        let suma_anterior = [];

        for (let fact = 0; fact < num_factores_den; fact++) {
            suma_actual.push(z3.If(ocupacion_huecos_variables_den[variable][hueco_den][fact], 1, 0));
            suma_anterior.push(z3.If(ocupacion_huecos_variables_den[variable][hueco_den - 1][fact], 1, 0));
        }

        solver.add(z3.Implies(addsum(suma_actual).gt(0), addsum(suma_anterior).gt(0)));
    }
  }

  // restricciones_huecos_v
  for (let variable = 0; variable < max_intermedias; variable++) {
    let cumple_grado_num = [];
    let cumple_grado_den = [];

    for (let hueco_num = 0; hueco_num < maxDeg; hueco_num++) {
        for (let variable_anterior = 0; variable_anterior < variable; variable_anterior++) {
            cumple_grado_num.push(z3.If(ocupacion_huecos_variables_v_num[variable][hueco_num][variable_anterior], 1, 0));
        }

        for (let factor = 0; factor < num_factores_num; factor++) {
            cumple_grado_num.push(z3.If(ocupacion_huecos_variables_f_num[variable][hueco_num][factor], factores_num_degree[factor], 0));
        }
    }

    for (let hueco_den = 0; hueco_den < maxDeg; hueco_den++) {
        for (let factor = 0; factor < num_factores_den; factor++) {
            cumple_grado_den.push(z3.If(ocupacion_huecos_variables_den[variable][hueco_den][factor], factores_den_degree[factor], 0));
        }
    }

    solver.add(addsum(cumple_grado_num).le(maxDeg));
    solver.add(addsum(cumple_grado_den).le(maxDeg));
  }

  // variables_correctas
  for (let variable = 0; variable < max_intermedias; variable++) {
    let activos_primer_hueco = [];
    let activos_segundo_hueco = [];

    if (maxDeg >= 2){
        for (let variable_anterior = 0; variable_anterior < variable; variable_anterior++) {
            activos_primer_hueco.push(z3.If(ocupacion_huecos_variables_v_num[variable][0][variable_anterior], 1, 0));
            activos_segundo_hueco.push(z3.If(ocupacion_huecos_variables_v_num[variable][1][variable_anterior], 1, 0));
        }

        for (let factor = 0; factor < num_factores_num; factor++) {
            activos_primer_hueco.push(z3.If(ocupacion_huecos_variables_f_num[variable][0][factor], 1, 0));
            activos_segundo_hueco.push(z3.If(ocupacion_huecos_variables_f_num[variable][1][factor], 1, 0));
        }

        for (let factor = 0; factor < num_factores_den; factor++) {
            activos_primer_hueco.push(z3.If(ocupacion_huecos_variables_den[variable][0][factor], 1, 0));
            activos_segundo_hueco.push(z3.If(ocupacion_huecos_variables_den[variable][1][factor], 1, 0));
        }

        solver.add(z3.Implies(addsum(activos_primer_hueco).gt(0), addsum(activos_segundo_hueco).gt(0)));
    }
  }

  // una_por_hueco_v
  for (let variable = 0; variable < max_intermedias; variable++) {
    for (let hueco_num = 0; hueco_num < maxDeg; hueco_num++) {
        for (let var_anterior = 0; var_anterior < variable; var_anterior++) {
            for (let siguientes = var_anterior + 1; siguientes < variable; siguientes++) {
                solver.add(z3.Implies(ocupacion_huecos_variables_v_num[variable][hueco_num][var_anterior], z3.Not(ocupacion_huecos_variables_v_num[variable][hueco_num][siguientes])));
            }

            for (let factor = 0; factor < num_factores_num; factor++) {
                solver.add(z3.Implies(ocupacion_huecos_variables_v_num[variable][hueco_num][var_anterior], z3.Not(ocupacion_huecos_variables_f_num[variable][hueco_num][factor])));
            }
        }

        for (let factor = 0; factor < num_factores_num; factor++) {
            for (let factor_sig = factor + 1; factor_sig < num_factores_num; factor_sig++) {
                solver.add(z3.Implies(ocupacion_huecos_variables_f_num[variable][hueco_num][factor], z3.Not(ocupacion_huecos_variables_f_num[variable][hueco_num][factor_sig])));
            }
        }
    }

    for (let hueco_den = 0; hueco_den < maxDeg; hueco_den++) {
        for (let factor = 0; factor < num_factores_den; factor++) {
            for (let factor_sig = factor + 1; factor_sig < num_factores_den; factor_sig++) {
                solver.add(z3.Implies(ocupacion_huecos_variables_den[variable][hueco_den][factor], z3.Not(ocupacion_huecos_variables_den[variable][hueco_den][factor_sig])));
            }
        }
    }
  }

  // variables_en_orden
  for (let variable = 1; variable < max_intermedias; variable++) {
    let suma_actual = [];
    let suma_anterior = [];

    for (let hueco_num = 0; hueco_num < maxDeg; hueco_num++) {
        for (let var_anterior = 0; var_anterior < variable; var_anterior++) {
            suma_actual.push(z3.If(ocupacion_huecos_variables_v_num[variable][hueco_num][var_anterior], 1, 0));
        }

        for (let var_anterior = 0; var_anterior < variable - 1; var_anterior++) {
            suma_anterior.push(z3.If(ocupacion_huecos_variables_v_num[variable - 1][hueco_num][var_anterior], 1, 0));
        }

        for (let factor = 0; factor < num_factores_num; factor++) {
            suma_actual.push(z3.If(ocupacion_huecos_variables_f_num[variable][hueco_num][factor], 1, 0));
            suma_anterior.push(z3.If(ocupacion_huecos_variables_f_num[variable - 1][hueco_num][factor], 1, 0));
        }
    }

    for (let hueco_den = 0; hueco_den < maxDeg; hueco_den++) {
        for (let factor = 0; factor < num_factores_den; factor++) {
            suma_actual.push(z3.If(ocupacion_huecos_variables_den[variable][hueco_den][factor], 1, 0));
            suma_anterior.push(z3.If(ocupacion_huecos_variables_den[variable - 1][hueco_den][factor], 1, 0));
        }
    }

    solver.add(z3.Implies(addsum(suma_actual).gt(0), addsum(suma_anterior).gt(0)));
  }

  let cuantas_variables = [];

  // cubre_variables_v
  for (let variable = 0; variable < max_intermedias; variable++) {
    let variables_elem = [];
    for (let variable_original = 0; variable_original < cjto_variables.length; variable_original++) {
        let varInt = z3.Int.const(`var_${variable}_${variable_original}`);
        variables_elem.push(varInt);
    }

    cuantas_variables.push(variables_elem);
  }

  for (let variable = 0; variable < max_intermedias; variable++) {
    for (let variable_original = 0; variable_original < cjto_variables.length; variable_original++) {
        let conteo_var = [];
        for (let hueco_num = 0; hueco_num < maxDeg; hueco_num++) {
            for (let v = 0; v < variable; v++) {
                conteo_var.push(z3.If(ocupacion_huecos_variables_v_num[variable][hueco_num][v], cuantas_variables[v][variable_original], 0));
            }

            for (let factor = 0; factor < num_factores_num; factor++) {
                if (cjto_variables[variable_original] == factores_num_signal[factor]) {
                    conteo_var.push(z3.If(ocupacion_huecos_variables_f_num[variable][hueco_num][factor], factores_num_degree[factor], 0));
                }
            }
        }

        for (let hueco_den = 0; hueco_den < maxDeg; hueco_den++) {
            for (let factor = 0; factor < num_factores_den; factor++) {
                if (cjto_variables[variable_original] == factores_den_signal[factor]) {
                    conteo_var.push(z3.If(ocupacion_huecos_variables_den[variable][hueco_den][factor], factores_den_degree[factor], 0));
                }
            }
        }

        solver.add(cuantas_variables[variable][variable_original].eq(addsum(conteo_var)));
    }
  }

  let ocupacion_huecos_prod_v_num = [];
  let ocupacion_huecos_prod_f_num = [];
  let ocupacion_huecos_prod_den = [];

  // composicion_productos
  for (let prod = 0; prod < num_productos; prod++) {
    let huecos_prod_v_num = [];
    let huecos_prod_f_num = [];
    let huecos_prod_den = [];

    for (let hueco_num = 0; hueco_num < maxDeg; hueco_num++) {
        let ocupa_v = [];
        let ocupa_f = [];

        for (let variable = 0; variable < max_intermedias; variable++) {
            let varBool = z3.Bool.const(`ocupapvn_${prod}_${hueco_num}_${variable}`);
            ocupa_v.push(varBool);
            if (grados_prod[prod] <= maxDeg) solver.add(z3.Not(ocupa_v[variable]));
        }

        for (let factor = 0; factor < num_factores_num; factor++) {
            let varBool = z3.Bool.const(`ocupapfn_${prod}_${hueco_num}_${factor}`);
            ocupa_f.push(varBool);
            if (grados_prod[prod] <= maxDeg) solver.add(z3.Not(ocupa_f[factor]));
        }

        huecos_prod_v_num.push(ocupa_v);
        huecos_prod_f_num.push(ocupa_f);
    }

    for (let hueco_den = 0; hueco_den < maxDeg; hueco_den++) {
        let ocupa_f = [];
        for (let factor = 0; factor < num_factores_den; factor++) {
            let varBool = z3.Bool.const(`ocupapfd_${prod}_${hueco_den}_${factor}`);
            ocupa_f.push(varBool);
            if (grados_prod[prod] <= maxDeg) solver.add(z3.Not(ocupa_f[factor]));
        }

        huecos_prod_den.push(ocupa_f);
    }

    ocupacion_huecos_prod_v_num.push(huecos_prod_v_num);
    ocupacion_huecos_prod_f_num.push(huecos_prod_f_num);
    ocupacion_huecos_prod_den.push(huecos_prod_den);
  }

  // orden_huecos_productos
  for (let prod = 0; prod < num_productos; prod++) {
    if (grados_prod[prod] > maxDeg) {
        for (let hueco_num = 0; hueco_num < maxDeg; hueco_num++) {
            for (let variable = 0; variable < max_intermedias; variable++) {
                for (let hueco_sig = hueco_num + 1; hueco_sig < maxDeg; hueco_sig++) {
                    for (let var_anterior = 0; var_anterior < variable; var_anterior++) {
                        solver.add(z3.Implies(ocupacion_huecos_prod_v_num[prod][hueco_num][variable], z3.Not(ocupacion_huecos_prod_v_num[prod][hueco_sig][var_anterior])));
                    }
                }
            }

            for (let factor = 0; factor < num_factores_num; factor++) {
                for (let hueco_sig = hueco_num + 1; hueco_sig < maxDeg; hueco_sig++) {
                    for (let var_anterior = 0; var_anterior < max_intermedias; var_anterior++) {
                        solver.add(z3.Implies(ocupacion_huecos_prod_f_num[prod][hueco_num][factor], z3.Not(ocupacion_huecos_prod_v_num[prod][hueco_sig][var_anterior])));
                    }

                    for (let factores_anteriores = 0; factores_anteriores < factor; factores_anteriores++) {
                        solver.add(z3.Implies(ocupacion_huecos_prod_f_num[prod][hueco_num][factor], z3.Not(ocupacion_huecos_prod_f_num[prod][hueco_sig][factores_anteriores])));
                    }
                }
            }
        }
    }

    for (let hueco_den = 0; hueco_den < maxDeg; hueco_den++) {
        for (let factor = 0; factor < num_factores_den; factor++) {
            for (let hueco_sig = hueco_den + 1; hueco_sig < maxDeg; hueco_sig++) {
                for (let factores_anteriores = 0; factores_anteriores < factor; factores_anteriores++) {
                    solver.add(z3.Implies(ocupacion_huecos_prod_den[prod][hueco_den][factor], z3.Not(ocupacion_huecos_prod_den[prod][hueco_den][factores_anteriores])));
                }
            }
        }
    }
  }

  // rellenar_huecos_productos_en_orden
  for (let prod = 0; prod < num_productos; prod ++) {
    if (grados_prod[prod] > maxDeg) {
        for (let hueco_num = 1; hueco_num < maxDeg; hueco_num++) {
            let suma_actual = [];
            let suma_anterior = [];

            for (let variable = 0; variable < max_intermedias; variable++) {
                suma_actual.push(z3.If(ocupacion_huecos_prod_v_num[prod][hueco_num][variable], 1, 0));
                suma_anterior.push(z3.If(ocupacion_huecos_prod_v_num[prod][hueco_num - 1][variable], 1, 0));
            }

            for (let factor = 0; factor < num_factores_num; factor++) {
                suma_actual.push(z3.If(ocupacion_huecos_prod_f_num[prod][hueco_num][factor], 1, 0));
                suma_anterior.push(z3.If(ocupacion_huecos_prod_f_num[prod][hueco_num - 1][factor], 1, 0));
            }

            solver.add(z3.Implies(addsum(suma_actual).gt(0), addsum(suma_anterior).gt(0)));
        }

        for (let hueco_den = 1; hueco_den < maxDeg; hueco_den++) {
            let suma_actual = [];
            let suma_anterior = [];

            for (let factor = 0; factor < num_factores_den; factor++) {
                suma_actual.push(z3.If(ocupacion_huecos_prod_den[prod][hueco_den][factor], 1, 0));
                suma_anterior.push(z3.If(ocupacion_huecos_prod_den[prod][hueco_den - 1][factor], 1, 0));
            }

            solver.add(z3.Implies(addsum(suma_actual).gt(0), addsum(suma_anterior).gt(0)));
        }
    }
  }

  // restricciones_huecos_p
  for (let prod = 0; prod < num_productos; prod++) {
    let de_cuantas_depende_num = [];
    let de_cuantas_depende_den = [];

    if (grados_prod[prod] > maxDeg) {
        for (let hueco_num = 0; hueco_num < maxDeg; hueco_num++) {
            for (let variable = 0; variable < max_intermedias; variable++) {
                de_cuantas_depende_num.push(z3.If(ocupacion_huecos_prod_v_num[prod][hueco_num][variable], 1, 0));
            }

            for (let factor = 0; factor < num_factores_num; factor++) {
                de_cuantas_depende_num.push(z3.If(ocupacion_huecos_prod_f_num[prod][hueco_num][factor], factores_num_degree[factor], 0));
            }
        }

        for (let hueco_den = 0; hueco_den < maxDeg; hueco_den++) {
            for (let factor = 0; factor < num_factores_den; factor++) {
                de_cuantas_depende_den.push(z3.If(ocupacion_huecos_prod_den[prod][hueco_den][factor], factores_den_degree[factor], 0));
            }
        }

        solver.add(addsum(de_cuantas_depende_num).le(maxDeg));
        solver.add(addsum(de_cuantas_depende_den).le(maxDeg));
    }
  }

  // una_por_hueco_p
  for (let producto = 0; producto < num_productos; producto++) {
    if (grados_prod[producto] > maxDeg) {
        for (let hueco_num = 0; hueco_num < maxDeg; hueco_num++) {
            for (let variable = 0; variable < max_intermedias; variable++) {
                for (let siguientes = variable + 1; siguientes < max_intermedias; siguientes++) {
                    solver.add(z3.Implies(ocupacion_huecos_prod_v_num[producto][hueco_num][variable], z3.Not(ocupacion_huecos_prod_v_num[producto][hueco_num][siguientes])));
                }

                for (let factor = 0; factor < num_factores_num; factor++) {
                    solver.add(z3.Implies(ocupacion_huecos_prod_v_num[producto][hueco_num][variable], z3.Not(ocupacion_huecos_prod_f_num[producto][hueco_num][factor])));
                }
            }

            for (let factor = 0; factor < num_factores_num; factor++) {
                for (let factor_sig = factor + 1; factor_sig < num_factores_num; factor_sig++) {
                    solver.add(z3.Implies(ocupacion_huecos_prod_f_num[producto][hueco_num][factor], z3.Not(ocupacion_huecos_prod_f_num[producto][hueco_num][factor_sig])));
                }
            }
        }

        for (let hueco_den = 0; hueco_den < maxDeg; hueco_den++) {
            for (let factor = 0; factor < num_factores_den; factor++) {
                for (let factor_sig = factor + 1; factor_sig < num_factores_den; factor_sig++) {
                    solver.add(z3.Implies(ocupacion_huecos_prod_den[producto][hueco_den][factor], z3.Not(ocupacion_huecos_prod_den[producto][hueco_den][factor_sig])));
                }
            }
        }
    }
  }

  // cubre_variables_p
  for (let prod = 0; prod < num_productos; prod++) {
    if (grados_prod[prod] > maxDeg) {
        for (let variable_original = 0; variable_original < cjto_variables.length; variable_original++) {
            let conteo_var = [];
            for (let hueco_num = 0; hueco_num < maxDeg; hueco_num++) {
                for (let variable = 0; variable < max_intermedias; variable++) {
                    conteo_var.push(z3.If(ocupacion_huecos_prod_v_num[prod][hueco_num][variable], cuantas_variables[variable][variable_original], 0));
                }

                for (let factor = 0; factor < num_factores_num; factor++) {
                    if (cjto_variables[variable_original] == factores_num_signal[factor]) {
                        conteo_var.push(z3.If(ocupacion_huecos_prod_f_num[prod][hueco_num][factor], factores_num_degree[factor], 0));
                    }
                }
            }

            for (let hueco_den = 0; hueco_den < maxDeg; hueco_den++) {
                for (let factor = 0; factor < num_factores_den; factor++) {
                    if (cjto_variables[variable_original] == factores_den_signal[factor]) {
                        conteo_var.push(z3.If(ocupacion_huecos_prod_den[prod][hueco_den][factor], factores_den_degree[factor], 0));
                    }
                }
            }

            solver.add(addsum(conteo_var).eq(num_variables_por_producto[prod][variable_original]));
        }
    }
  }

  // restricciones_cuentan
  for (let variable = 0; variable < max_intermedias; variable++) {
    let huecos_ocupados = [];

    for (let hueco_num = 0; hueco_num < maxDeg; hueco_num++) {
        for (let variable_anterior = 0; variable_anterior < variable; variable_anterior++) {
            huecos_ocupados.push(z3.If(ocupacion_huecos_variables_v_num[variable][hueco_num][variable_anterior], 1, 0));
        }

        for (let factor = 0; factor < num_factores_num; factor++) {
            huecos_ocupados.push(z3.If(ocupacion_huecos_variables_f_num[variable][hueco_num][factor], 1, 0));
        }
    }

    for (let hueco_den = 0; hueco_den < maxDeg; hueco_den++) {
        for (let factor = 0; factor < num_factores_den; factor++) {
            huecos_ocupados.push(z3.If(ocupacion_huecos_variables_den[variable][hueco_den][factor], 1, 0));
        }
    }

    solver.addSoft(addsum(huecos_ocupados).eq(0), 1, "min_vars");
  }

  let result = await solver.check();
  if (result === 'sat') {
    let model = solver.model();

    console.log("\n=== COMPOSICIÓN DE VARIABLES INTERMEDIAS ===");
    for (let variable = 0; variable < max_intermedias; variable++) {
        let partes_num = [];
        let partes_den = [];
        let huecos_num = [];
        let huecos_den = [];

        for (let hueco_num = 0; hueco_num < maxDeg; hueco_num++) {
            contenido = " ";
            for (let prev_var = 0; prev_var < variable; prev_var++) {
                const val = model.eval(ocupacion_huecos_variables_v_num[variable][hueco_num][prev_var]).toString();
                if (val === "true") {
                    partes_num.push(`VI_${prev_var}`);
                    contenido = `VI_${prev_var}`;
                }
            }

            for (let factor = 0; factor < num_factores_num; factor++) {
                const val = model.eval(ocupacion_huecos_variables_f_num[variable][hueco_num][factor]).toString();
                if (val === "true") {
                    partes_num.push(`S_${factores_num_signal[factor]}`);
                    contenido = `S_${factores_num_signal[factor]}`;
                }
            }

            if (partes_num.length > 0) {
                huecos_num.push((hueco_num, contenido));
            }
        }

        for (let hueco_den = 0; hueco_den < maxDeg; hueco_den++) {
            contenido = " ";
            for (let factor = 0; factor < num_factores_den; factor++) {
                const val = model.eval(ocupacion_huecos_variables_den[variable][hueco_den][factor]).toString();
                if (val === "true") {
                    partes_den.push(`S_${factores_den_signal[factor]}`);
                    contenido = `S_${factores_den_signal[factor]}`;
                }
            }
            if (partes_den.length > 0) {
                huecos_den.push((hueco_den, contenido));
            }
        }

        if (partes_num.length > 0 || partes_den.length > 0) {
            if (partes_den.length > 0) {
                console.log(`VI_${variable} = (${partes_num.join(' * ')}) / (${partes_den.join(' * ')})`);
            } 
            else {
                console.log(`VI_${variable} = ${partes_num.join(' * ')}`);
            }

            console.log(`  Huecos numerador: ${JSON.stringify(huecos_num)}`);
            console.log(`  Huecos denominador: ${JSON.stringify(huecos_den)}`);
        }
    }

    console.log("\n=== COMPOSICIÓN DE PRODUCTOS ===");
    for (let prod = 0; prod < num_productos; prod++) {
        if (grados_prod[prod] <= maxDeg) {
            console.log(`Producto ${prod} no pasa de grado`);
        }
        else {
            let partes_num = [];
            let partes_den = [];
            let huecos_num = [];
            let huecos_den = [];

            for (let hueco_num = 0; hueco_num < maxDeg; hueco_num++) {
                contenido = " ";

                for (let variable = 0; variable < max_intermedias; variable++) {
                    const val = model.eval(ocupacion_huecos_prod_v_num[prod][hueco_num][variable]).toString();

                    if (val === "true") {
                        partes_num.push(`VI_${variable}`);
                        contenido = `VI_${variable}`;
                    }
                }

                for (let factor = 0; factor < num_factores_num; factor++) {
                    const val = model.eval(ocupacion_huecos_prod_f_num[prod][hueco_num][factor]).toString();
                    
                    if (val === "true") {
                        partes_num.push(`S_${factores_num_signal[factor]}`);
                        contenido = `S_${factores_num_signal[factor]}`;
                    }
                }

                if (partes_num.length > 0) huecos_num.push((huecos_num, contenido))
            }

            for (let hueco_den = 0; hueco_den < maxDeg; hueco_den++) {
                contenido = " ";

                for (let factor = 0; factor < num_factores_den; factor++) {
                    const val = model.eval(ocupacion_huecos_prod_den[prod][hueco_den][factor]).toString();

                    if (val === "true") {
                        partes_den.push(`S_${factores_den_signal[factor]}`);
                        contenido = `S_${factores_den_signal[factor]}`;
                    }
                }

                if (partes_den.length > 0) huecos_den.push((huecos_num, contenido));
            }

            if (partes_num.length > 0 || partes_den.length > 0) {
                if (partes_den.length > 0) {
                    console.log(`Producto ${prod}: grado ${grados_prod[prod]} > ${maxDeg}`);
                    console.log(`   = (${partes_num.join(' * ')}) / (${partes_den.join(' * ')})`);
                }
                else {
                    console.log(`Producto ${prod}: grado ${grados_prod[prod]} > ${maxDeg}`);
                    console.log(`   = ${partes_num.join(' * ')}`);
                }

                console.log(`   Huecos numerador: ${huecos_num}`);
                console.log(`   Huecos denominador: ${huecos_den}`);
            }
        }
    }
  }
  else {
    console.log(`\n❌ No se ha encontrado una solución.`);
  }
}

main();