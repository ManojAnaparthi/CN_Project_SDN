# File: test_topology_tcp.py
"""
Comprehensive test topology for TCP baseline performance measurement
"""

from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink
import time

class TCPTestTopology:
    """Test topology for TCP baseline measurements"""
    
    def __init__(self):
        self.net = None
        
    def create_topology(self):
        """Create multi-switch topology for testing"""
        info('*** Creating TCP Test Topology\n')
        
        self.net = Mininet(
            controller=RemoteController,
            switch=OVSSwitch,
            link=TCLink,
            autoSetMacs=True,
            autoStaticArp=False
        )
        
        # Add controller
        info('*** Adding controller\n')
        c0 = self.net.addController(
            'c0',
            controller=RemoteController,
            ip='127.0.0.1',
            port=6633
        )
        
        # Add switches
        info('*** Adding switches\n')
        s1 = self.net.addSwitch('s1', protocols='OpenFlow13')
        s2 = self.net.addSwitch('s2', protocols='OpenFlow13')
        s3 = self.net.addSwitch('s3', protocols='OpenFlow13')
        
        # Add hosts
        info('*** Adding hosts\n')
        h1 = self.net.addHost('h1', ip='10.0.0.1/24')
        h2 = self.net.addHost('h2', ip='10.0.0.2/24')
        h3 = self.net.addHost('h3', ip='10.0.0.3/24')
        h4 = self.net.addHost('h4', ip='10.0.0.4/24')
        
        # Add links with bandwidth and delay constraints
        info('*** Adding links\n')
        self.net.addLink(h1, s1, bw=100, delay='5ms')
        self.net.addLink(h2, s1, bw=100, delay='5ms')
        self.net.addLink(h3, s2, bw=100, delay='5ms')
        self.net.addLink(h4, s3, bw=100, delay='5ms')
        
        # Inter-switch links
        self.net.addLink(s1, s2, bw=100, delay='10ms')
        self.net.addLink(s2, s3, bw=100, delay='10ms')
        #self.net.addLink(s1, s3, bw=100, delay='10ms')
        
        return self.net
        
    def run_tests(self):
        """Run comprehensive TCP tests"""
        info('*** Starting network\n')
        self.net.start()
        
        info('*** Waiting for controller connection\n')
        time.sleep(5)
        
        info('\n*** Running TCP Baseline Tests ***\n')
        info('=' * 70 + '\n')
        
        # Test 1: Connectivity
        info('\n[TEST 1] Basic Connectivity Test\n')
        self.net.pingAll()
        
        # Test 2: Latency measurement
        info('\n[TEST 2] Latency Measurement (h1 -> h2)\n')
        h1, h2 = self.net.get('h1', 'h2')
        result = h1.cmd(f'ping -c 100 {h2.IP()}')
        info(result)
        
        # Test 3: Bandwidth measurement
        info('\n[TEST 3] Bandwidth Measurement (h1 <-> h3)\n')
        h1, h3 = self.net.get('h1', 'h3')
        info('*** Starting iperf server on h3\n')
        h3.cmd('iperf -s &')
        time.sleep(2)
        
        info('*** Running iperf client on h1\n')
        result = h1.cmd(f'iperf -c {h3.IP()} -t 30')
        info(result)
        
        # Test 4: Multiple concurrent flows
        info('\n[TEST 4] Multiple Concurrent Flows\n')
        h1, h2, h3, h4 = self.net.get('h1', 'h2', 'h3', 'h4')
        
        h2.cmd('iperf -s &')
        h4.cmd('iperf -s &')
        time.sleep(2)
        
        h1.cmd(f'iperf -c {h2.IP()} -t 20 &')
        h3.cmd(f'iperf -c {h4.IP()} -t 20 &')
        time.sleep(25)
        
        info('\n*** Tests completed ***\n')
        info('=' * 70 + '\n')
        
        # Open CLI for manual testing
        CLI(self.net)
        
    def stop(self):
        """Stop network"""
        if self.net:
            info('*** Stopping network\n')
            self.net.stop()

def main():
    setLogLevel('info')
    
    topology = TCPTestTopology()
    topology.create_topology()
    
    try:
        topology.run_tests()
    except KeyboardInterrupt:
        info('\n*** Interrupted by user\n')
    finally:
        topology.stop()

if __name__ == '__main__':
    main()
