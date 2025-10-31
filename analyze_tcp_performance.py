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
    
    def __init__(self, metrics_file='tcp_baseline_metrics.json'):
        with open(metrics_file, 'r') as f:
            self.data = json.load(f)
        self.metrics = self.data['metrics']
        
    def analyze_latency(self):
        """Analyze packet-in to flow-mod latency"""
        latencies = self.metrics['packet_in']['latencies']
        
        if not latencies:
            print("No latency data available")
            return
            
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
        
        print("\n" + "=" * 70)
        print("TCP LATENCY ANALYSIS (Packet-In to Flow-Mod)")
        print("=" * 70)
        print(f"Sample Count: {stats['count']}")
        print(f"Mean:         {stats['mean']:.3f} ms")
        print(f"Median:       {stats['median']:.3f} ms")
        print(f"Std Dev:      {stats['std']:.3f} ms")
        print(f"Min:          {stats['min']:.3f} ms")
        print(f"Max:          {stats['max']:.3f} ms")
        print(f"95th %ile:    {stats['p95']:.3f} ms")
        print(f"99th %ile:    {stats['p99']:.3f} ms")
        print("=" * 70 + "\n")
        
        return stats
        
    def analyze_throughput(self):
        """Analyze message throughput"""
        pi_times = self.metrics['packet_in']['timestamps']
        fm_times = self.metrics['flow_mod']['timestamps']
        
        if not pi_times or not fm_times:
            print("No throughput data available")
            return
            
        # Calculate messages per second
        pi_duration = pi_times[-1] - pi_times[0] if len(pi_times) > 1 else 1
        fm_duration = fm_times[-1] - fm_times[0] if len(fm_times) > 1 else 1
        
        pi_rate = len(pi_times) / pi_duration
        fm_rate = len(fm_times) / fm_duration
        
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
        total_headers = self.metrics['overhead']['total_headers']
        total_payload = self.metrics['overhead']['payload']
        total_data = total_headers + total_payload
        
        if total_data == 0:
            print("No overhead data available")
            return
            
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
        """Plot latency distribution"""
        latencies = self.metrics['packet_in']['latencies']
        
        if not latencies:
            print("No latency data to plot")
            return
            
        plt.figure(figsize=(10, 6))
        plt.hist(latencies, bins=50, edgecolor='black', alpha=0.7)
        plt.xlabel('Latency (ms)')
        plt.ylabel('Frequency')
        plt.title('TCP Baseline: Packet-In to Flow-Mod Latency Distribution')
        plt.grid(True, alpha=0.3)
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Latency distribution plot saved to {output_file}")
        
    def plot_latency_cdf(self, output_file='tcp_latency_cdf.png'):
        """Plot latency CDF"""
        latencies = np.sort(self.metrics['packet_in']['latencies'])
        
        if len(latencies) == 0:
            print("No latency data to plot")
            return
            
        cdf = np.arange(1, len(latencies) + 1) / len(latencies)
        
        plt.figure(figsize=(10, 6))
        plt.plot(latencies, cdf, linewidth=2)
        plt.xlabel('Latency (ms)')
        plt.ylabel('CDF')
        plt.title('TCP Baseline: Latency Cumulative Distribution')
        plt.grid(True, alpha=0.3)
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Latency CDF plot saved to {output_file}")
        
    def generate_report(self, output_file='tcp_baseline_report.txt'):
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
            lat_stats = self.analyze_latency()
            if lat_stats:
                f.write("LATENCY STATISTICS\n")
                f.write("-" * 70 + "\n")
                for key, value in lat_stats.items():
                    if isinstance(value, float):
                        f.write(f"{key:12s}: {value:.3f} ms\n")
                    else:
                        f.write(f"{key:12s}: {value}\n")
                f.write("\n")
                
            # Throughput stats
            tp_stats = self.analyze_throughput()
            if tp_stats:
                f.write("THROUGHPUT STATISTICS\n")
                f.write("-" * 70 + "\n")
                for key, value in tp_stats.items():
                    f.write(f"{key:20s}: {value:.2f} msg/sec\n")
                f.write("\n")
                
            # Overhead stats
            oh_stats = self.analyze_overhead()
            if oh_stats:
                f.write("OVERHEAD STATISTICS\n")
                f.write("-" * 70 + "\n")
                f.write(f"Headers:  {oh_stats['headers']:,} bytes\n")
                f.write(f"Payload:  {oh_stats['payload']:,} bytes\n")
                f.write(f"Overhead: {oh_stats['overhead_pct']:.2f}%\n")
                
        print(f"Report saved to {output_file}")

def main():
    analyzer = TCPPerformanceAnalyzer()
    
    # Run all analyses
    analyzer.analyze_latency()
    analyzer.analyze_throughput()
    analyzer.analyze_overhead()
    
    # Generate plots
    analyzer.plot_latency_distribution()
    analyzer.plot_latency_cdf()
    
    # Generate report
    analyzer.generate_report()

if __name__ == '__main__':
    main()
