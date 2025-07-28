import { init } from 'z3-solver';
import fs from 'fs';
import path from 'path';

function addsum(ctx, arr) {
  if (arr.length === 0) return ctx.Int.val(0);
  let asum = arr[0];
  for (let i = 1; i < arr.length; i++) {
    asum = ctx.mkAdd(asum, arr[i]);
  }
  return asum;
}

async function main() {
  const { Context, Z3 } = await init();
  const ctx = new Context('main');
  const { Bool, Int, Optimize, And, Not, Or, Implies, If } = ctx;

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

  const expresiones = data["expressions"];
  const maxDeg = data["degree"];
  const num_expresiones = expresiones.length;

  const solver = new Optimize(); // Solver();
  
  const expando = [];

  for (let exp = 0; exp < num_expresiones; exp++) {
    const boolVar = Bool.const(`exp_${exp}`);
    expando.push(boolVar);
    // solver.add(Or(boolVar, Not(boolVar))); // dummy constraint
    solver.addSoft(boolVar, 1, "keeps")
  }

  const juntar = []

  for (let exp = 0; exp < num_expresiones; exp++) {
    const juntar_exp =[]

    for (let e = 0; e < num_expresiones; e++) {
      const boolVar = Bool.const(`juntar_${exp}_${e}`)
      juntar_exp.push(boolVar)
    }

    juntar.push(juntar_exp)
  }

  for (let exp = 0; exp < num_expresiones; exp++) {
    for (let e = 0; e < num_expresiones; e++) {
      if (exp >= e) {
         solver.add(Not(juntar[exp][e]))
      }
      // else if (exp > e) {
      //   solver.add(Jun)
      // }
      else {
        solver.add(Implies(Not(And(expando[exp], expando[e])), Not(juntar[exp][e])))
        
        for (let anterior = 0; anterior < e; anterior ++) {
          solver.add(Implies(And(juntar[exp][e], juntar[exp][anterior]), Not(juntar[anterior][e])))
        }
      }
    }
  }

  for (let exp = 0; exp < num_expresiones; exp++) {
    const grado_num = [If(expando[exp], Int.val(expresiones[exp]["values"][0]["degree"]), Int.val(0))]
    const grado_den = [If(expando[exp], Int.val(expresiones[exp]["values"][1]["degree"]), Int.val(0))]

    for (let e = 0; e < num_expresiones; e++) {
      const prev_grado_num = grado_num[grado_num.length -1]
      const prev_grado_den = grado_den[grado_den.length -1]

      const expr1 = prev_grado_num.add(Int.val(expresiones[e]["values"][1]["degree"]));
      const expr2 = prev_grado_den.add(Int.val(expresiones[e]["values"][0]["degree"]));

      const cond = expr1.gt(expr2); // Z3.BoolExpr
      const maxExpr = ctx.If(cond, expr1, expr2);
      const nuevo_grado_num = ctx.If(juntar[exp][e], maxExpr, prev_grado_num);
      const nuevo_grado_den = ctx.If(juntar[exp][e], prev_grado_den.add(Int.val(expresiones[e]["values"][1]["degree"])), prev_grado_den);

      grado_num.push(nuevo_grado_num)
      grado_den.push(nuevo_grado_den)
    }

    const final_num = grado_num[grado_num.length -1]
    const final_den = grado_den[grado_den.length -1]

    const grado_total = ctx.If(expando[exp], ctx.If(final_num.gt(final_den), final_num, final_den), Int.val(0));

    solver.add(grado_total.le(Int.val(maxDeg)));
  }

  const result = await solver.check();
  if (result === 'sat') {
    const model = solver.model();

    const expanded = [];
    const notExpanded = [];

    for (let i = 0; i < num_expresiones; i++) {
      const val = model.eval(expando[i]);
      if (val && val.eq(ctx.Bool.val(true))) {
        expanded.push(i);
      } else {
        notExpanded.push(i);
      }
    }

    const unifications = [];
    const seen = new Set();

    for (const i of expanded) {
      const group = [i];
      for (let j = 0; j < num_expresiones; j++) {
        const joinVal = model.eval(juntar[i][j]);
        if (i !== j && joinVal && joinVal.eq(ctx.Bool.val(true))) {
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
}

main();
