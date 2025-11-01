# File: tcp_baseline_instrumented.py
"""
Comprehensive TCP Baseline Controller with Performance Instrumentation
Measures: latency, throughput, message rates, connection overhead
"""

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ether_types
import time
import json
import threading
from collections import defaultdict
from datetime import datetime

class TCPBaselineInstrumented(app_manager.RyuApp):
    """
    L2 Learning Switch with comprehensive TCP performance metrics
    """
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    
    def __init__(self, *args, **kwargs):
        super(TCPBaselineInstrumented, self).__init__(*args, **kwargs)
        
        # MAC learning table
        self.mac_to_port = {}
        
        # Performance metrics
        self.metrics = {
            'packet_in': {
                'count': 0,
                'timestamps': [],
                'sizes': [],
                'latencies': []
            },
            'flow_mod': {
                'count': 0,
                'timestamps': [],
                'sizes': [],
                'latencies': []
            },
            'packet_out': {
                'count': 0,
                'timestamps': [],
                'sizes': []
            },
            'hello': {
                'count': 0,
                'timestamps': [],
                'sizes': []
            },
            'features_request': {
                'count': 0,
                'timestamps': [],
                'sizes': []
            },
            'features_reply': {
                'count': 0,
                'timestamps': [],
                'sizes': []
            },
            'echo_request': {
                'count': 0,
                'timestamps': [],
                'sizes': []
            },
            'echo_reply': {
                'count': 0,
                'timestamps': [],
                'sizes': []
            },
            'connection': {
                'established': [],
                'establishment_times': [],
                'active_connections': 0
            },
            'overhead': {
                'tcp_header_bytes': 0,
                'ip_header_bytes': 0,
                'ethernet_header_bytes': 0,
                'total_payload_bytes': 0
            }
        }
        
        # Controller start time for connection establishment tracking
        self.start_time = time.time()
        self.first_message_time = None
        
        # Timing trackers
        self.packet_in_times = {}  # Track when packet_in arrives
        
        # Connection tracking
        self.datapaths = {}
        
        # Start metrics collection thread
        self.running = True
        self.metrics_thread = threading.Thread(target=self._metrics_collector)
        self.metrics_thread.daemon = True
        self.metrics_thread.start()
        
        self.logger.info("=" * 70)
        self.logger.info("TCP BASELINE INSTRUMENTED CONTROLLER STARTED")
        self.logger.info("=" * 70)
        
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        """Handle switch connection and install table-miss flow"""
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        dpid = datapath.id
        
        # Track connection establishment
        conn_time = time.time()
        
        # Track first message time (connection establishment time)
        if self.first_message_time is None:
            self.first_message_time = conn_time
            establishment_time = (conn_time - self.start_time) * 1000  # ms
            self.metrics['connection']['establishment_times'].append(establishment_time)
            self.logger.info(f"[CONNECTION] First message after {establishment_time:.2f}ms")
        
        self.metrics['connection']['established'].append({
            'dpid': dpid,
            'timestamp': conn_time,
            'datetime': datetime.fromtimestamp(conn_time).isoformat()
        })
        self.metrics['connection']['active_connections'] += 1
        
        # Track features_reply message size
        msg_size = len(ev.msg.buf) if hasattr(ev.msg, 'buf') else 0
        self.metrics['features_reply']['count'] += 1
        self.metrics['features_reply']['timestamps'].append(conn_time)
        self.metrics['features_reply']['sizes'].append(msg_size)
        
        # Store datapath
        self.datapaths[dpid] = datapath
        
        self.logger.info(f"[CONNECTION] Switch {dpid:#x} connected at {datetime.now()}")
        self.logger.info(f"  • Active connections: {self.metrics['connection']['active_connections']}")
        self.logger.info(f"  • Features reply size: {msg_size} bytes")
        
        # Install table-miss flow entry (send to controller)
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                         ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)
        
    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        """Add flow entry to switch"""
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                            actions)]
        


        # Create flow mod message
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                   priority=priority, match=match,
                                   instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                   match=match, instructions=inst)
        
        # Record metrics BEFORE sending
        start_time = time.time()
        datapath.send_msg(mod)
        msg_size = len(getattr(mod, 'buf', b'')) if getattr(mod, 'buf', None) else 64

        # Record metrics AFTER sending
        end_time = time.time()
        latency = (end_time - start_time) * 1000  # milliseconds
        
        # Update metrics
        self.metrics['flow_mod']['count'] += 1
        self.metrics['flow_mod']['timestamps'].append(end_time)
        self.metrics['flow_mod']['sizes'].append(msg_size)
        self.metrics['flow_mod']['latencies'].append(latency)
        
        # Update overhead calculation
        self.metrics['overhead']['total_headers'] += 20  # TCP header
        self.metrics['overhead']['payload'] += msg_size
        
        self.logger.debug(f"[FLOW_MOD] Sent to {datapath.id:#x}, "
                         f"size={msg_size}B, latency={latency:.3f}ms")
        
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        """Handle packet-in messages from switch"""
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']
        dpid = datapath.id
        
        # Record packet-in arrival time
        arrival_time = time.time()
        
        # Parse packet
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]
        
        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            # Ignore LLDP packets
            return
            
        dst = eth.dst
        src = eth.src
        
        # Record metrics
        msg_size = len(msg.data)
        self.metrics['packet_in']['count'] += 1
        self.metrics['packet_in']['timestamps'].append(arrival_time)
        self.metrics['packet_in']['sizes'].append(msg_size)
        
        # Update overhead
        self.metrics['overhead']['total_headers'] += 20  # TCP header
        self.metrics['overhead']['payload'] += msg_size
        
        self.logger.debug(f"[PACKET_IN] From {dpid:#x} port {in_port}, "
                         f"src={src} dst={dst}, size={msg_size}B")
        
        # Learn MAC address
        self.mac_to_port.setdefault(dpid, {})
        self.mac_to_port[dpid][src] = in_port
        
        # Determine output port
        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD
            
        actions = [parser.OFPActionOutput(out_port)]
        
        # Install flow to avoid packet_in next time
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_src=src)
            
            # Verify if we have a valid buffer_id
            if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                self.add_flow(datapath, 1, match, actions, msg.buffer_id)
                
                # Calculate end-to-end latency (packet_in to flow_mod)
                flow_install_time = time.time()
                e2e_latency = (flow_install_time - arrival_time) * 1000
                self.metrics['packet_in']['latencies'].append(e2e_latency)
                
                self.logger.debug(f"  → Flow installed, e2e_latency={e2e_latency:.3f}ms")
                return
            else:
                self.add_flow(datapath, 1, match, actions)
        
        # Send packet out
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data
            
        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        
        # Record packet-out metrics
        if out is not None and hasattr(out, 'buf') and out.buf is not None:
            out_size = len(out.buf)
        else:
            out_size = 0
        self.metrics['packet_out']['count'] += 1
        self.metrics['packet_out']['timestamps'].append(time.time())
        self.metrics['packet_out']['sizes'].append(out_size)
        
        datapath.send_msg(out)
        
        # Calculate latency if flow was installed
        if out_port != ofproto.OFPP_FLOOD:
            complete_time = time.time()
            e2e_latency = (complete_time - arrival_time) * 1000
            self.metrics['packet_in']['latencies'].append(e2e_latency)
            self.logger.debug(f"  → Packet sent, e2e_latency={e2e_latency:.3f}ms")
            
    def _metrics_collector(self):
        """Background thread to periodically log metrics"""
        while self.running:
            time.sleep(30)  # Log every 30 seconds
            self._log_metrics_summary()
            
    def _log_metrics_summary(self):
        """Log current metrics summary"""
        self.logger.info("\n" + "=" * 70)
        self.logger.info("TCP BASELINE METRICS SUMMARY")
        self.logger.info("=" * 70)
        
        # Packet-In stats
        pi_count = self.metrics['packet_in']['count']
        pi_latencies = self.metrics['packet_in']['latencies']
        
        self.logger.info(f"[PACKET-IN]")
        self.logger.info(f"  • Total Count: {pi_count}")
        if pi_latencies:
            self.logger.info(f"  • Avg Latency: {sum(pi_latencies)/len(pi_latencies):.3f} ms")
            self.logger.info(f"  • Min Latency: {min(pi_latencies):.3f} ms")
            self.logger.info(f"  • Max Latency: {max(pi_latencies):.3f} ms")
            
        # Flow-Mod stats
        fm_count = self.metrics['flow_mod']['count']
        fm_latencies = self.metrics['flow_mod']['latencies']
        
        self.logger.info(f"\n[FLOW-MOD]")
        self.logger.info(f"  • Total Count: {fm_count}")
        if fm_latencies:
            self.logger.info(f"  • Avg Latency: {sum(fm_latencies)/len(fm_latencies):.3f} ms")
            
        # Overhead stats
        total_headers = self.metrics['overhead']['total_headers']
        total_payload = self.metrics['overhead']['payload']
        total_data = total_headers + total_payload
        overhead_pct = (total_headers / total_data * 100) if total_data > 0 else 0
        
        self.logger.info(f"\n[OVERHEAD]")
        self.logger.info(f"  • TCP Headers: {total_headers} bytes")
        self.logger.info(f"  • Payload: {total_payload} bytes")
        self.logger.info(f"  • Overhead: {overhead_pct:.2f}%")
        
        self.logger.info("=" * 70 + "\n")
        
    def save_metrics(self, filename='../data/tcp_baseline_metrics.json'):
        """Save metrics to JSON file"""
        output = {
            'metadata': {
                'protocol': 'TCP',
                'controller': 'Ryu',
                'openflow_version': '1.3',
                'timestamp': datetime.now().isoformat()
            },
            'metrics': self.metrics
        }
        
        with open(filename, 'w') as f:
            json.dump(output, f, indent=2)
            
        self.logger.info(f"Metrics saved to {filename}")
        
    def stop(self):
        """Cleanup on shutdown"""
        self.running = False
        self.save_metrics()
        self.logger.info("Controller stopped, metrics saved")
