#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import sys
import os
import random
import json
from pathlib import Path

# Añadir la carpeta padre al path para importar las versiones
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from suma_fracciones_0_1 import suma_fracciones as suma_v0_1
from suma_fracciones_v1_2 import suma_fracciones as suma_v1_2

# ==================== GENERAR Y EJECUTAR CASOS ====================

def generate_test_data(num_fractions, degree, save_json=True, description=""):
    """Genera datos de prueba en memoria y opcionalmente los guarda"""
    expressions = []
    
    for i in range(num_fractions):
        deg_num = random.randint(1, degree)
        deg_den = random.randint(1, degree - 1)
        signals_num = random.randint(1, degree * 2)
        signals_den = random.randint(1, degree * 2)
        
        expressions.append({
            "op": "frac",
            "values": [
                {"signals": signals_num, "degree": deg_num},
                {"signals": signals_den, "degree": deg_den}
            ]
        })
    
    data = {
        "degree": degree,
        "expressions": expressions
    }
    
    # Guardar si se solicita
    if save_json:
        test_data_dir = Path(os.path.dirname(__file__)) / "test_data"
        test_data_dir.mkdir(exist_ok=True)
        
        filename = f"test_{num_fractions}expr_deg{degree}.json"
        filepath = test_data_dir / filename
        
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
    
    return data

def test_case(version_name, suma_func, expressions, degree):
    """Prueba una versión y mide tiempos, retorna tiempo, estado, grupos y solución"""
    indices = list(range(len(expressions)))
    
    start = time.perf_counter()
    
    try:
        resultado = suma_func(degree, degree - 1, expressions, indices)
        end = time.perf_counter()
        elapsed = end - start
        
        if resultado == 0:
            return elapsed, "NO_SOLUTION", 0, None
        else:
            return elapsed, "SUCCESS", len(resultado), resultado
    
    except Exception as e:
        end = time.perf_counter()
        elapsed = end - start
        return elapsed, f"ERROR", 0, None

def run_tests():
    """Ejecuta casos de prueba de diferentes tamaños"""
    
    # Crear carpeta de datos de prueba
    test_data_dir = Path(os.path.dirname(__file__)) / "test_data"
    test_data_dir.mkdir(exist_ok=True)
    
    print("\n" + "="*80)
    print("🔬 BENCHMARK: Comparativa v0_1 (Int) vs v1_2 (Bool)")
    print("="*80)
    print(f"📁 JSON guardados en: {test_data_dir.resolve()}")
    print("="*80 + "\n")
    
    # Casos a probar: (num_fracciones, degree, descripcion)
    test_cases = [
        (3, 3, "Muy pequeño (3 expr)"),
        (4, 4, "Pequeño (4 expr)"),
        (5, 5, "Pequeño (5 expr)"),
        (6, 6, "Mediano (6 expr)"),
        (7, 6, "Mediano (7 expr)"),
        (8, 7, "Mediano-Grande (8 expr)"),
        (9, 7, "Grande (9 expr)"),
        (10, 7, "Grande (10 expr)"),
        (12, 8, "Muy grande (12 expr)"),
    ]
    
    results = []
    
    for num_frac, degree, description in test_cases:
        # Generar datos (y guardar JSON)
        data = generate_test_data(num_frac, degree, save_json=True, description=description)
        expressions = data["expressions"]
        
        print(f"📊 {description} | Grado: {degree}")
        print("-" * 80)
        
        # v0_1 (Int)
        time_v0_1, status_v0_1, groups_v0_1, sol_v0_1 = test_case("v0_1", suma_v0_1, expressions, degree)
        print(f"  v0_1 (Int):  {time_v0_1:8.4f}s [{status_v0_1}] - {groups_v0_1} grupos")
        
        # v1_2 (Bool)
        time_v1_2, status_v1_2, groups_v1_2, sol_v1_2 = test_case("v1_2", suma_v1_2, expressions, degree)
        print(f"  v1_2 (Bool): {time_v1_2:8.4f}s [{status_v1_2}] - {groups_v1_2} grupos")
        
        # Comparativa
        if time_v0_1 > 0 and time_v1_2 > 0:
            ratio = time_v1_2 / time_v0_1
            faster = "v0_1 ⚡" if ratio > 1 else "v1_2 ⚡"
            percent = abs(ratio - 1) * 100
            factor = max(ratio, 1/ratio) if ratio != 0 else 0
            print(f"  🏆 {faster} es {percent:.1f}% más rápida ({factor:.2f}x)")
            
            results.append({
                "caso": description,
                "v0_1": time_v0_1,
                "v1_2": time_v1_2,
                "ratio": ratio
            })
        
        print()
    
    # Resumen final
    print("="*80)
    print("📈 RESUMEN FINAL")
    print("="*80 + "\n")
    
    if results:
        v0_1_times = [r["v0_1"] for r in results if r["v0_1"] > 0]
        v1_2_times = [r["v1_2"] for r in results if r["v1_2"] > 0]
        
        if v0_1_times:
            print(f"v0_1 (Int):")
            print(f"  Tiempo total:    {sum(v0_1_times):8.4f}s")
            print(f"  Tiempo promedio: {sum(v0_1_times)/len(v0_1_times):8.4f}s")
            print(f"  Mínimo:          {min(v0_1_times):8.4f}s")
            print(f"  Máximo:          {max(v0_1_times):8.4f}s\n")
        
        if v1_2_times:
            print(f"v1_2 (Bool):")
            print(f"  Tiempo total:    {sum(v1_2_times):8.4f}s")
            print(f"  Tiempo promedio: {sum(v1_2_times)/len(v1_2_times):8.4f}s")
            print(f"  Mínimo:          {min(v1_2_times):8.4f}s")
            print(f"  Máximo:          {max(v1_2_times):8.4f}s\n")
        
        if v0_1_times and v1_2_times:
            avg_v0_1 = sum(v0_1_times) / len(v0_1_times)
            avg_v1_2 = sum(v1_2_times) / len(v1_2_times)
            avg_ratio = avg_v1_2 / avg_v0_1
            faster = "v1_2 (Bool)" if avg_ratio < 1 else "v0_1 (Int)"
            percent = abs(avg_ratio - 1) * 100
            
            print(f"🏅 GANADOR: {faster}")
            print(f"   Es {percent:.1f}% más rápida en promedio")
            print(f"   Factor: {max(avg_ratio, 1/avg_ratio):.2f}x")

def main():
    test_data_dir = Path(os.path.dirname(__file__)) / "test_data"
    
    run_tests()
    
    # Mostrar archivos guardados
    print("\n" + "="*80)
    print("✅ Benchmark completado")
    print("="*80)
    
    if test_data_dir.exists():
        json_files = list(test_data_dir.glob("*.json"))

    
    print()

if __name__ == "__main__":
    main()
