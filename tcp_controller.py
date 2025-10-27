from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ether_types
import time

class TCPOpenFlowTester(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    
    def __init__(self, *args, **kwargs):
        super(TCPOpenFlowTester, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.packet_in_count = 0
        self.packet_out_count = 0
        self.flow_mod_count = 0
        self.latencies = []
        
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        """Handle initial TCP connection and switch features"""
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        
        self.logger.info("="*60)
        self.logger.info("TCP CONNECTION ESTABLISHED")
        self.logger.info("Switch DPID: %s", datapath.id)
        self.logger.info("OpenFlow Version: %s", ofproto.OFP_VERSION)
        self.logger.info("TCP Port: 6653")
        self.logger.info("="*60)
        
        # Install table-miss flow entry
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)
        
    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        """Add flow entry and log TCP transmission"""
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match, instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst)
        
        self.flow_mod_count += 1
        self.logger.info("[TCP-TX] FlowMod #%d sent", self.flow_mod_count)
        datapath.send_msg(mod)
        
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        """Handle Packet_in messages arriving via TCP"""
        start_time = time.time()
        
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']
        
        self.packet_in_count += 1
        
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]
        
        dst = eth.dst
        src = eth.src
        dpid = datapath.id
        
        self.logger.info("[TCP-RX] Packet_in #%d", self.packet_in_count)
        self.logger.info("  Switch: %s, Port: %s", dpid, in_port)
        self.logger.info("  Src MAC: %s -> Dst MAC: %s", src, dst)
        self.logger.info("  Buffer ID: %s, Total Length: %s bytes", 
                        msg.buffer_id, msg.total_len)
        
        # Learning switch logic
        self.mac_to_port.setdefault(dpid, {})
        self.mac_to_port[dpid][src] = in_port
        
        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD
            
        actions = [parser.OFPActionOutput(out_port)]
        
        # Install flow to avoid packet_in next time
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_src=src)
            if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                self.add_flow(datapath, 1, match, actions, msg.buffer_id)
                latency = time.time() - start_time
                self.latencies.append(latency)
                self.logger.info("  Processing latency: %.6f ms", latency * 1000)
                return
            else:
                self.add_flow(datapath, 1, match, actions)
                
        # Send packet_out
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data
            
        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        
        self.packet_out_count += 1
        self.logger.info("[TCP-TX] Packet_out #%d to port %s", 
                        self.packet_out_count, out_port)
        
        datapath.send_msg(out)
        
        latency = time.time() - start_time
        self.latencies.append(latency)
        self.logger.info("  Total processing latency: %.6f ms", latency * 1000)
        
    @set_ev_cls(ofp_event.EventOFPPortStatus, MAIN_DISPATCHER)
    def port_status_handler(self, ev):
        """Handle port status change messages"""
        msg = ev.msg
        reason = msg.reason
        port_no = msg.desc.port_no
        
        ofproto = msg.datapath.ofproto
        if reason == ofproto.OFPPR_ADD:
            self.logger.info("[TCP-RX] Port %s ADDED", port_no)
        elif reason == ofproto.OFPPR_DELETE:
            self.logger.info("[TCP-RX] Port %s DELETED", port_no)
        elif reason == ofproto.OFPPR_MODIFY:
            self.logger.info("[TCP-RX] Port %s MODIFIED", port_no)