import random
import json
import subprocess

def generar_fracciones_json(
    num_fracciones=30,
    grado_min=0,
    grado_max=3,
    señal_inicial=1
):
    expresiones = []
    señal_actual = señal_inicial

    print("Fracciones generadas:")
    print("----------------------")

    for idx in range(num_fracciones):
        grado_num = random.randint(grado_min, grado_max)
        grado_den = random.randint(grado_min, grado_max)

        num_signal = señal_actual
        señal_actual += 1
        den_signal = señal_actual
        señal_actual += 1

        numerador = {
            "signals": num_signal,
            "degree": grado_num
        }

        denominador = {
            "signals": den_signal,
            "degree": grado_den
        }

        expresion = {
            "op": "frac",
            "values": [numerador, denominador]
        }

        expresiones.append(expresion)

        # Mostrar en pantalla
        num_str = f"{num_signal} [grado {grado_num}]"
        den_str = f"{den_signal} [grado {grado_den}]"
        print(f"Expresión {idx}: {num_str} / {den_str}")

    grado_objetivo = 5

    print(f"\nGrado objetivo (máximo permitido): {grado_objetivo}")

    return {
        "expressions": expresiones,
        "degree": grado_objetivo
    }

# Generar archivo de entrada
with open("input_fracciones.json", "w") as f:
    json.dump(generar_fracciones_json(), f, indent=4)

# Ejecutar el solucionador Z3
subprocess.run(["python", "fracciones_v1_incr.py", "input_fracciones.json"])