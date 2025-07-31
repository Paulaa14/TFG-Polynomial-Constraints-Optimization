const z3s = require("z3-solver")
const init = z3s.init;
const fs = require("fs");
const path = require("path");

function addsum(arr, z3) {
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

  let expresiones = data["expressions"];
  let maxDeg = z3.Int.val(data["degree"]);
  let num_expresiones = expresiones.length;
  
  for (let expr of expresiones) {
    for (let value of expr.values) {
      value.degree = z3.Int.val(value.degree);
    }
  }

  let expando = [];

  for (let exp = 0; exp < num_expresiones; exp++) {
    let boolVar = z3.Bool.const(`exp_${exp}`);
    expando.push(boolVar);
    solver.addSoft(boolVar, 10, "keeps");
  }

  for (let exp = 0; exp < num_expresiones; exp++) {
    let grado_num_exp = expresiones[exp]["values"][0]["degree"]
    let grado_den_exp = expresiones[exp]["values"][1]["degree"] 
    
    // Si ya se pasa de grado no se va a poder unificar con nada
    if (grado_num_exp > maxDeg || grado_den_exp > maxDeg) {
      solver.add(z3.Not(expando[exp]))
    }
  }

  let juntar = [];

  for (let exp = 0; exp < num_expresiones; exp++) {
    let juntar_exp =[];

    for (let e = exp + 1; e < num_expresiones; e++) {
      let boolVar = z3.Bool.const(`juntar_${exp}_${e}`);
      juntar_exp.push(boolVar);
    }

    juntar.push(juntar_exp);
  }

  for (let exp = 0; exp < num_expresiones; exp++) {
    for (let e = exp + 1; e < num_expresiones; e++) {
        solver.add(z3.Implies(z3.Or(z3.Not(expando[exp]), z3.Not(expando[e])), z3.Not(juntar[exp][e - exp - 1])));
        
        for (let anterior = 0; anterior < e - exp - 1; anterior ++) {
            solver.add(z3.Implies(z3.And(juntar[exp][e - exp - 1], juntar[exp][anterior]), z3.Not(juntar[anterior][e - anterior - 1])));
        }
    }
  }

  for (let exp = 0; exp < num_expresiones; exp++) {
    for (let e = exp + 1; e < num_expresiones; e++) {
        let grado_num_exp = expresiones[exp]["values"][0]["degree"]
        let grado_den_exp = expresiones[exp]["values"][1]["degree"] 
        let grado_num_e = expresiones[e]["values"][0]["degree"]
        let grado_den_e = expresiones[e]["values"][1]["degree"]

        // Si se juntan se pasa de grado
        if (grado_num_exp + grado_den_e > maxDeg || grado_num_e + grado_den_exp > maxDeg || grado_den_exp + grado_den_e > maxDeg) {
          solver.add(z3.Not(juntar[exp][e - exp - 1]))
        }
    }
  }

  // Comprobar que las expresiones que se forman no superan el grado
  for (let exp = 0; exp < num_expresiones; exp++) {
    let grado_num = [expresiones[exp]["values"][0]["degree"]];
    let grado_den = [expresiones[exp]["values"][1]["degree"]];

    for (let e = exp + 1; e < num_expresiones; e++) {
        let prev_grado_num = grado_num[grado_num.length -1];
        let prev_grado_den = grado_den[grado_den.length -1];

        let expr1 = prev_grado_num.add(expresiones[e]["values"][1]["degree"]);
        let expr2 = prev_grado_den.add(expresiones[e]["values"][0]["degree"]);

        let maxExpr = z3.If(expr1.gt(expr2), expr1, expr2);
        let nuevo_grado_num = z3.If(juntar[exp][e - exp - 1], maxExpr, prev_grado_num);
        let nuevo_grado_den = z3.If(juntar[exp][e - exp - 1], prev_grado_den.add(expresiones[e]["values"][1]["degree"]), prev_grado_den);

        grado_num.push(nuevo_grado_num);
        grado_den.push(nuevo_grado_den);
    }

    let final_num = grado_num[grado_num.length -1];
    let final_den = grado_den[grado_den.length -1];

    let grado_total = z3.If(expando[exp], z3.If(final_num.gt(final_den), final_num, final_den), 0);

    solver.add(grado_total.le(maxDeg));
  }

  for (let exp = 0; exp < num_expresiones; exp++) {
    let suma_fila = [];
    let suma_col = [];

    for(let e = exp + 1; e < num_expresiones; e++) {
      suma_fila.push(z3.If(juntar[exp][e - exp - 1], 1, 0));
    }

    for (let e = 0; e < exp; e++) {
        suma_col.push(z3.If(juntar[e][exp - e - 1], 1, 0));
    }

    solver.add(z3.Implies(addsum(suma_fila, z3).gt(0), addsum(suma_col, z3).eq(0)));
    solver.add(z3.Implies(addsum(suma_col, z3).gt(0), addsum(suma_fila, z3).eq(0)));
    solver.add(addsum(suma_col, z3).le(1));

    solver.add(z3.Implies(expando[exp], z3.Or(addsum(suma_fila, z3).gt(0), addsum(suma_col, z3).gt(0))));

    solver.addSoft(addsum(suma_fila, z3).eq(0), 5, "min_vars");
  }

  let result = await solver.check();
  if (result === 'sat') {
    let model = solver.model();

    const expanded = [];
    const notExpanded = [];

    for (let i = 0; i < num_expresiones; i++) {
      const val = model.eval(expando[i]).toString();
      if (val === "true") {
        expanded.push(i);
      } else {
        notExpanded.push(i);
      }
    }

    const unifications = [];
    const seen = new Set();

    for (const i of expanded) {
      const group = [i];
      for (let j = i + 1; j < num_expresiones; j++) {
        const joinVal = model.eval(juntar[i][j - i - 1]).toString();
        if (joinVal === "true") {
          group.push(j);
        }
      }

      const key = JSON.stringify([...new Set(group)].sort());
      if (group.length > 1 && !seen.has(key)) {
        unifications.push(group.sort((a, b) => a - b));
        seen.add(key);
      }
    }

    console.log('✅ Solución encontrada:\n');

    console.log('Fracciones con expando = true:', expanded);
    console.log('Fracciones con expando = false:', notExpanded);
    console.log();

    if (unifications.length > 0) {
      unifications.forEach((group, idx) => {
        console.log(`Fracción nueva ${idx + 1}: combinación de expresiones [${group.join(', ')}]`);
        group.forEach((g) => {
          const num = expresiones[g].values[0].signals;
          const den = expresiones[g].values[1].signals;
          console.log(`    · Exp ${g}: (${num}) \\ (${den})`);
        });
      });
    } else {
      console.log('No se han unificado fracciones.');
    }

    if (notExpanded.length > 0) {
      console.log('\nFracciones originales que no se han expandido:');
      notExpanded.forEach((i) => {
        const num = expresiones[i].values[0].signals;
        const den = expresiones[i].values[1].signals;
        console.log(`  - Expresión ${i} → (${num}) \\ (${den})`);
      });
    }
  } else {
    console.log('❌ No se encontró una solución válida bajo las restricciones dadas.');
  }
  
  const assertions = solver.assertions();
  const constraints = [];

  for (let i = 0; i < assertions.length(); i++) {
    constraints.push(assertions.get(i).toString());
  }

  fs.writeFileSync('restricciones.smt2', constraints.join('\n'), 'utf8');

}

main();
