# File: basic_topo.py
from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel

def simple_topology():
    net = Mininet(controller=RemoteController, switch=OVSSwitch)
    
    # Add controller
    c0 = net.addController('c0', controller=RemoteController, 
                           ip='127.0.0.1', port=6633)
    
    # Add switches
    s1 = net.addSwitch('s1', protocols='OpenFlow13')
    s2 = net.addSwitch('s2', protocols='OpenFlow13')
    
    # Add hosts
    h1 = net.addHost('h1')
    h2 = net.addHost('h2')
    h3 = net.addHost('h3')
    
    # Add links
    net.addLink(h1, s1)
    net.addLink(h2, s2)
    net.addLink(h3, s2)
    net.addLink(s1, s2)
    
    net.start()
    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    simple_topology()
