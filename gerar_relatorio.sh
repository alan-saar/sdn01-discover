#!/usr/bin/env bash
# ==============================================================================
# Trabalho SDN 01 — Descoberta de Topologias de Rede com Mininet e Ryu
# Programa de Pós-Graduação em Informática (PPCOMP) — IFES Campus Serra
# Autores: Alan Saar e Leonardo Herkenhoff
#
# Script: gerar_relatorio.sh
# Objetivo:
#   Compilar o relatório técnico em Typst para PDF com suporte a live-reload.
#
# Uso:
#   ./gerar_relatorio.sh          # Compilação única
#   ./gerar_relatorio.sh --watch  # Modo contínuo (recompila ao salvar)
# ==============================================================================

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RELATORIO_DIR="$PROJECT_ROOT/relatorio"
SRC_TYP="$RELATORIO_DIR/relatorio.typ"
OUT_PDF="$RELATORIO_DIR/relatorio.pdf"

if ! command -v typst &> /dev/null; then
    echo "[Erro] O compilador Typst não foi encontrado no PATH."
    echo "       Instale no Arch Linux com: sudo pacman -S typst"
    exit 1
fi

echo "===================================================================="
echo "   Compilador do Relatório Técnico Typst — PPCOMP / IFES Serra     "
echo "===================================================================="
echo "[*] Fonte:  $SRC_TYP"
echo "[*] Destino: $OUT_PDF"

# Garante que os gráficos NetworkX estejam gerados
if [ ! -f "$RELATORIO_DIR/img/topo_triangle_networkx.png" ] || [ ! -f "$RELATORIO_DIR/img/topo_someloops_networkx.png" ]; then
    echo "[*] Gráficos NetworkX não encontrados. Gerando via export_topology_graph.py..."
    uv run --with networkx --with matplotlib python3 export_topology_graph.py --all
fi

if [ "$1" == "--watch" ]; then
    echo ""
    echo "[*] Modo de observação contínua (--watch) ativado."
    echo "    Pressione Ctrl+C para encerrar."
    typst watch "$SRC_TYP" "$OUT_PDF"
else
    typst compile "$SRC_TYP" "$OUT_PDF"
    echo ""
    echo "[✓] Relatório compilado com sucesso!"
    
    # Exibe informações do arquivo gerado
    if command -v pdfinfo &> /dev/null; then
        PAGES=$(pdfinfo "$OUT_PDF" | grep "Pages:" | awk '{print $2}')
        SIZE=$(du -h "$OUT_PDF" | awk '{print $1}')
        echo "    - Tamanho: $SIZE"
        echo "    - Páginas: $PAGES páginas"
    fi
    echo "    - Arquivo: $OUT_PDF"
fi
