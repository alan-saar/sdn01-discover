#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trabalho SDN 01 — Descoberta de Topologias de Rede com Mininet e Ryu
Programa de Pós-Graduação em Informática (PPCOMP) — IFES Campus Serra
Autores: Alan Saar e Leonardo Herkenhoff

Script: teste_topologia.py
Objetivo:
    1. Ler e fazer o parsing de um arquivo de texto contendo uma lista de arestas (topologia arbitrária).
    2. Instanciar dinamicamente switches Open vSwitch (OVS) configurados com OpenFlow 1.3.
    3. Conectar os switches de acordo com as arestas definidas no arquivo.
    4. Criar um host dedicado para cada switch, com endereçamento IP e MAC determinísticos.
    5. Conectar cada host à porta de acesso do seu respectivo switch.
    6. Iniciar a rede e disparar pacotes Gratuitous ARP (via 'arping') a partir de cada host
       para viabilizar a descoberta passiva de servidores pelo controlador Ryu.

Analogia Pedagógica ("O Galpão e os Funcionários"):
    - Cada switch adicionado é como uma sala de triagem de correspondência (ex: funcionários Luiz e Flávio).
    - As arestas entre switches são os tubos pneumáticos interligando as salas.
    - Cada host é um cliente da empresa que chega à porta de uma sala e entrega seu cartão de
      visitas não solicitado (Gratuitous ARP) contendo seu nome físico (MAC) e ramal telefônico (IP).
"""

import sys
import os
import re
from time import sleep


def log_msg(msg):
    """Encaminha mensagem para o logger do Mininet se disponível, ou print comum."""
    try:
        from mininet.log import info
        info(msg)
    except ImportError:
        sys.stdout.write(msg)
        sys.stdout.flush()


def parse_edge_list(edge_list_file):
    """
    Realiza a leitura e o parsing do arquivo de arestas da topologia.

    Regras de parsing:
      - Linhas vazias ou contendo apenas espaços são ignoradas.
      - Linhas que iniciam com '#' (comentários ou diagramas em ASCII) são descartadas.
      - Cada linha de aresta válida contém dois identificadores separados por espaço: 's1 s2'.

    Retorna:
      - edges (list of tuples): Lista de tuplas (switch_origem, switch_destino).
      - switches (list of str): Lista ordenada de identificadores únicos de switches.
    """
    if not os.path.exists(edge_list_file):
        raise FileNotFoundError(f"Arquivo de topologia não encontrado: {edge_list_file}")

    edges = []
    unique_switches = set()

    with open(edge_list_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            # Ignora linhas em branco e comentários (incluindo diagramas ASCII)
            if not line or line.startswith('#'):
                continue

            parts = line.split()
            if len(parts) >= 2:
                src, dst = parts[0], parts[1]
                edges.append((src, dst))
                unique_switches.add(src)
                unique_switches.add(dst)
            else:
                log_msg(f"[Aviso] Linha {line_num} ignorada por formato inválido: '{line}'\n")

    # Ordenação natural dos switches (ex: 's1', 's2', ..., 's10') baseada no número extraído
    def natural_sort_key(s):
        numbers = re.findall(r'\d+', s)
        return int(numbers[0]) if numbers else s

    sorted_switches = sorted(list(unique_switches), key=natural_sort_key)
    return edges, sorted_switches


def extract_node_number(node_name):
    """
    Extrai o número identificador do switch para atribuir IP e MAC determinísticos.
    Exemplo: 's1' -> 1; 's6' -> 6. Caso não possua número, retorna 1 como fallback.
    """
    match = re.search(r'\d+', node_name)
    return int(match.group()) if match else 1


def start_network(edge_list_file, interactive=True):
    """
    Constrói e inicia a rede virtualizada utilizando a API do Mininet.

    Parâmetros:
      - edge_list_file (str): Caminho para o arquivo contendo a lista de arestas.
      - interactive (bool): Se True, abre o console interativo do Mininet (CLI).
                            Se False, aguarda a convergência e encerra automaticamente (para testes/scripts).
    """
    log_msg(f"\n=======================================================\n")
    log_msg(f"   Iniciando Instanciação da Topologia: {edge_list_file}\n")
    log_msg(f"=======================================================\n")

    # 1. Parsing do arquivo de topologia
    edges, switch_names = parse_edge_list(edge_list_file)
    log_msg(f"[Mininet] Switches identificados ({len(switch_names)}): {', '.join(switch_names)}\n")
    log_msg(f"[Mininet] Enlaces inter-switch lidos ({len(edges)}):\n")
    for src, dst in edges:
        log_msg(f"          - Enlace: {src} <---> {dst}\n")

    # 2. Inicialização da instância principal do Mininet
    # RemoteController: Delega todas as decisões de controle ao Ryu (localhost:6633).
    # OVSKernelSwitch: Utiliza o módulo em nível de kernel do Open vSwitch para alto desempenho.
    try:
        from mininet.net import Mininet
        from mininet.node import RemoteController, OVSKernelSwitch
        from mininet.cli import CLI
    except ImportError as e:
        log_msg(f"\n[Erro Crítico] O pacote 'mininet' não está instalado neste ambiente Python.\n")
        log_msg(f"Certifique-se de executar em um ambiente com Mininet (ex: VM Mininet ou via 'sudo mn').\nDetalhes: {e}\n")
        sys.exit(1)

    net = Mininet(controller=RemoteController, switch=OVSKernelSwitch)

    log_msg("\n[Mininet] Adicionando Controlador Remoto OpenFlow (Ryu em 127.0.0.1:6633)...\n")
    c0 = net.addController('c0', controller=RemoteController, ip='127.0.0.1', port=6633)

    # 3. Criação dinâmica dos switches OpenFlow 1.3
    # Nota pedagógica: Forçar 'protocols=OpenFlow13' garante que o switch OVS negociará
    # estritamente a versão 1.3 do protocolo com o controlador Ryu.
    switches_dict = {}
    log_msg("[Mininet] Criando switches Open vSwitch (OpenFlow 1.3)...\n")
    for s_name in switch_names:
        sw = net.addSwitch(s_name, protocols='OpenFlow13')
        switches_dict[s_name] = sw
        log_msg(f"          + Switch '{s_name}' criado com sucesso.\n")

    # 4. Criação dos enlaces físicos entre switches (inter-switch links)
    log_msg("\n[Mininet] Estabelecendo enlaces inter-switch...\n")
    for src, dst in edges:
        net.addLink(switches_dict[src], switches_dict[dst])
        log_msg(f"          + Cabo virtual conectado: {src} <---> {dst}\n")

    # 5. Criação de um host determinístico para cada switch
    # Conforme padronização do projeto:
    # Switch sX -> Host hX | IP: 10.0.0.X/24 | MAC: 00:00:00:00:00:0X
    log_msg("\n[Mininet] Criando hosts com endereçamento determinístico e conectando aos switches...\n")
    for s_name in switch_names:
        num = extract_node_number(s_name)
        h_name = f"h{num}"
        ip_addr = f"10.0.0.{num}/24"
        mac_addr = f"00:00:00:00:00:{num:02x}"

        host = net.addHost(h_name, ip=ip_addr, mac=mac_addr)
        net.addLink(host, switches_dict[s_name])
        log_msg(f"          + Host '{h_name}' (IP: {ip_addr.split('/')[0]}, MAC: {mac_addr}) ligado a '{s_name}'\n")

    # 6. Inicialização dos nós da rede e do plano de controle
    log_msg("\n[Mininet] Subindo a rede Mininet...\n")
    net.start()

    # Período de acomodação para o handshake inicial OpenFlow e injeção dos primeiros pacotes LLDP
    log_msg("[Mininet] Aguardando 3 segundos para estabilização do handshake OpenFlow e LLDP...\n")
    sleep(3)

    # 7. Disparo do Gratuitous ARP (GARP)
    # Explicação pedagógica:
    # O comando 'arping -U -c 1 <IP>' faz com que a pilha de rede do host monte um pacote ARP
    # não solicitado (Unsolicited / Gratuitous ARP).
    # O switch de borda recebe o quadro de broadcast na porta de acesso e, por não possuir
    # regras pré-instaladas de encaminhamento para esse tráfego, encapsula o frame em uma
    # mensagem OpenFlow OFPT_PACKET_IN e o envia diretamente ao controlador Ryu.
    # Dessa forma, o controlador descobre o MAC, o IP, o Datapath ID e a porta de conexão do host,
    # sem que ocorra flooding na rede de dados (eliminando riscos de loops).
    log_msg("\n=======================================================\n")
    log_msg("   Enviando Gratuitous ARP de todos os hosts para o Ryu\n")
    log_msg("=======================================================\n")
    for h in net.hosts:
        raw_ip = h.IP()
        log_msg(f"[Mininet Host {h.name}] Executando: arping -U -c 1 {raw_ip}\n")
        # -U: Modo Unsolicited ARP (Gratuitous ARP)
        # -c 1: Envia exatamente 1 pacote
        cmd_output = h.cmd(f'arping -U -c 1 {raw_ip}')
        sleep(0.15)

    log_msg("\n[Mininet] Todos os pacotes Gratuitous ARP foram transmitidos com sucesso!\n")

    # 8. Modo de Execução: Interativo ou Automático
    if interactive:
        log_msg("\n=======================================================\n")
        log_msg("   Abrindo CLI do Mininet (digite 'exit' para encerrar)\n")
        log_msg("=======================================================\n")
        CLI(net)
    else:
        log_msg("\n[Mininet] Modo não-interativo ativo. Aguardando 3 segundos para registro no Ryu...\n")
        sleep(3)

    log_msg("\n[Mininet] Encerrando a rede Mininet e restaurando configurações de rede...\n")
    net.stop()
    log_msg("[Mininet] Execução concluída com sucesso.\n")


if __name__ == '__main__':
    # Configuração de verbosidade do log do Mininet ('info' exibe mensagens formatadas)
    try:
        from mininet.log import setLogLevel
        setLogLevel('info')
    except ImportError:
        pass

    if len(sys.argv) > 1:
        topo_file = sys.argv[1]
        # Suporte à flag opcional '--no-cli' para scripts de automação de testes
        is_interactive = '--no-cli' not in sys.argv
        start_network(topo_file, interactive=is_interactive)
    else:
        print("\nUso do Script:")
        print("    sudo python3 teste_topologia.py <arquivo_topologia.txt> [--no-cli]")
        print("\nExemplos:")
        print("    sudo python3 teste_topologia.py topologias/topo_triangle.txt")
        print("    sudo python3 teste_topologia.py topologias/topo_someloops.txt --no-cli\n")
