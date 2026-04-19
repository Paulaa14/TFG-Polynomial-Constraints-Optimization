#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import matplotlib.pyplot as plt
from pathlib import Path
import numpy as np

def load_results(results_file):
    with open(results_file, 'r') as f:
        return json.load(f)

def plot_results(results_data):
    data = results_data['data']
    
    input_sizes = []
    all_times_v0_1 = []
    all_times_v1_2 = []
    
    for entry in data:
        input_sizes.append(entry['num_expressions'])
        all_times_v0_1.extend(entry['v_0_1_times'])
        all_times_v1_2.extend(entry['v_bool_times'])
    
    fig = plt.figure(figsize=(18, 10))
    ax1 = plt.subplot(1, 2, 1)
    
    sample_idx = 0
    x_ticks = []
    x_labels = []
    
    from statistics import mean
    avg_x_positions = []
    avg_v0_1 = []
    avg_v1_2 = []
    
    all_x_positions_v0_1 = []
    all_times_individual_v0_1 = []
    all_x_positions_v1_2 = []
    all_times_individual_v1_2 = []
    
    for i, entry in enumerate(data):
        v0_1_times = entry['v_0_1_times']
        v1_2_times = entry['v_bool_times']
        num_expr = entry['num_expressions']
        
        x_positions_v0_1 = [sample_idx + j * 0.12 for j in range(len(v0_1_times))]
        x_positions_v1_2 = [sample_idx + 0.06 + j * 0.12 for j in range(len(v1_2_times))]
        
        ax1.scatter(x_positions_v0_1, v0_1_times, color='#FF6B6B', s=150, alpha=0.95, 
                   label='v_0_1' if i == 0 else '', marker='o', edgecolors='#CC5555', linewidth=2)
        
        ax1.scatter(x_positions_v1_2, v1_2_times, color='#4ECDC4', s=150, alpha=0.95,
                   label='v_bool' if i == 0 else '', marker='s', edgecolors='#2BB8A8', linewidth=2)
        
        all_x_positions_v0_1.extend(x_positions_v0_1)
        all_times_individual_v0_1.extend(v0_1_times)
        all_x_positions_v1_2.extend(x_positions_v1_2)
        all_times_individual_v1_2.extend(v1_2_times)
        
        x_tick_pos = sample_idx + 0.25
        x_ticks.append(x_tick_pos)
        x_labels.append(str(num_expr))
        
        avg_x_positions.append(x_tick_pos)
        avg_v0_1.append(mean(v0_1_times))
        avg_v1_2.append(mean(v1_2_times))
        
        ax1.axvline(x=x_tick_pos, color='gray', linestyle='--', alpha=0.4, linewidth=1)
        
        sample_idx += 1.2
    
    if all_x_positions_v0_1:
        ax1.plot(all_x_positions_v0_1, all_times_individual_v0_1, color='#FF6B6B', linewidth=2, alpha=0.8)
    if all_x_positions_v1_2:
        ax1.plot(all_x_positions_v1_2, all_times_individual_v1_2, color='#4ECDC4', linewidth=2, alpha=0.8)
    
    ax1.set_xlabel('Input size (number of expressions)', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Time (seconds)', fontsize=12, fontweight='bold')
    ax1.set_title('Real times of each algorithm by input', fontsize=13, fontweight='bold', pad=15)
    ax1.legend(fontsize=11, loc='upper left')

    all_times = []
    for entry in data:
        all_times.extend(entry['v_0_1_times'])
        all_times.extend(entry['v_bool_times'])
    max_time = max(all_times) if all_times else 2
    y_limit = max_time * 1.1  # Add 10% margin
    ax1.set_ylim(0, y_limit)
    ax1.set_xticks(x_ticks)
    ax1.set_xticklabels(x_labels, rotation=45, ha='right')
    
    ax2 = plt.subplot(1, 2, 2)
    
    input_sizes_unique = []
    improvements = []
    faster_algo = []
    
    for entry in data:
        v0_1_times = entry['v_0_1_times']
        v1_2_times = entry['v_bool_times']
        num_expr = entry['num_expressions']
        
        from statistics import mean
        mean_v0_1 = mean(v0_1_times)
        mean_v1_2 = mean(v1_2_times)
        
        ratio = mean_v1_2 / mean_v0_1
        
        if ratio > 1:
            imp = (1 - 1/ratio) * 100
            faster = 'v_0_1'
        else:
            imp = (1 - ratio) * 100
            faster = 'v_bool'
        
        input_sizes_unique.append(num_expr)
        improvements.append(imp)
        faster_algo.append(faster)
    
    colors = ['#FF6B6B' if algo == 'v_0_1' else '#4ECDC4' for algo in faster_algo]
    
    bars = ax2.barh(input_sizes_unique, improvements, color=colors, alpha=0.8, 
                     edgecolor='black', linewidth=1.5)
    
    ax2.set_xlabel('Percentage improvement (%)', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Input size (number of expressions)', fontsize=12, fontweight='bold')
    ax2.set_title('Speed improvement (% faster)', fontsize=13, fontweight='bold', pad=15)
    
    for bar, imp, algo in zip(bars, improvements, faster_algo):
        label_text = f'{imp:.1f}% ({algo})'
        x_pos = imp + 0.5
        ax2.text(x_pos, bar.get_y() + bar.get_height()/2, label_text,
                ha='left', va='center', fontsize=9, fontweight='bold')
    
    plt.suptitle('Performance comparison: v_0_1 vs v_bool', 
                 fontsize=14, fontweight='bold', y=1.00)
    plt.subplots_adjust(left=0.08, right=0.97, top=0.88, bottom=0.12, wspace=0.3)
    
    return fig

def create_summary_table(results_data, ax=None):
    from statistics import mean
    data = results_data['data']
    
    table_data = []
    for entry in data:
        num_expr = entry['num_expressions']
        v0_1_times = entry['v_0_1_times']
        v1_2_times = entry['v_bool_times']
        
        mean_v0_1 = mean(v0_1_times)
        mean_v1_2 = mean(v1_2_times)
        
        ratio = mean_v1_2 / mean_v0_1
        
        table_data.append([
            str(num_expr),
            f'{mean_v0_1:.4f}s',
            f'{mean_v1_2:.4f}s',
            f'{ratio:.3f}x'
        ])
    
    columns = ['Input size', 'V_    0_1 average', 'V_bool average', 'Factor']
    
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

script_dir = Path(__file__).parent
results_file = script_dir / 'results' / 'benchmark_results.json'

if not results_file.exists():
    print(f"Archivo no encontrado: {results_file}")

else:
    print("Cargando resultados...")
    results_data = load_results(results_file)

    print("Generando graficas...")
    fig = plot_results(results_data)

    output_file = script_dir / 'results' / 'benchmark_comparison.png'
    fig.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"Grafica guardada: {output_file}")

    print("Generando tabla resumen...")
    fig_table = plt.figure(figsize=(12, len(results_data['data']) * 0.4 + 1.5))
    ax_table = fig_table.add_subplot(111)
    create_summary_table(results_data, ax_table)

    output_table = script_dir / 'results' / 'benchmark_summary_table.png'
    fig_table.savefig(output_table, dpi=150, bbox_inches='tight')
    print(f"Tabla resumen guardada: {output_table}")

    plt.show()

    print("Completado")
