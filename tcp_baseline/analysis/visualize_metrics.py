#!/usr/bin/env python3
"""
TCP Baseline Visualization - Comprehensive Performance Analysis
Generates 4 key plots for in-depth performance insights
"""

import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns

plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

def load_metrics(file='../data/tcp_baseline_metrics.json'):
    """Load metrics from JSON file"""
    with open(file, 'r') as f:
        return json.load(f).get('metrics', {})

def plot_performance_overview(metrics):
    """Create comprehensive 4-panel performance visualization"""
    fig = plt.figure(figsize=(20, 12))
    gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.35, wspace=0.30)
    
    # Extract data
    pi_times = metrics.get('packet_in', {}).get('timestamps', [])
    pi_lat = metrics.get('packet_in', {}).get('latencies', [])
    fm_lat = metrics.get('flow_mod', {}).get('latencies', [])
    pi_sizes = metrics.get('packet_in', {}).get('sizes', [])
    fm_sizes = metrics.get('flow_mod', {}).get('sizes', [])
    po_sizes = metrics.get('packet_out', {}).get('sizes', [])
    
    # ==== PANEL 1: Throughput Over Time (top-left) ====
    ax1 = fig.add_subplot(gs[0, 0])
    if len(pi_times) > 10:
        start = pi_times[0]
        
        # Calculate throughput in 1-second windows
        windows = {}
        for t in pi_times:
            w = int(t - start)
            windows[w] = windows.get(w, 0) + 1
        
        times = sorted(windows.keys())
        throughputs = [windows[w] for w in times]
        
        # Plot with filled area
        ax1.plot(times, throughputs, linewidth=2.5, color='#2E86AB', marker='o', 
                markersize=4, alpha=0.8, label='Packet-In Rate')
        ax1.fill_between(times, throughputs, alpha=0.3, color='#2E86AB')
        
        # Mean line
        mean_throughput = np.mean(throughputs)
        ax1.axhline(mean_throughput, color='#A23B72', linestyle='--', linewidth=2.5,
                   label=f'Mean: {mean_throughput:.0f} msg/s')
        
        # Highlight peak
        max_idx = np.argmax(throughputs)
        ax1.scatter(times[max_idx], throughputs[max_idx], color='red', s=150, 
                   zorder=5, marker='*', label=f'Peak: {max(throughputs)} msg/s')
        
        ax1.set_xlabel('Time (seconds)', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Messages per Second', fontsize=12, fontweight='bold')
        ax1.set_title('Throughput Over Time', fontsize=14, fontweight='bold', pad=20)
        ax1.legend(fontsize=10, loc='upper right', framealpha=0.9)
        ax1.grid(True, alpha=0.3, linestyle='--')
        ax1.set_xlim(left=0)
        ax1.set_ylim(bottom=0)
        ax1.tick_params(labelsize=10)
    
    # ==== PANEL 2: Average Latency Comparison (top-right) ====
    ax2 = fig.add_subplot(gs[0, 1])
    
    # Simple bar chart comparing average latencies
    msg_types = []
    avg_latencies = []
    colors_bar = []
    
    if pi_lat:
        msg_types.append('Packet-In')
        avg_latencies.append(np.mean(pi_lat))
        colors_bar.append('#06A77D')
    
    if fm_lat:
        msg_types.append('Flow-Mod')
        avg_latencies.append(np.mean(fm_lat))
        colors_bar.append('#F77F00')
    
    if msg_types:
        bars = ax2.bar(msg_types, avg_latencies, color=colors_bar, alpha=0.8, 
                      edgecolor='black', linewidth=2, width=0.6)
        
        # Add value labels on bars
        for i, (bar, val) in enumerate(zip(bars, avg_latencies)):
            ax2.text(bar.get_x() + bar.get_width()/2., val,
                    f'{val:.2f} ms',
                    ha='center', va='bottom', fontsize=12, fontweight='bold')
            
            # Add sample count below bar
            if i == 0 and pi_lat:
                ax2.text(bar.get_x() + bar.get_width()/2., -0.5,
                        f'(n={len(pi_lat)})',
                        ha='center', va='top', fontsize=10)
            elif i == 1 and fm_lat:
                ax2.text(bar.get_x() + bar.get_width()/2., -0.5,
                        f'(n={len(fm_lat)})',
                        ha='center', va='top', fontsize=10)
        
        ax2.set_ylabel('Average Latency (ms)', fontsize=12, fontweight='bold')
        ax2.set_title('Average Latency by Message Type', fontsize=14, fontweight='bold', pad=20)
        ax2.grid(True, alpha=0.3, axis='y', linestyle='--')
        ax2.set_ylim(bottom=0, top=max(avg_latencies) * 1.3)
        ax2.tick_params(labelsize=11)
        
        # Add interpretation
        fastest = msg_types[np.argmin(avg_latencies)]
        slowest = msg_types[np.argmax(avg_latencies)]
        diff = max(avg_latencies) - min(avg_latencies)
        
        if len(msg_types) > 1:
            interpretation = f'{fastest} is faster\nDifference: {diff:.2f} ms'
        else:
            interpretation = f'Average: {avg_latencies[0]:.2f} ms'
            
        ax2.text(0.98, 0.98, interpretation, transform=ax2.transAxes,
                fontsize=10, verticalalignment='top', horizontalalignment='right',
                bbox=dict(boxstyle='round,pad=0.6', facecolor='lightblue', 
                         alpha=0.9, edgecolor='darkblue', linewidth=2))
    
    # ==== PANEL 3: Message Size Distribution (bottom-left) ====
    ax3 = fig.add_subplot(gs[1, 0])
    
    all_sizes = []
    size_labels = []
    size_colors = []
    
    if pi_sizes:
        all_sizes.append(pi_sizes)
        size_labels.append('Packet-In')
        size_colors.append('#06A77D')
    
    if fm_sizes:
        all_sizes.append(fm_sizes)
        size_labels.append('Flow-Mod')
        size_colors.append('#F77F00')
    
    if po_sizes:
        all_sizes.append(po_sizes)
        size_labels.append('Packet-Out')
        size_colors.append('#D62828')
    
    if all_sizes:
        # Horizontal box plot
        bp = ax3.boxplot(all_sizes, labels=size_labels, patch_artist=True,
                        vert=False, showmeans=True, meanline=True,
                        widths=0.6, medianprops=dict(linewidth=2, color='black'))
        
        # Color the boxes
        for patch, color in zip(bp['boxes'], size_colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
            patch.set_linewidth(1.5)
        
        # UDP limit line
        ax3.axvline(65507, color='red', linestyle='--', linewidth=2.5, alpha=0.7,
                   label='UDP Limit (65,507 bytes)', zorder=10)
        
        ax3.set_xlabel('Message Size (bytes)', fontsize=12, fontweight='bold')
        ax3.set_ylabel('Message Type', fontsize=12, fontweight='bold')
        ax3.set_title('Message Size Distribution vs UDP Limit', fontsize=14, fontweight='bold', pad=20)
        ax3.legend(fontsize=10, loc='upper right', framealpha=0.9)
        ax3.grid(True, alpha=0.3, axis='x', linestyle='--')
        ax3.tick_params(labelsize=10)
        ax3.yaxis.set_tick_params(labelsize=11)
        
        # Calculate and display safety margin - repositioned
        max_size = max([max(s) for s in all_sizes])
        margin = ((65507 - max_size) / 65507) * 100
        ax3.text(0.02, 0.02, 
                f'Max: {max_size} B\nMargin: {margin:.1f}%\nUDP OK',
                transform=ax3.transAxes, fontsize=10, verticalalignment='bottom',
                bbox=dict(boxstyle='round,pad=0.6', facecolor='lightgreen', 
                         alpha=0.85, edgecolor='darkgreen', linewidth=2))
    
    # ==== PANEL 4: Protocol Overhead Breakdown (bottom-right) ====
    ax4 = fig.add_subplot(gs[1, 1])
    
    # Calculate protocol overhead
    overhead_types = ['TCP\nHeader', 'IP\nHeader', 'Ethernet\nHeader']
    overhead_bytes = [20, 20, 14]  # Standard sizes
    overhead_colors = ['#E63946', '#F77F00', '#06A77D']
    
    # Create bar chart
    bars = ax4.bar(overhead_types, overhead_bytes, color=overhead_colors, 
                   alpha=0.8, edgecolor='black', linewidth=2, width=0.6)
    
    # Add value labels
    for bar, val in zip(bars, overhead_bytes):
        ax4.text(bar.get_x() + bar.get_width()/2., val,
                f'{val} bytes',
                ha='center', va='bottom', fontsize=11, fontweight='bold')
    
    ax4.set_ylabel('Bytes per Message', fontsize=12, fontweight='bold')
    ax4.set_title('TCP Protocol Overhead Breakdown', fontsize=14, fontweight='bold', pad=20)
    ax4.grid(True, alpha=0.3, axis='y', linestyle='--')
    ax4.set_ylim(bottom=0, top=25)
    ax4.tick_params(labelsize=11)
    
    # Add total overhead annotation
    total_overhead = sum(overhead_bytes)
    udp_overhead = 8 + 20 + 14  # UDP + IP + Ethernet = 42 bytes
    savings = total_overhead - udp_overhead
    savings_pct = (savings / total_overhead) * 100
    
    info_text = f'Total TCP Overhead: {total_overhead} bytes/msg\n'
    info_text += f'UDP Overhead: {udp_overhead} bytes/msg\n'
    info_text += f'Potential Savings: {savings} bytes ({savings_pct:.0f}%)'
    
    ax4.text(0.98, 0.98, info_text, transform=ax4.transAxes,
            fontsize=10, verticalalignment='top', horizontalalignment='right',
            bbox=dict(boxstyle='round,pad=0.7', facecolor='lightyellow', 
                     alpha=0.9, edgecolor='orange', linewidth=2))
    
    # Overall title
    plt.suptitle('TCP Baseline Performance Analysis', fontsize=16, fontweight='bold', y=0.995)
    
    plt.savefig('../results/tcp_baseline_performance.png', dpi=300, bbox_inches='tight', pad_inches=0.3)
    print("✓ Created: ../results/tcp_baseline_performance.png")
    plt.close()

def print_summary(metrics):
    """Print essential metrics summary"""
    pi_times = metrics.get('packet_in', {}).get('timestamps', [])
    pi_lat = metrics.get('packet_in', {}).get('latencies', [])
    pi_sizes = metrics.get('packet_in', {}).get('sizes', [])
    fm_sizes = metrics.get('flow_mod', {}).get('sizes', [])
    
    print("\n" + "="*60)
    print("TCP BASELINE SUMMARY")
    print("="*60)
    
    if pi_times:
        duration = pi_times[-1] - pi_times[0]
        print(f"\nDuration:        {duration:.2f} seconds")
        print(f"Total Messages:  {len(pi_times):,}")
        print(f"Throughput:      {len(pi_times)/duration:.0f} msg/sec")
    
    if pi_lat:
        print(f"\nLatency (n={len(pi_lat)}):")
        print(f"  Mean:          {np.mean(pi_lat):.3f} ms")
        print(f"  Median:        {np.median(pi_lat):.3f} ms")
        print(f"  Std Dev:       {np.std(pi_lat):.3f} ms")
        print(f"  P95:           {np.percentile(pi_lat, 95):.3f} ms")
        print(f"  P99:           {np.percentile(pi_lat, 99):.3f} ms")
        print(f"  Range:         [{np.min(pi_lat):.3f}, {np.max(pi_lat):.3f}] ms")
    
    if pi_sizes or fm_sizes:
        all_sizes = (pi_sizes if pi_sizes else []) + (fm_sizes if fm_sizes else [])
        max_size = max(all_sizes)
        margin = ((65507 - max_size) / 65507) * 100
        print(f"\nMessage Sizes:")
        print(f"  Max Size:      {max_size} bytes")
        print(f"  UDP Limit:     65,507 bytes")
        print(f"  Safety Margin: {margin:.1f}%")
        print(f"  UDP Compatible: {'✓ YES' if max_size < 65507 else '✗ NO'}")
    
    print("="*60 + "\n")

if __name__ == '__main__':
    metrics = load_metrics()
    plot_performance_overview(metrics)
    print_summary(metrics)
