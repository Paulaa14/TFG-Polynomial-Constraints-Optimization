const z3s = require("z3-solver")
const init = z3s.init;
const fs = require("fs");
const path = require("path");

function addsum(arr) {
  if (arr.length === 0) return z3.Int.val(0);
  let asum = arr[0];
  for (let i = 1; i < arr.length; i++) {
    asum = asum.add(arr[i]);
  }
  return asum;
}

async function main() {
  let { Context } = await init();
  let z3 = Context('main');

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

  let factores_num = [];
  let factores_den = [];

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

    grados_prod.push(max(grado_num, grado_den));
  }

  for (let p = 0; p < num_productos; p++) {
    let exp = productos[p]["expressions"];
    let grado = grados_prod[p];

    for (let e = 0; e < exp.length; e++) {
        if (grado > maxDeg) {
            cjto_variables.add(e["values"][0]["signals"]);
            cjto_variables.add(e["values"][1]["signals"]);

            factores_num.push(e["values"][0]["signals"]);
            factores_den.push(e["values"][1]["signals"]);
        }
    }
  }

  let num_factores_num = factores_num.length;
  let num_factores_den = factores_den.length;

  cjto_variables = Array.from(cjto_variables);
  cjto_variables.sort((a, b) => a.localeCompare(b, 'es'));
  
  let num_variables_por_producto = [];
  for (let prod = 0; prod < productos.length; prod++) {
    let counts = [];

    for (let v = 0; v < cjto_variables.length; v++) {
        let c_num = 0;
        let c_den = 0;

        for (let exp = 0; exp < productos[prod]["expressions"]; exp++) {
            if (exp["values"][0]["signals"] == cjto_variables[v]) {
                c_num += exp["values"][0]["degree"];
            }
            if (exp["values"][1]["signals"] == cjto_variables[v]) {
                c_den += exp["values"][1]["degree"];
            }
        }

        counts.push(c_num + c_den);
    }

    num_variables_por_producto.push(counts);
  }

  let max_intermedias = 10;

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
                    solver.add(z3.Implies(ocupacion_huecos_variables_f_num[variable][hueco_num][factor], z3.Not(ocupacion_huecos_variables_f_num[variable][hueco_sig][var_anterior])));
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
}

main();