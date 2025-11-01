# TCP Baseline (Phase 1 & 2 Complete)

TCP baseline implementation, performance analysis, and architecture study.

## Structure

```
tcp_baseline/
├── controllers/          # Ryu controller implementations
├── analysis/             # Analysis and visualization scripts
├── data/                 # Raw data (metrics, logs, pcap)
├── results/              # Generated reports and visualizations
└── topology/             # Mininet network topologies
```

## Quick Start

### 1. Run TCP Baseline Test

**Terminal 1** - Start Controller:
```bash
cd controllers
ryu-manager tcp_baseline_instrumented.py --verbose
```

**Terminal 2** - Run Test Topology:
```bash
cd topology
sudo python test_topology_tcp.py
```

### 2. Generate Visualization

```bash
cd analysis
python3 visualize_metrics.py
# Output: results/tcp_baseline_performance.png
```

## Files

### Controllers
- `tcp_baseline_controller.py` - Basic L2 learning switch
- `tcp_baseline_instrumented.py` - Enhanced with metrics collection (338 lines)

### Analysis
- `visualize_metrics.py` - Performance visualization (176 lines)
- `analyze_tcp_performance.py` - Statistical analysis
- `analyze_ryu_tcp.py` - Ryu-specific analysis

### Data (67 MB total)
- `tcp_baseline_metrics.json` - Raw performance data (7.1 MB, 94,423 events)
- `tcp_baseline.pcap` - Packet capture (46 KB)
- `tcp_baseline.log` - Controller logs (60 MB)
- `ryu_tcp_analysis.txt` - Analysis summary

### Results
- `tcp_baseline_performance.png` - 3-panel visualization (379 KB)
- `tcp_baseline_report.txt` - Performance summary

### Topology
- `test_topology_tcp.py` - 3-switch, 4-host test topology
- `basic_topo.py` - Simple single-switch topology

## Performance Summary

```
Duration:         37.38 seconds
Total Messages:   94,423
Throughput:       2,526 msg/sec
Mean Latency:     1.973 ms
P95 Latency:      8.805 ms
Max Message Size: 218 bytes
UDP Compatible:   ✅ YES (99.7% safety margin)
```

See main [README.md](../README.md) for complete documentation.
