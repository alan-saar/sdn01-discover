#!/usr/bin/env bash
# ==============================================================================
# Trabalho SDN 01 — Descoberta de Topologias de Rede com Mininet e Ryu
# Programa de Pós-Graduação em Informática (PPCOMP) — IFES Campus Serra
# Autores: Alan Saar e Leonardo Herkenhoff
#
# Script: run_experiments.sh
# Objetivo:
#   Orquestrar e automatizar a execução dos experimentos para as topologias
#   'Triangle' e 'Someloops', coletando os logs do Mininet e do Ryu e
#   atualizando os gráficos NetworkX para inclusão no relatório técnico.
# ==============================================================================

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

LOGS_DIR="$PROJECT_ROOT/relatorio/logs"
IMG_DIR="$PROJECT_ROOT/relatorio/img"
RYU_BIN="$PROJECT_ROOT/.venv-ryu/bin/ryu-manager"

# Garante que as pastas de destino existam
mkdir -p "$LOGS_DIR" "$IMG_DIR"

echo "===================================================================="
echo "   Iniciando Bateria de Experimentos SDN (Triangle e Someloops)     "
echo "===================================================================="

# 1. Verifica se o ambiente virtual do Ryu está pronto
if [ ! -f "$RYU_BIN" ]; then
    echo "[!] Ambiente virtual do Ryu não encontrado em .venv-ryu."
    echo "    Criando ambiente virtual com uv..."
    uv venv --python 3.9 .venv-ryu
    uv pip install --python .venv-ryu/bin/python "setuptools<58" wheel
    uv pip install --python .venv-ryu/bin/python --no-build-isolation "eventlet==0.30.2" "dnspython<2.0.0" "ryu==4.34"
fi

# 2. Atualiza renderização dos gráficos NetworkX
echo ""
echo "[1/3] Gerando diagramas em alta resolução com NetworkX..."
uv run --with networkx --with matplotlib python3 export_topology_graph.py --all

# Função auxiliar para executar um cenário
run_scenario() {
    local SCENARIO_NAME="$1"
    local TOPO_FILE="$2"
    local RYU_LOG="$LOGS_DIR/ryu_${SCENARIO_NAME}.log"
    local MN_LOG="$LOGS_DIR/mininet_${SCENARIO_NAME}.log"

    echo ""
    echo "--------------------------------------------------------------------"
    echo "   Executando Cenário: Topologia $SCENARIO_NAME ($TOPO_FILE)"
    echo "--------------------------------------------------------------------"

    # Limpa estados prévios do Mininet e Open vSwitch
    echo "[*] Limpando topologias anteriores do Mininet (sudo mn -c)..."
    sudo mn -c >/dev/null 2>&1 || true

    # Inicia o Ryu Controller em background
    echo "[*] Iniciando Ryu Controller (ryu-manager --observe-links topo_discover.py)..."
    "$RYU_BIN" --observe-links topo_discover.py > "$RYU_LOG" 2>&1 &
    local RYU_PID=$!

    # Aguarda o socket TCP 6633 abrir
    echo "[*] Aguardando o controlador Ryu inicializar na porta 6633..."
    sleep 3

    # Executa o Mininet em modo não-interativo (--no-cli) para automação
    echo "[*] Executando Mininet com a topologia $TOPO_FILE..."
    sudo PYTHONPATH="/usr/lib/python3.15/site-packages:$PYTHONPATH" python3 -u teste_topologia.py "$TOPO_FILE" --no-cli 2>&1 | tee "$MN_LOG"

    # Aguarda convergência final das mensagens OpenFlow
    echo "[*] Aguardando acomodação final das mensagens de controle..."
    sleep 4

    # Encerra o controlador Ryu de forma limpa
    echo "[*] Finalizando processo do Ryu (PID $RYU_PID)..."
    kill -TERM "$RYU_PID" 2>/dev/null || true
    wait "$RYU_PID" 2>/dev/null || true

    # Limpeza final do Mininet
    sudo mn -c >/dev/null 2>&1 || true

    echo "[✓] Cenário $SCENARIO_NAME finalizado com sucesso!"
    echo "    - Log do Mininet: $MN_LOG"
    echo "    - Log do Ryu:     $RYU_LOG"
}

# 3. Execução dos dois cenários obrigatórios
echo ""
echo "[2/3] Executando bateria de testes nas topologias..."
run_scenario "triangle" "topologias/topo_triangle.txt"
run_scenario "someloops" "topologias/topo_someloops.txt"

echo ""
echo "===================================================================="
echo "[3/3] Resumo dos Logs Coletados em $LOGS_DIR:"
ls -lh "$LOGS_DIR"
echo "===================================================================="
echo "[✓] Todos os experimentos foram executados e registrados com sucesso!"
echo "    Os artefatos estão prontos para compilação no relatório Typst."
