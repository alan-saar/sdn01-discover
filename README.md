# SDN Topology Discover — Mininet & Ryu

```text
 ▄▄▄▄▄▄▄▄▄▄▄  ▄▄▄▄▄▄▄▄▄▄   ▄▄        ▄  
▐░░░░░░░░░░░▌▐░░░░░░░░░░▌ ▐░░▌      ▐░▌ 
 ▀▀▀▀█░█▀▀▀▀ ▐░█▀▀▀▀▀▀▀█░▌▐░▌░▌     ▐░▌ 
     ▐░▌     ▐░▌       ▐░▌▐░▌▐░▌    ▐░▌ 
     ▐░▌     ▐░▌       ▐░▌▐░▌ ▐░▌   ▐░▌ 
     ▐░▌     ▐░▌       ▐░▌▐░▌  ▐░▌  ▐░▌ 
     ▐░▌     ▐░▌       ▐░▌▐░▌   ▐░▌ ▐░▌ 
     ▐░▌     ▐░▌       ▐░▌▐░▌    ▐░▐░▌ 
 ▄▄▄▄█░█▄▄▄▄ ▐░█▄▄▄▄▄▄▄█░▌▐░▌     ▐░░▌ 
▐░░░░░░░░░░░▌▐░░░░░░░░░░▌ ▐░▌      ▐░▌ 
 ▀▀▀▀▀▀▀▀▀▀▀  ▀▀▀▀▀▀▀▀▀▀   ▀        ▀  
   TOPOLOGY DISCOVERY & ACTIVE MAPPING (OPENFLOW 1.3)
```

[![Arch Linux](https://img.shields.io/badge/OS-Arch%20Linux%20%7C%20Omarchy-1793D1?logo=arch-linux&logoColor=white)](https://archlinux.org)
[![Python](https://img.shields.io/badge/Python-3.9%20(Ryu)%20%7C%203.15%20(Mininet)-3776AB?logo=python&logoColor=white)](https://python.org)
[![Mininet](https://img.shields.io/badge/Mininet-2.3.1-orange)](http://mininet.org)
[![Ryu](https://img.shields.io/badge/Ryu-4.34-blue)](https://ryu-sdn.org)
[![OpenFlow](https://img.shields.io/badge/OpenFlow-1.3-green)](https://opennetworking.org)
[![Typst](https://img.shields.io/badge/Report-Typst%200.15-239DAD?logo=typst&logoColor=white)](https://typst.app)

> **Trabalho 01 — Redes Definidas por Software (SDN)**  
> **Programa de Pós-Graduação em Informática (PPCOMP) — IFES Campus Serra**  
> **Autores:** Alan Saar e Leonardo Herkenhoff

---

## ⚡ Visão Geral

Solução completa para **instanciação dinâmica, descoberta ativa de enlaces e mapeamento de estações em SDN**, combinando:
1. **Mininet:** Leitura e instanciação dinâmica de grafos arbitrários a partir de listas de arestas (`topo_*.txt`) com switches Open vSwitch (OVS).
2. **Ryu Controller:** Descoberta de enlaces físicos inter-switch via injeção periódica de pacotes **LLDP** (`--observe-links`) e consumo de eventos `EventSwitchEnter` e `EventLinkAdd`.
3. **Mapeamento Passivo de Hosts:** Descoberta de terminais por interceptação controlada de pacotes **Gratuitous ARP (GARP)** via mensagens OpenFlow `Packet-In`, suprimindo transmissões em *broadcast* e evitando *broadcast storms* em topologias cíclicas.
4. **Modelagem em Grafos (NetworkX):** Renderização automática da topologia física $G = (V, E)$ em imagens de alta definição (300 DPI).
5. **Relatório Técnico em Typst:** Documentação acadêmica estruturada sobre o modelo institucional `IFES-DOC`.

---

## 🏛️ A Analogia do Galpão e dos Funcionários

Para facilitar o entendimento didático da divisão entre o Plano de Controle e o Plano de Dados:

```
                      ┌──────────────────────────────────────┐
                      │    GERENTE GERAL (Controlador Ryu)    │
                      │   - Visão global da topologia         │
                      │   - Injeta bilhetes LLDP             │
                      │   - Cadastra visitantes (Hosts)       │
                      └──────────────────┬───────────────────┘
                                         │  OpenFlow 1.3 (TCP :6633)
                ┌────────────────────────┴────────────────────────┐
                ▼                                                 ▼
     ┌─────────────────────┐       Tubo Pneumático     ┌─────────────────────┐
     │  FUNCIONÁRIO LUIZ   │◄========================►│  FUNCIONÁRIO FLÁVIO  │
     │     (Switch s1)     │        (Cabo Físico)      │     (Switch s2)     │
     └──────────▲──────────┘                           └──────────▲──────────┘
                │ Porta 3                                         │ Porta 3
                │ Cartão de Visitas                               │ Cartão de Visitas
                │ (Gratuitous ARP)                                │ (Gratuitous ARP)
         ┌──────┴──────┐                                   ┌──────┴──────┐
         │ CLIENTE h1  │                                   │ CLIENTE h2  │
         │ (10.0.0.1)  │                                   │ (10.0.0.2)  │
         └─────────────┘                                   └─────────────┘
```

* **O Gerente Geral (Ryu):** Coordena todo o edifício a partir de uma sala central.
* **Os Funcionários Luiz e Flávio (Switches):** Ficam trancados em salas de triagem com portas numeradas, cumprindo estritamente as ordens da tabela de regras (*Flow Table*).
* **Os Tubos Pneumáticos (Cabos de Rede):** Interligam as portas das salas.
* **O Bilhete nos Tubos (Pacote LLDP):** O Gerente manda Luiz jogar um bilhete pelo tubo da Porta 1; quando o bilhete cai na sala de Flávio, Flávio liga para a gerência avisando: *o enlace entre Luiz e Flávio existe!*
* **O Cartão de Visitas do Cliente (Gratuitous ARP):** Ao se plugar à sala de Luiz, o cliente entrega seu cartão (MAC e IP). Luiz não sai gritando pelo prédio (*flooding*); ele repassa a correspondência em envelope fechado ao Gerente (`Packet-In`).

---

## 📂 Estrutura do Repositório

```text
.
├── topologias/
│   ├── topo_triangle.txt         # Grafo triangular com loops (s1, s2, s3)
│   └── topo_someloops.txt        # Grafo complexo com anéis entrelaçados (s1..s6)
├── teste_topologia.py            # Instanciação Mininet (parser, OVS OF1.3, arping)
├── topo_discover.py              # Aplicação controladora Ryu (LLDP, GARP, log tabular)
├── export_topology_graph.py      # Renderizador NetworkX -> relatorio/img/ (300 DPI)
├── run_experiments.sh            # Script de automação total dos testes e coleta de logs
├── gerar_relatorio.sh            # Compilador automatizado do relatório em Typst (com suporte a --watch)
├── empacotar_entrega.sh          # Script de validação e geração do pacote ZIP para o AVA / Moodle
├── devrefs/
│   ├── especificacao.md          # Especificação original da atividade
│   └── planejamento.md           # Planejamento completo de tarefas e decisões
├── relatorio/
│   ├── modelo/IFES-DOC/          # Template institucional IFES em Typst
│   ├── img/                      # Imagens de topologia renderizadas pelo NetworkX
│   └── logs/                     # Registros de execução do Mininet e Ryu
├── .gitignore                    # Regras de exclusão (venv, devrefs, caches)
└── README.md                     # Este documento
```

---

## 🛠️ Configuração do Ambiente no Arch / Omarchy Linux

O Mininet opera no espaço de kernel com o Python nativo do Arch Linux, enquanto o Ryu requer bibliotecas legadas (`eventlet==0.30.2`, `setuptools<58`), necessitando do Python 3.9. 

Graças ao desacoplamento do OpenFlow, **eles rodam em ambientes separados e conversam via rede TCP (127.0.0.1:6633)**.

### 1. Preparar o venv do Ryu com `uv`

Utilize o gerenciador ultra-rápido `uv`:

```bash
# 1. Cria o ambiente virtual com Python 3.9
uv venv --python 3.9 .venv-ryu

# 2. Instala setuptools legado e wheel
uv pip install --python .venv-ryu/bin/python "setuptools<58" wheel

# 3. Instala o Ryu e dependências estáveis sem isolamento de build
uv pip install --python .venv-ryu/bin/python --no-build-isolation "eventlet==0.30.2" "dnspython<2.0.0" "ryu==4.34"
```

Valide a instalação:
```bash
.venv-ryu/bin/ryu-manager --version
# Saída esperada: ryu-manager 4.34
```

### 2. Gerar as Imagens dos Grafos com NetworkX

Para gerar as representações visuais em alta resolução das duas topologias:

```bash
uv run --with networkx --with matplotlib python3 export_topology_graph.py --all
```
As imagens serão salvas automaticamente em:
* `relatorio/img/topo_triangle_networkx.png`
* `relatorio/img/topo_someloops_networkx.png`

---

## 🚀 Como Executar os Experimentos

Você pode executar os experimentos de duas formas:

### Opção 1 — Automação Completa (Recomendado) ⚡

Utilize o script de orquestração que executa sequencialmente as topologias *Triangle* e *Someloops*, limpa o ambiente anterior com `mn -c`, salva os logs do Mininet e do Ryu em `relatorio/logs/` e atualiza as imagens do NetworkX:

```bash
./run_experiments.sh
```

Os logs consolidados serão gerados em:
* `relatorio/logs/ryu_triangle.log` e `relatorio/logs/mininet_triangle.log`
* `relatorio/logs/ryu_someloops.log` e `relatorio/logs/mininet_someloops.log`

---

### Opção 2 — Execução Interativa (Dois Terminais) 🖥️

Caso queira inspecionar visualmente o console do Ryu ou acessar o prompt `mininet>`:

#### Terminal 1 — Subir o Controlador Ryu:
```bash
# Ativa o ambiente dedicado do Ryu
source .venv-ryu/bin/activate

# Executa com descoberta ativa de enlaces LLDP
ryu-manager --observe-links topo_discover.py
```

#### Terminal 2 — Instanciar a Topologia no Mininet:
No terminal do sistema (**sem** ativar o venv do Ryu):

```bash
# Topologia 1: Triangle
sudo python3 teste_topologia.py topologias/topo_triangle.txt

# Topologia 2: Someloops
sudo python3 teste_topologia.py topologias/topo_someloops.txt
```

> **Dica:** Para rodar sem abrir o prompt interativo do Mininet, passe `--no-cli`:
> ```bash
> sudo python3 teste_topologia.py topologias/topo_triangle.txt --no-cli
> ```

---

## 📊 Saída Esperada no Log do Ryu

Quando os pacotes LLDP mapearem os enlaces e os Gratuitous ARPs forem interceptados, o Ryu imprimirá no console a topologia completa consolidada:

```text
====================================================================
  TOPOLOGIA MAPEADA PELO RYU (Atualização #4)
====================================================================
[+] SWITCHES ATIVOS (3):
    s1 (DPID: 1), s2 (DPID: 2), s3 (DPID: 3)

[+] ENLACES ENTRE SWITCHES (Descobertos via LLDP: 3 físicos):
    s1 (Porta 1) <=====> s2 (Porta 1)
    s1 (Porta 2) <=====> s3 (Porta 2)
    s2 (Porta 2) <=====> s3 (Porta 1)

[+] HOSTS CONECTADOS (Descobertos via Gratuitous ARP: 3):
    Host 10.0.0.1 [MAC: 00:00:00:00:00:01] ---> Switch s1, Porta 3
    Host 10.0.0.2 [MAC: 00:00:00:00:00:02] ---> Switch s2, Porta 3
    Host 10.0.0.3 [MAC: 00:00:00:00:00:03] ---> Switch s3, Porta 3
====================================================================
```

---

## 📄 Compilação do Relatório Técnico

O relatório técnico é escrito em **Typst** e utiliza o modelo oficial do IFES. Para compilá-lo com um único comando:

```bash
# Compilação padrão (gera relatorio/relatorio.pdf)
./gerar_relatorio.sh

# Modo contínuo (live-reload enquanto edita o .typ)
./gerar_relatorio.sh --watch
```

Também é possível compilar diretamente via utilitário nativo do Typst:
```bash
typst compile relatorio/relatorio.typ relatorio/relatorio.pdf
```

---

## 📦 Empacotamento para Submissão no AVA / Moodle

Para validar todos os artefatos obrigatórios e gerar o arquivo ZIP de entrega exigido pela disciplina:

```bash
./empacotar_entrega.sh
```

Esse script realiza:
1. A recompilação do relatório em PDF com dados atualizados;
2. A validação de integridade dos 16 arquivos obrigatórios;
3. A criação do arquivo compactado `trab-sdn-01-alan-leonardo.zip`, expurgando arquivos temporários e virtuais.

---

## 📜 Licença

Projeto desenvolvido para fins educacionais e de pesquisa no Programa de Pós-Graduação em Informática (PPCOMP - IFES). Licenciado sob a licença MIT.
