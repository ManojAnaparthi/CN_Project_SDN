# File: analyze_tcp_performance.py
"""
Analyze TCP baseline performance from captured data
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

class TCPPerformanceAnalyzer:
    """Analyze TCP performance metrics"""
    
    def __init__(self, metrics_file='../data/tcp_baseline_metrics.json'):
        try:
            with open(metrics_file, 'r') as f:
                self.data = json.load(f)
            self.metrics = self.data.get('metrics', {})
            if not self.metrics:
                print(f"Warning: 'metrics' key not found in {metrics_file}")
                self.metrics = {
                    'packet_in': {},
                    'flow_mod': {},
                    'overhead': {}
                }
        except FileNotFoundError:
            print(f"Error: Metrics file not found at {metrics_file}")
            exit(1)
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from {metrics_file}")
            exit(1)
            
    def _analyze_latency_stats(self, latencies):
        """Helper function to calculate stats for a list of latencies"""
        if not latencies:
            return None
            
        stats = {
            'count': len(latencies),
            'mean': np.mean(latencies),
            'median': np.median(latencies),
            'std': np.std(latencies),
            'min': np.min(latencies),
            'max': np.max(latencies),
            'p95': np.percentile(latencies, 95),
            'p99': np.percentile(latencies, 99)
        }
        return stats

    def analyze_latency(self):
        """Analyze both packet-in and flow-mod latencies"""
        pi_latencies = self.metrics.get('packet_in', {}).get('latencies', [])
        fm_latencies = self.metrics.get('flow_mod', {}).get('latencies', [])
        
        all_stats = {}

        print("\n" + "=" * 70)
        print("TCP LATENCY ANALYSIS")
        print("=" * 70)
        
        if not pi_latencies and not fm_latencies:
            print("No latency data available")
            print("=" * 70 + "\n")
            return all_stats

        if pi_latencies:
            pi_stats = self._analyze_latency_stats(pi_latencies)
            all_stats['packet_in'] = pi_stats
            print("\n--- Packet-In to Flow-Mod Latency ---")
            print(f"Sample Count: {pi_stats['count']}")
            print(f"Mean:         {pi_stats['mean']:.3f} ms")
            print(f"Median:       {pi_stats['median']:.3f} ms")
            print(f"Std Dev:      {pi_stats['std']:.3f} ms")
            print(f"Min:          {pi_stats['min']:.3f} ms")
            print(f"Max:          {pi_stats['max']:.3f} ms")
            print(f"95th %ile:    {pi_stats['p95']:.3f} ms")
            print(f"99th %ile:    {pi_stats['p99']:.3f} ms")

        if fm_latencies:
            fm_stats = self._analyze_latency_stats(fm_latencies)
            all_stats['flow_mod'] = fm_stats
            print("\n--- Flow-Mod Send Time Latency ---")
            print(f"Sample Count: {fm_stats['count']}")
            print(f"Mean:         {fm_stats['mean']:.3f} ms")
            print(f"Median:       {fm_stats['median']:.3f} ms")
            print(f"Std Dev:      {fm_stats['std']:.3f} ms")
            print(f"Min:          {fm_stats['min']:.3f} ms")
            print(f"Max:          {fm_stats['max']:.3f} ms")
            print(f"95th %ile:    {fm_stats['p95']:.3f} ms")
            print(f"99th %ile:    {fm_stats['p99']:.3f} ms")
            
        print("=" * 70 + "\n")
        return all_stats
        
    def analyze_throughput(self):
        """Analyze message throughput"""
        pi_times = self.metrics.get('packet_in', {}).get('timestamps', [])
        fm_times = self.metrics.get('flow_mod', {}).get('timestamps', [])
        
        if not pi_times or not fm_times:
            print("\n" + "=" * 70)
            print("TCP THROUGHPUT ANALYSIS")
            print("=" * 70)
            print("No throughput data available")
            print("=" * 70 + "\n")
            return None
            
        # Calculate messages per second
        pi_duration = pi_times[-1] - pi_times[0] if len(pi_times) > 1 else 1
        fm_duration = fm_times[-1] - fm_times[0] if len(fm_times) > 1 else 1
        
        # Avoid division by zero if duration is too small
        pi_rate = len(pi_times) / pi_duration if pi_duration > 0 else 0
        fm_rate = len(fm_times) / fm_duration if fm_duration > 0 else 0
        
        print("\n" + "=" * 70)
        print("TCP THROUGHPUT ANALYSIS")
        print("=" * 70)
        print(f"Packet-In Rate:  {pi_rate:.2f} msg/sec")
        print(f"Flow-Mod Rate:   {fm_rate:.2f} msg/sec")
        print(f"Total Duration:  {max(pi_duration, fm_duration):.2f} seconds")
        print("=" * 70 + "\n")
        
        return {'packet_in_rate': pi_rate, 'flow_mod_rate': fm_rate}
        
    def analyze_overhead(self):
        """Analyze protocol overhead"""
        overhead_metrics = self.metrics.get('overhead', {})
        total_headers = overhead_metrics.get('total_headers', 0)
        total_payload = overhead_metrics.get('payload', 0)
        total_data = total_headers + total_payload
        
        if total_data == 0:
            print("\n" + "=" * 70)
            print("TCP OVERHEAD ANALYSIS")
            print("=" * 70)
            print("No overhead data available")
            print("=" * 70 + "\n")
            return None
            
        overhead_pct = (total_headers / total_data) * 100
        
        print("\n" + "=" * 70)
        print("TCP OVERHEAD ANALYSIS")
        print("=" * 70)
        print(f"TCP Headers:     {total_headers:,} bytes")
        print(f"Payload Data:    {total_payload:,} bytes")
        print(f"Total Data:      {total_data:,} bytes")
        print(f"Overhead:        {overhead_pct:.2f}%")
        print("=" * 70 + "\n")
        
        return {
            'headers': total_headers,
            'payload': total_payload,
            'overhead_pct': overhead_pct
        }
        
    def plot_latency_distribution(self, output_file='tcp_latency_dist.png'):
        """Plot latency distribution for both PacketIn and FlowMod"""
        pi_latencies = self.metrics.get('packet_in', {}).get('latencies', [])
        fm_latencies = self.metrics.get('flow_mod', {}).get('latencies', [])
        
        if not pi_latencies and not fm_latencies:
            print("No latency data to plot for distribution")
            return
            
        # Create a figure with 2 subplots (2 rows, 1 column)
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 12))
        fig.suptitle('TCP Baseline: Latency Distributions', fontsize=16, y=1.02)
        
        # Plot 1: Packet-In to Flow-Mod Latency
        if pi_latencies:
            ax1.hist(pi_latencies, bins=50, edgecolor='black', alpha=0.7, color='blue')
            ax1.set_xlabel('Latency (ms)')
            ax1.set_ylabel('Frequency')
            ax1.set_title('Packet-In to Flow-Mod Latency')
            ax1.grid(True, alpha=0.3)
        else:
            ax1.text(0.5, 0.5, 'No Packet-In Latency Data', horizontalalignment='center', verticalalignment='center', transform=ax1.transAxes)
            ax1.set_title('Packet-In to Flow-Mod Latency')

        # Plot 2: Flow-Mod Send Time Latency
        if fm_latencies:
            ax2.hist(fm_latencies, bins=50, edgecolor='black', alpha=0.7, color='green')
            ax2.set_xlabel('Latency (ms)')
            ax2.set_ylabel('Frequency')
            ax2.set_title('Flow-Mod Send Time Latency')
            ax2.grid(True, alpha=0.3)
        else:
            ax2.text(0.5, 0.5, 'No Flow-Mod Latency Data', horizontalalignment='center', verticalalignment='center', transform=ax2.transAxes)
            ax2.set_title('Flow-Mod Send Time Latency')
            
        plt.tight_layout(rect=[0, 0.03, 1, 0.98]) # Adjust layout to prevent title overlap
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Latency distribution plot saved to {output_file}")
        plt.close(fig) # Close the figure to free memory
        
    def plot_latency_cdf(self, output_file='tcp_latency_cdf.png'):
        """Plot latency CDF for both PacketIn and FlowMod"""
        pi_latencies = np.sort(self.metrics.get('packet_in', {}).get('latencies', []))
        fm_latencies = np.sort(self.metrics.get('flow_mod', {}).get('latencies', []))

        if len(pi_latencies) == 0 and len(fm_latencies) == 0:
            print("No latency data to plot for CDF")
            return
            
        # Create a figure with 2 subplots (2 rows, 1 column)
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 12))
        fig.suptitle('TCP Baseline: Latency Cumulative Distribution (CDF)', fontsize=16, y=1.02)

        # Plot 1: Packet-In to Flow-Mod CDF
        if len(pi_latencies) > 0:
            cdf_pi = np.arange(1, len(pi_latencies) + 1) / len(pi_latencies)
            ax1.plot(pi_latencies, cdf_pi, linewidth=2, color='blue')
            ax1.set_xlabel('Latency (ms)')
            ax1.set_ylabel('CDF')
            ax1.set_title('Packet-In to Flow-Mod Latency CDF')
            ax1.grid(True, alpha=0.3)
            ax1.set_ylim(0, 1) # CDF y-axis is always 0 to 1
        else:
            ax1.text(0.5, 0.5, 'No Packet-In Latency Data', horizontalalignment='center', verticalalignment='center', transform=ax1.transAxes)
            ax1.set_title('Packet-In to Flow-Mod Latency CDF')

        # Plot 2: Flow-Mod Send Time CDF
        if len(fm_latencies) > 0:
            cdf_fm = np.arange(1, len(fm_latencies) + 1) / len(fm_latencies)
            ax2.plot(fm_latencies, cdf_fm, linewidth=2, color='green')
            ax2.set_xlabel('Latency (ms)')
            ax2.set_ylabel('CDF')
            ax2.set_title('Flow-Mod Send Time Latency CDF')
            ax2.grid(True, alpha=0.3)
            ax2.set_ylim(0, 1) # CDF y-axis is always 0 to 1
        else:
            ax2.text(0.5, 0.5, 'No Flow-Mod Latency Data', horizontalalignment='center', verticalalignment='center', transform=ax2.transAxes)
            ax2.set_title('Flow-Mod Send Time Latency CDF')
            
        plt.tight_layout(rect=[0, 0.03, 1, 0.98]) # Adjust layout
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Latency CDF plot saved to {output_file}")
        plt.close(fig) # Close the figure to free memory
        
    def generate_report(self, output_file='../results/tcp_baseline_report.txt'):
        """Generate comprehensive performance report"""
        with open(output_file, 'w') as f:
            f.write("=" * 70 + "\n")
            f.write("TCP BASELINE PERFORMANCE REPORT\n")
            f.write("=" * 70 + "\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n")
            f.write(f"Protocol: TCP\n")
            f.write(f"Controller: Ryu\n")
            f.write(f"OpenFlow: 1.3\n")
            f.write("=" * 70 + "\n\n")
            
            # Latency stats
            # Note: analyze_latency() already prints to console
            lat_stats_dict = self.analyze_latency()
            
            # Write Packet-In Latency to report
            if 'packet_in' in lat_stats_dict:
                f.write("LATENCY STATISTICS (Packet-In to Flow-Mod)\n")
                f.write("-" * 70 + "\n")
                for key, value in lat_stats_dict['packet_in'].items():
                    if isinstance(value, float):
                        f.write(f"{key:12s}: {value:.3f} ms\n")
                    else:
                        f.write(f"{key:12s}: {value}\n")
                f.write("\n")
            
            # Write Flow-Mod Latency to report
            if 'flow_mod' in lat_stats_dict:
                f.write("LATENCY STATISTICS (Flow-Mod Send Time)\n")
                f.write("-" * 70 + "\n")
                for key, value in lat_stats_dict['flow_mod'].items():
                    if isinstance(value, float):
                        f.write(f"{key:12s}: {value:.3f} ms\n")
                    else:
                        f.write(f"{key:12s}: {value}\n")
                f.write("\n")

            if not lat_stats_dict:
                f.write("LATENCY STATISTICS\n")
                f.write("-" * 70 + "\n")
                f.write("No latency data available\n\n")
                
            # Throughput stats
            tp_stats = self.analyze_throughput()
            if tp_stats:
                f.write("THROUGHPUT STATISTICS\n")
                f.write("-" * 70 + "\n")
                for key, value in tp_stats.items():
                    f.write(f"{key:20s}: {value:.2f} msg/sec\n")
                f.write("\n")
            else:
                f.write("THROUGHPUT STATISTICS\n")
                f.write("-" * 70 + "\n")
                f.write("No throughput data available\n\n")
                
            # Overhead stats
            oh_stats = self.analyze_overhead()
            if oh_stats:
                f.write("OVERHEAD STATISTICS\n")
                f.write("-" * 70 + "\n")
                f.write(f"Headers:  {oh_stats['headers']:,} bytes\n")
                f.write(f"Payload:  {oh_stats['payload']:,} bytes\n")
                f.write(f"Overhead: {oh_stats['overhead_pct']:.2f}%\n")
            else:
                f.write("OVERHEAD STATISTICS\n")
                f.write("-" * 70 + "\n")
                f.write("No overhead data available\n\n")
                
        print(f"Report saved to {output_file}")

def main():
    analyzer = TCPPerformanceAnalyzer()
    
    # Run all analyses (they will print to console)
    analyzer.analyze_latency()
    analyzer.analyze_throughput()
    analyzer.analyze_overhead()
    
    # Generate plots
    analyzer.plot_latency_distribution()
    analyzer.plot_latency_cdf()
    
    # Generate final report file
    analyzer.generate_report()

if __name__ == '__main__':
    main()
