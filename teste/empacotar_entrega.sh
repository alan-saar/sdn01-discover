#!/usr/bin/env bash
# ==============================================================================
# Trabalho SDN 01 — Descoberta de Topologias de Rede com Mininet e Ryu
# Programa de Pós-Graduação em Informática (PPCOMP) — IFES Campus Serra
# Autores: Alan Saar e Leonardo Herkenhoff
#
# Script: empacotar_entrega.sh
# Objetivo:
#   1. Recompilar o relatório em PDF (garantindo dados atualizados).
#   2. Validar a presença de todos os códigos, topologias, imagens e logs.
#   3. Gerar o arquivo ZIP final para submissão no AVA / Moodle,
#      excluindo ambientes virtuais (.venv), histórico git e caches.
# ==============================================================================

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

ZIP_NAME="trab-sdn-01-alan-leonardo.zip"
ZIP_PATH="$PROJECT_ROOT/$ZIP_NAME"

echo "===================================================================="
echo "   Empacotador de Entrega — Trabalho SDN 01 (PPCOMP / IFES)        "
echo "===================================================================="

# 1. Recompila o relatório Typst para garantir que o PDF está na versão mais recente
echo "[1/4] Recompilando o relatório técnico em PDF..."
./gerar_relatorio.sh > /dev/null

if [ ! -f "relatorio/relatorio.pdf" ]; then
    echo "[Erro] O arquivo relatorio/relatorio.pdf não foi gerado!"
    exit 1
fi
echo "      [✓] relatorio/relatorio.pdf atualizado com sucesso."

# 2. Validação dos artefatos obrigatórios da especificação
echo ""
echo "[2/4] Validando artefatos obrigatórios da entrega..."

REQUIRED_FILES=(
    "teste_topologia.py"
    "topo_discover.py"
    "export_topology_graph.py"
    "run_experiments.sh"
    "gerar_relatorio.sh"
    "README.md"
    "topologias/topo_triangle.txt"
    "topologias/topo_someloops.txt"
    "relatorio/img/topo_triangle_networkx.png"
    "relatorio/img/topo_someloops_networkx.png"
    "relatorio/logs/mininet_triangle.log"
    "relatorio/logs/ryu_triangle.log"
    "relatorio/logs/mininet_someloops.log"
    "relatorio/logs/ryu_someloops.log"
    "relatorio/relatorio.typ"
    "relatorio/relatorio.pdf"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "      [X] Arquivo obrigatório ausente: $file"
        exit 1
    else
        echo "      [✓] $file"
    fi
done

# 3. Remoção de pacote anterior se existente
echo ""
echo "[3/4] Criando arquivo ZIP da entrega ($ZIP_NAME)..."
rm -f "$ZIP_PATH"

# 4. Compactação seletiva (excluindo .venv, .git, caches e temporários)
zip -r "$ZIP_PATH" \
    teste_topologia.py \
    topo_discover.py \
    export_topology_graph.py \
    run_experiments.sh \
    gerar_relatorio.sh \
    empacotar_entrega.sh \
    README.md \
    topologias/ \
    relatorio/ \
    -x "*.venv*" \
    -x "*__pycache__*" \
    -x "*.git*" \
    -x "*.pyc" \
    -x "*.DS_Store" > /dev/null

echo "      [✓] Arquivo ZIP compactado com sucesso!"

# 5. Resumo da Entrega
ZIP_SIZE=$(du -h "$ZIP_PATH" | awk '{print $1}')
PDF_SIZE=$(du -h "relatorio/relatorio.pdf" | awk '{print $1}')

echo ""
echo "===================================================================="
echo "   PACOTE DE ENTREGA PRONTO PARA O AVA / MOODLE                   "
echo "===================================================================="
echo "1. Pacote ZIP:        $ZIP_PATH ($ZIP_SIZE)"
echo "2. Relatório Técnico: relatorio/relatorio.pdf ($PDF_SIZE)"
echo "===================================================================="
echo "Para reenviar ou atualizar o pacote no futuro após qualquer edição,"
echo "basta executar novamente: ./empacotar_entrega.sh"
echo "===================================================================="
