#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trabalho SDN 01 — Descoberta de Topologias de Rede com Mininet e Ryu
Programa de Pós-Graduação em Informática (PPCOMP) — IFES Campus Serra
Autores: Alan Saar e Leonardo Herkenhoff

Script: export_topology_graph.py
Objetivo:
    1. Modelar a topologia de rede descoberta como um Grafo Não-Direcionado G = (V, E)
       utilizando a biblioteca NetworkX.
    2. Diferenciar visualmente switches (plano de controle/encaminhamento) e hosts (terminais).
    3. Gerar representações gráficas de alta resolução (PNG 300 DPI) para as topologias
       'Triangle' e 'Someloops', salvando diretamente em 'relatorio/img/'.

Conceito Pedagógico (SDN e Teoria dos Grafos):
    Em redes SDN, o controlador mantém uma visão global e centralizada da rede representada
    formalmente por um grafo G = (V, E):
      - V = S U H, onde S é o conjunto de switches OpenFlow e H é o conjunto de hosts.
      - E = E_switch U E_host, onde E_switch são os enlaces físicos descobertos via LLDP
        e E_host são as conexões de borda mapeadas pelo Gratuitous ARP.
    Essa abstração permite a execução de algoritmos clássicos de grafos (ex: Dijkstra para
    menor caminho, Spanning Tree para prevenção de loops e BFS para busca em largura).
"""

import os
import sys
import argparse
import networkx as nx
import matplotlib.pyplot as plt

# Reutiliza o parser de arestas e utilitários de teste_topologia.py
from teste_topologia import parse_edge_list, extract_node_number


def build_networkx_graph(edge_list_file):
    """
    Constrói um grafo NetworkX a partir de um arquivo de arestas.
    Adiciona switches, enlaces entre switches e os respectivos hosts conectados.

    Retorna:
      - G (nx.Graph): Grafo completo com atributos de nós e arestas.
      - switch_nodes (list): Lista de identificadores de switches.
      - host_nodes (list): Lista de identificadores de hosts.
    """
    edges, switch_names = parse_edge_list(edge_list_file)

    G = nx.Graph()
    switch_nodes = []
    host_nodes = []

    # 1. Adiciona os nós de switches com atributos
    for s in switch_names:
        num = extract_node_number(s)
        G.add_node(s, type='switch', dpid=num, label=f"{s}\n(DPID {num})")
        switch_nodes.append(s)

    # 2. Adiciona as arestas inter-switch (enlaces descobertos por LLDP)
    for u, v in edges:
        G.add_edge(u, v, type='inter-switch', label='LLDP Link')

    # 3. Adiciona os hosts determinísticos e suas arestas (descobertos por GARP)
    for s in switch_names:
        num = extract_node_number(s)
        h = f"h{num}"
        ip = f"10.0.0.{num}"
        mac = f"00:00:00:00:00:{num:02x}"
        G.add_node(h, type='host', ip=ip, mac=mac, label=f"{h}\n{ip}")
        host_nodes.append(h)
        G.add_edge(h, s, type='host-link', label='Host Access')

    return G, switch_nodes, host_nodes


def get_custom_layout(G, topo_name):
    """
    Define coordenadas manuais ou ajustadas para os nós, visando a máxima
    clareza estética e alinhamento com os diagramas teóricos da especificação.
    """
    pos = {}
    topo_lower = topo_name.lower()

    if "triangle" in topo_lower:
        # Topologia Triangular: s1 e s3 na base, s2 no topo
        # Hosts posicionados radialmente para fora
        pos['s1'] = (-1.0, 0.0)
        pos['s3'] = (1.0, 0.0)
        pos['s2'] = (0.0, 1.4)

        pos['h1'] = (-1.8, -0.4)
        pos['h3'] = (1.8, -0.4)
        pos['h2'] = (0.0, 2.2)

    elif "someloops" in topo_lower:
        # Topologia Someloops conforme especificação:
        # s5 --- s1 --- s2
        #  | \ /  | \ /  | \
        #  |  X   |  X   |  s6
        #  | / \  | / \  | /
        # s3 --- s4 -----+
        pos['s5'] = (-1.2, 1.0)
        pos['s1'] = (0.0, 1.0)
        pos['s2'] = (1.2, 1.0)

        pos['s3'] = (-1.2, -1.0)
        pos['s4'] = (0.0, -1.0)
        pos['s6'] = (2.2, 0.0)

        # Hosts posicionados próximos aos seus respectivos switches
        pos['h5'] = (-1.8, 1.6)
        pos['h1'] = (0.0, 1.8)
        pos['h2'] = (1.2, 1.8)
        pos['h3'] = (-1.8, -1.6)
        pos['h4'] = (0.0, -1.8)
        pos['h6'] = (3.0, 0.0)

    else:
        # Fallback genérico usando spring layout para topologias arbitrárias
        pos = nx.spring_layout(G, seed=42, k=1.2)

    return pos


def render_and_save_graph(G, switch_nodes, host_nodes, output_path, title):
    """
    Renderiza o grafo NetworkX usando Matplotlib e salva em arquivo com alta resolução.
    """
    plt.figure(figsize=(9, 7), dpi=300)
    plt.title(title, fontsize=14, fontweight='bold', pad=20, color='#1A365D')

    # Identifica o layout geométrico mais adequado
    pos = get_custom_layout(G, output_path)

    # 1. Desenha arestas inter-switch (LLDP) com linha sólida e espessura destacada
    inter_switch_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get('type') == 'inter-switch']
    nx.draw_networkx_edges(
        G, pos,
        edgelist=inter_switch_edges,
        width=3.0,
        edge_color='#2B6CB0',
        style='solid',
        alpha=0.9,
        label='Enlaces Inter-Switch (LLDP)'
    )

    # 2. Desenha arestas host-switch com linha pontilhada/tracejada
    host_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get('type') == 'host-link']
    nx.draw_networkx_edges(
        G, pos,
        edgelist=host_edges,
        width=2.0,
        edge_color='#718096',
        style='dashed',
        alpha=0.8,
        label='Acesso de Hosts (GARP)'
    )

    # 3. Desenha nós de Switches (quadrados azuis)
    nx.draw_networkx_nodes(
        G, pos,
        nodelist=switch_nodes,
        node_shape='s',
        node_size=1800,
        node_color='#3182CE',
        edgecolors='#1A365D',
        linewidths=2.5,
        label='Switches OpenFlow (OVS)'
    )

    # 4. Desenha nós de Hosts (círculos verdes)
    nx.draw_networkx_nodes(
        G, pos,
        nodelist=host_nodes,
        node_shape='o',
        node_size=1400,
        node_color='#38A169',
        edgecolors='#22543D',
        linewidths=2.0,
        label='Hosts / Servidores'
    )

    # 5. Rótulos dos nós (com fontes limpas e legíveis)
    switch_labels = {s: f"{s}\n(DPID {G.nodes[s]['dpid']})" for s in switch_nodes}
    host_labels = {h: f"{h}\n{G.nodes[h]['ip']}" for h in host_nodes}

    nx.draw_networkx_labels(
        G, pos,
        labels=switch_labels,
        font_size=9,
        font_weight='bold',
        font_color='white'
    )
    nx.draw_networkx_labels(
        G, pos,
        labels=host_labels,
        font_size=8,
        font_weight='bold',
        font_color='white'
    )

    # Legenda descritiva
    plt.legend(scatterpoints=1, loc='upper left', frameon=True, facecolor='#F7FAFC', edgecolor='#CBD5E0', fontsize=8)
    plt.axis('off')
    plt.tight_layout()

    # Cria diretório de destino se não existir
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close()

    print(f"[NetworkX] Imagem da topologia gerada com sucesso: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Exporta gráficos NetworkX das topologias SDN.")
    parser.add_argument("--all", action="store_true", help="Gera os gráficos de todas as topologias do projeto")
    parser.add_argument("--topo", type=str, help="Caminho para arquivo de arestas específico")
    parser.add_argument("--output", type=str, help="Caminho para o arquivo PNG de saída")
    args = parser.parse_args()

    # Mapeamento padrão dos cenários do projeto
    topologias = [
        {
            "file": "topologias/topo_triangle.txt",
            "output": "relatorio/img/topo_triangle_networkx.png",
            "title": "Topologia Triangle — Mapeamento em Grafo (NetworkX)"
        },
        {
            "file": "topologias/topo_someloops.txt",
            "output": "relatorio/img/topo_someloops_networkx.png",
            "title": "Topologia Someloops — Mapeamento em Grafo (NetworkX)"
        }
    ]

    if args.all or (not args.topo and not args.output):
        for item in topologias:
            if os.path.exists(item["file"]):
                G, sw, ho = build_networkx_graph(item["file"])
                render_and_save_graph(G, sw, ho, item["output"], item["title"])
            else:
                print(f"[Erro] Arquivo não encontrado: {item['file']}")
    else:
        if not args.topo or not args.output:
            print("Uso: python3 export_topology_graph.py --topo <arquivo> --output <imagem.png>")
            sys.exit(1)
        G, sw, ho = build_networkx_graph(args.topo)
        render_and_save_graph(G, sw, ho, args.output, "Topologia Customizada — Mapeamento em Grafo")


if __name__ == '__main__':
    main()
