#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import sys
import os
import random
import matplotlib.pyplot as plt
from pathlib import Path
from statistics import mean

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from suma_fracciones_0_1 import suma_fracciones as suma_v0_1
from suma_fracciones_v1_2 import suma_fracciones as suma_v1_2


def generate_test_data(num_fractions, degree):
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
    
    return expressions


def test_case(suma_func, expressions, degree):
    indices = list(range(len(expressions)))
    
    start = time.perf_counter()
    
    resultado = suma_func(degree, degree - 1, expressions, indices)
    end = time.perf_counter()
    elapsed = end - start
    
    if resultado == 0:
        return elapsed
    else:
        return elapsed


def run_benchmark():
    results_dir = Path(os.path.dirname(__file__)) / "results"
    results_dir.mkdir(exist_ok=True)
    
    print(f"Resultados en: {results_dir.resolve()}\n")
    
    NUM_SAMPLES = 1
    test_cases = [
        3, 4, 5, 6, 7, 8, 9, 10,
        11, 12, 13, 14, 15, 16, 17, 18,
        19, 20, 21, 22, 23, 24, 25, 26,
        27, 28, 29, 30, 31, 32
    ]
    
    results = []
    benchmark_data = {"data": []}
    
    maxDeg = 3
    for num_frac in test_cases:
        print(f"Tamaño: {num_frac}")
        
        times_v0_1 = []
        times_v1_2 = []
        
        for sample_id in range(NUM_SAMPLES):
            expressions = generate_test_data(num_frac, maxDeg)
            
            time_v0_1 = test_case(suma_v0_1, expressions, maxDeg)
            times_v0_1.append(time_v0_1)
            
            time_v1_2 = test_case(suma_v1_2, expressions, maxDeg)
            times_v1_2.append(time_v1_2)
            
            print(f"  v0_1={time_v0_1:8.4f}s | v1_2={time_v1_2:8.4f}s")
        
        if times_v0_1 and times_v1_2:
            mean_v0_1 = mean(times_v0_1)
            mean_v1_2 = mean(times_v1_2)
            ratio = mean_v1_2 / mean_v0_1
            
            results.append({
                "num_expressions": num_frac,
                "v0_1": mean_v0_1,
                "v1_2": mean_v1_2,
                "ratio": ratio
            })
            
            benchmark_data["data"].append({
                "num_expressions": num_frac,
                "degree": maxDeg,
                "v0_1_times": times_v0_1,
                "v1_2_times": times_v1_2
            })
        
        print()
    
    print()
    
    if results:
        v0_1_times = [r["v0_1"] for r in results if r["v0_1"] > 0]
        v1_2_times = [r["v1_2"] for r in results if r["v1_2"] > 0]
        
        if v0_1_times and v1_2_times:
            avg_v0_1 = mean(v0_1_times)
            avg_v1_2 = mean(v1_2_times)
            faster = "v1_2" if avg_v1_2 < avg_v0_1 else "v0_1"
            print(f"Promedio v0_1: {avg_v0_1:.4f}s")
            print(f"Promedio v1_2: {avg_v1_2:.4f}s")
            print(f"Ganador: {faster}")
    
    return benchmark_data


def plot_results(results_data):
    data = results_data['data']
    
    fig = plt.figure(figsize=(18, 10))
    ax1 = plt.subplot(1, 2, 1)
    
    sample_idx = 0
    x_ticks = []
    x_labels = []
    avg_x_positions = []
    avg_v0_1 = []
    avg_v1_2 = []
    
    for i, entry in enumerate(data):
        v0_1_times = entry['v0_1_times']
        v1_2_times = entry['v1_2_times']
        num_expr = entry['num_expressions']
        
        x_positions_v0_1 = [sample_idx + j * 0.12 for j in range(len(v0_1_times))]
        x_positions_v1_2 = [sample_idx + 0.06 + j * 0.12 for j in range(len(v1_2_times))]
        
        ax1.scatter(x_positions_v0_1, v0_1_times, color='#FF6B6B', s=150, alpha=0.7, 
                   label='v0.1 (Int) - datos' if i == 0 else '', marker='o', edgecolors='#CC5555', linewidth=2)
        ax1.scatter(x_positions_v1_2, v1_2_times, color='#4ECDC4', s=150, alpha=0.7,
                   label='v1.2 (Bool) - datos' if i == 0 else '', marker='s', edgecolors='#2BB8A8', linewidth=2)
        
        x_tick_pos = sample_idx + 0.25
        x_ticks.append(x_tick_pos)
        x_labels.append(str(num_expr))
        
        avg_x_positions.append(x_tick_pos)
        avg_v0_1.append(mean(v0_1_times))
        avg_v1_2.append(mean(v1_2_times))
        
        ax1.axvline(x=x_tick_pos, color='gray', linestyle='--', alpha=0.4, linewidth=1)
        
        sample_idx += 1.2
    
    ax1.plot(avg_x_positions, avg_v0_1, color='#FF6B6B', linewidth=3, 
            label='v0.1 (Int) - promedio', marker='D', markersize=8, 
            markerfacecolor='#FF6B6B', markeredgecolor='#CC5555', markeredgewidth=2)
    ax1.plot(avg_x_positions, avg_v1_2, color='#4ECDC4', linewidth=3, 
            label='v1.2 (Bool) - promedio', marker='D', markersize=8,
            markerfacecolor='#4ECDC4', markeredgecolor='#2BB8A8', markeredgewidth=2)
    
    ax1.set_xlabel('Tamanio de entrada (expresiones)', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Tiempo (segundos)', fontsize=12, fontweight='bold')
    ax1.set_title('Tiempos reales de cada algoritmo por entrada', fontsize=13, fontweight='bold', pad=15)
    ax1.legend(fontsize=11, loc='upper left')
    ax1.set_ylim(0, 2)
    ax1.set_xticks(x_ticks)
    ax1.set_xticklabels(x_labels, rotation=45, ha='right')
    
    ax2 = plt.subplot(1, 2, 2)
    
    input_sizes_unique = []
    improvements = []
    faster_algo = []
    
    for entry in data:
        v0_1_times = entry['v0_1_times']
        v1_2_times = entry['v1_2_times']
        num_expr = entry['num_expressions']
        
        mean_v0_1 = mean(v0_1_times)
        mean_v1_2 = mean(v1_2_times)
        
        ratio = mean_v1_2 / mean_v0_1
        
        if ratio > 1:
            imp = (1 - 1/ratio) * 100
            faster = 'v0.1'
        else:
            imp = (1 - ratio) * 100
            faster = 'v1.2'
        
        input_sizes_unique.append(num_expr)
        improvements.append(imp)
        faster_algo.append(faster)
    
    colors = ['#FF6B6B' if algo == 'v0.1' else '#4ECDC4' for algo in faster_algo]
    
    bars = ax2.barh(input_sizes_unique, improvements, color=colors, alpha=0.8, 
                     edgecolor='black', linewidth=1.5)
    
    ax2.set_xlabel('Mejora porcentual (%)', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Tamanio de entrada (expresiones)', fontsize=12, fontweight='bold')
    ax2.set_title('Mejora de velocidad (% mas rapido)', fontsize=13, fontweight='bold', pad=15)
    
    for bar, imp, algo in zip(bars, improvements, faster_algo):
        label_text = f'{imp:.1f}% ({algo})'
        x_pos = imp + 0.5
        ax2.text(x_pos, bar.get_y() + bar.get_height()/2, label_text,
                ha='left', va='center', fontsize=9, fontweight='bold')
    
    plt.suptitle('Analisis de rendimiento: v0.1 (Int) vs v1.2 (Bool)', 
                 fontsize=14, fontweight='bold', y=1.00)
    plt.subplots_adjust(left=0.08, right=0.97, top=0.88, bottom=0.12, wspace=0.3)
    
    return fig


def create_summary_table(results_data, ax=None):
    data = results_data['data']
    
    table_data = []
    for entry in data:
        num_expr = entry['num_expressions']
        v0_1_times = entry['v0_1_times']
        v1_2_times = entry['v1_2_times']
        
        mean_v0_1 = mean(v0_1_times)
        mean_v1_2 = mean(v1_2_times)
        
        ratio = mean_v1_2 / mean_v0_1
        
        table_data.append([
            str(num_expr),
            f'{mean_v0_1:.4f}s',
            f'{mean_v1_2:.4f}s',
            f'{ratio:.3f}x'
        ])
    
    columns = ['Input size', 'V0_1 average', 'V_bool average', 'Factor']
    
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, len(table_data) * 0.4 + 1.5))
    
    table = ax.table(cellText=table_data, colLabels=columns, cellLoc='center',
                     loc='center', colWidths=[0.20, 0.25, 0.25, 0.20])
    
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2)
    
    for i in range(len(columns)):
        table[(0, i)].set_facecolor('#404040')
        table[(0, i)].set_text_props(weight='bold', color='white')
    
    for i in range(1, len(table_data) + 1):
        color = '#F0F0F0' if i % 2 == 0 else '#FFFFFF'
        for j in range(len(columns)):
            table[(i, j)].set_facecolor(color)
    
    ax.axis('tight')
    ax.axis('off')
    
    return table


print("Ejecutando benchmark...\n")
benchmark_data = run_benchmark()

results_dir = Path(__file__).parent / 'results'

print("Generando graficas...")
fig = plot_results(benchmark_data)

output_file = results_dir / 'benchmark_comparison.png'
fig.savefig(output_file, dpi=150, bbox_inches='tight')
print(f"Grafica guardada: {output_file}")

print("Generando tabla resumen...")
fig_table = plt.figure(figsize=(12, len(benchmark_data['data']) * 0.4 + 1.5))
ax_table = fig_table.add_subplot(111)
create_summary_table(benchmark_data, ax_table)

output_table = results_dir / 'benchmark_summary_table.png'
fig_table.savefig(output_table, dpi=150, bbox_inches='tight')
print(f"Tabla resumen guardada: {output_table}")

plt.show()

print("Completado")

