#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trabalho SDN 01 — Descoberta de Topologias de Rede com Mininet e Ryu
Programa de Pós-Graduação em Informática (PPCOMP) — IFES Campus Serra
Autores: Alan Saar e Leonardo Herkenhoff

Módulo: topo_discover.py
Descrição:
    Aplicação controladora desenvolvida no framework Ryu operando sobre OpenFlow 1.3.
    Responsável pela descoberta e mapeamento dinâmico da topologia física e dos hosts:
      1. Descoberta de switches e enlaces inter-switch via pacotes LLDP injetados pelo
         módulo de topologia do Ryu (ativado com a flag '--observe-links').
      2. Descoberta passiva de hosts através da interceptação de pacotes Gratuitous ARP (GARP)
         desviados para o controlador via OpenFlow Packet-In.
      3. Consolidação e exibição em tempo real da topologia da rede no console.

Analogia Pedagógica ("O Galpão e os Funcionários"):
    - O Controlador Ryu representa o Gerente Geral sentado na central de monitoramento.
    - Cada switch OVS representa um funcionário (ex: Luiz no Switch 1, Flávio no Switch 2)
      em uma sala de triagem com portas numeradas, sem autonomia para rotear.
    - A flag '--observe-links' acorda a equipe de mensageiros do Ryu, que injeta bilhetinhos
      coloridos (pacotes LLDP) pelas portas para que Luiz jogue no tubo e Flávio receba
      e avise o Gerente (OFP Packet-In).
    - O Gratuitous ARP é o cartão de visitas entregue pelo visitante (Host) na recepção
      de uma sala, que o funcionário imediatamente encaminha ao Gerente para cadastro.
"""

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.topology import event
from ryu.topology.api import get_switch, get_link
from ryu.lib.packet import packet, arp, ethernet


class TopoDiscover(app_manager.RyuApp):
    """
    Controlador Ryu para Descoberta Dinâmica de Topologias SDN.
    Opera estritamente sob a especificação OpenFlow versão 1.3.
    """
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(TopoDiscover, self).__init__(*args, **kwargs)
        # Referência da aplicação para consulta nas APIs de topologia do Ryu
        self.topology_api_app = self

        # Estruturas de dados internas para consolidação do grafo da rede:
        # self.switches: Lista de DPIDs (Datapath IDs) dos switches ativos
        self.switches = []
        # self.links: Lista de tuplas com enlaces direcionados (src_dpid, dst_dpid, src_port, dst_port)
        self.links = []
        # self.hosts: Dicionário mapeando IP do host -> {'mac': mac, 'dpid': dpid, 'port': in_port}
        self.hosts = {}

        # Contador de atualizações da topologia para log limpo
        self.topology_version = 0

    # =========================================================================
    # 1. Fase de Handshake e Instalação da Regra Table-Miss (OpenFlow 1.3)
    # =========================================================================
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        """
        Tratador disparado quando um switch conclui o handshake inicial com o controlador
        e responde com suas funcionalidades (OFPT_FEATURES_REPLY).

        Conceito Pedagógico:
            No OpenFlow 1.3, o comportamento padrão dos switches para pacotes que não dão match
            em nenhuma regra é descartá-los (drop), a menos que instalemos explicitamente a regra
            de prioridade 0 chamada 'Table-Miss Flow Entry'.
            Esta regra instrui o switch a desviar qualquer pacote não conhecido diretamente
            para o controlador através de uma mensagem Packet-In.
        """
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Cria uma regra de match vazia (corresponde a absolutamente qualquer pacote)
        match = parser.OFPMatch()

        # Define a ação: enviar o pacote integral ao controlador sem truncamento de buffer
        actions = [
            parser.OFPActionOutput(
                ofproto.OFPP_CONTROLLER,
                ofproto.OFPCML_NO_BUFFER
            )
        ]

        # Instala a regra Table-Miss na tabela 0 com a menor prioridade possível (0)
        self.add_flow(datapath, priority=0, match=match, actions=actions)

        # Regra explícita de alta prioridade para interceptar pacotes ARP (Gratuitous ARP / Request / Reply)
        # Garante que qualquer tráfego ARP seja desviado diretamente ao controlador para descoberta de hosts
        match_arp = parser.OFPMatch(eth_type=0x0806)
        self.add_flow(datapath, priority=10, match=match_arp, actions=actions)

        self.logger.info("[Handshake] Switch s%s conectado. Regras Table-Miss e ARP intercept instaladas.", datapath.id)

    def add_flow(self, datapath, priority, match, actions):
        """
        Função auxiliar para instalação de regras na Flow Table do switch via OFPFlowMod.
        """
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Instrução que aplica as ações imediatamente
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(
            datapath=datapath,
            priority=priority,
            match=match,
            instructions=inst
        )
        datapath.send_msg(mod)

    # =========================================================================
    # 2. Descoberta de Switches e Enlaces Inter-Switch (LLDP)
    # =========================================================================
    @set_ev_cls(event.EventSwitchEnter)
    def _event_switch_enter_handler(self, ev):
        """
        Disparado quando um novo switch é detectado pelo subsistema de topologia do Ryu.
        """
        switch_list = get_switch(self.topology_api_app, None)
        novos_switches = sorted([switch.dp.id for switch in switch_list])

        if novos_switches != self.switches:
            self.switches = novos_switches
            self.logger.info("[Topologia] Switches ativos atualizados: %s (Total: %d)",
                             [f"s{dpid}" for dpid in self.switches], len(self.switches))
            self.print_full_topology()

    @set_ev_cls(event.EventLinkAdd)
    def _event_link_add_handler(self, ev):
        """
        Disparado quando um novo enlace inter-switch é comprovado através da recepção
        de pacotes LLDP gerados pelo Ryu com a flag '--observe-links'.
        """
        link_list = get_link(self.topology_api_app, None)
        novos_links = [
            (link.src.dpid, link.dst.dpid, link.src.port_no, link.dst.port_no)
            for link in link_list
        ]

        if set(novos_links) != set(self.links):
            self.links = novos_links
            self.logger.info("[Topologia] Novo enlace comprovado via LLDP! Total de enlaces unidirecionais: %d",
                             len(self.links))
            self.print_full_topology()

    # =========================================================================
    # 3. Descoberta de Hosts via Gratuitous ARP (Packet-In)
    # =========================================================================
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        """
        Intercepta pacotes enviados pelos switches para o controlador via Packet-In.
        Utilizado especificamente para identificar hosts que emitem Gratuitous ARP.

        Conceito Pedagógico:
            Ao receber o Gratuitous ARP do host, o switch não faz flooding (o que geraria loops
            em topologias cíclicas). O switch desvia o pacote para o controlador.
            O controlador extrai o IP e o MAC da origem, descobre em qual switch e porta o host
            está conectado e armazena na estrutura self.hosts.
        """
        msg = ev.msg
        datapath = msg.datapath
        in_port = msg.match['in_port']

        # Desempacota o frame Ethernet e camadas superiores
        pkt = packet.Packet(msg.data)
        eth_pkt = pkt.get_protocol(ethernet.ethernet)
        arp_pkt = pkt.get_protocol(arp.arp)

        # Ignora pacotes LLDP (eles são consumidos pelo módulo ryu.topology.switches)
        if eth_pkt and eth_pkt.ethertype == 0x88CC:
            return

        # Processa pacotes ARP (Gratuitous ARP / Request / Reply)
        if arp_pkt:
            ip_src = arp_pkt.src_ip
            mac_src = arp_pkt.src_mac

            # Ignora IPs nulos ou inválidos
            if ip_src == "0.0.0.0":
                return

            host_key = ip_src
            info_atual = {'mac': mac_src, 'dpid': datapath.id, 'port': in_port}

            # Verifica se o host é novo ou se mudou de switch/porta
            if host_key not in self.hosts or self.hosts[host_key] != info_atual:
                self.hosts[host_key] = info_atual
                self.logger.info(
                    "[Host Descoberto] IP: %s | MAC: %s | Switch: s%s | Porta: %s",
                    ip_src, mac_src, datapath.id, in_port
                )
                # Atualiza a exibição da topologia completa
                self.print_full_topology()

    # =========================================================================
    # 4. Impressão Amigável e Consolidada da Topologia Completa
    # =========================================================================
    def print_full_topology(self):
        """
        Imprime no terminal uma visão consolidada, formatada e legível da topologia completa,
        contendo switches ativos, enlaces inter-switch e hosts mapeados.
        """
        self.topology_version += 1

        # Consolida enlaces bidirecionais para exibição mais limpa
        # (ex: s1:port1 <===> s2:port2)
        bidirectional_links = set()
        for src_dpid, dst_dpid, src_p, dst_p in self.links:
            # Ordena a tupla para garantir simetria (u < v)
            if (src_dpid, src_p) <= (dst_dpid, dst_p):
                edge = (f"s{src_dpid}", src_p, f"s{dst_dpid}", dst_p)
            else:
                edge = (f"s{dst_dpid}", dst_p, f"s{src_dpid}", src_p)
            bidirectional_links.add(edge)

        sep = "=" * 68
        lines = []
        lines.append("")
        lines.append(sep)
        lines.append(f"  TOPOLOGIA MAPEADA PELO RYU (Atualização #{self.topology_version})")
        lines.append(sep)

        # Seção 1: Switches
        lines.append(f"[+] SWITCHES ATIVOS ({len(self.switches)}):")
        if self.switches:
            switch_str = ", ".join([f"s{dpid} (DPID: {dpid})" for dpid in self.switches])
            lines.append(f"    {switch_str}")
        else:
            lines.append("    (Nenhum switch conectado até o momento)")

        # Seção 2: Enlaces Inter-Switch
        lines.append("")
        lines.append(f"[+] ENLACES ENTRE SWITCHES (Descobertos via LLDP: {len(bidirectional_links)} físicos):")
        if bidirectional_links:
            for s_a, p_a, s_b, p_b in sorted(bidirectional_links):
                lines.append(f"    {s_a} (Porta {p_a}) <=====> {s_b} (Porta {p_b})")
        else:
            lines.append("    (Nenhum enlace inter-switch descoberto ainda)")

        # Seção 3: Servidores e Hosts
        lines.append("")
        lines.append(f"[+] HOSTS CONECTADOS (Descobertos via Gratuitous ARP: {len(self.hosts)}):")
        if self.hosts:
            # Ordena os hosts pelo IP para exibição consistente
            for ip in sorted(self.hosts.keys()):
                info = self.hosts[ip]
                lines.append(
                    f"    Host {ip} [MAC: {info['mac']}] ---> Switch s{info['dpid']}, Porta {info['port']}"
                )
        else:
            lines.append("    (Nenhum host detectado até o momento)")

        lines.append(sep)
        lines.append("")

        # Exibe a saída formatada de uma única vez no log
        self.logger.info("\n".join(lines))
