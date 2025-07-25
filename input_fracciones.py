import random
import json
import subprocess

def generar_fracciones_json(
    num_fracciones=10,
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

        # signals ya no son listas, así que solo un número
        num_signal = random.randint(señal_inicial, señal_inicial + num_fracciones - 1)
        den_signal = random.randint(señal_inicial + num_fracciones, señal_inicial + 2 * num_fracciones - 1)

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

        # Mostrar en pantalla (adaptado a signals como enteros)
        num_str = f"{num_signal} [grado {grado_num}]"
        den_str = f"{den_signal} [grado {grado_den}]"
        print(f"Expresión {idx}: {num_str} / {den_str}")

    grado_objetivo = 3

    print(f"\nGrado objetivo (máximo permitido): {grado_objetivo}")

    return {
        "expressions": expresiones,
        "degree": grado_objetivo
    }

# Guardar archivo de entrada JSON
with open("input_fracciones.json", "w") as f:
    json.dump(generar_fracciones_json(), f, indent=4)

# Ejecutar solucionador (asegúrate de que fracciones_v1_1.py acepta el archivo como parámetro)
subprocess.run(["python", "fracciones_v1_1.py", "input_fracciones.json"])