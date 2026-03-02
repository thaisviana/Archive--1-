#!/bin/bash
# Script para ativar o ambiente virtual e reprocessar memória para o grafo

set -e

# Verificar se estamos em um diretório com .venv
if [ ! -d ".venv" ]; then
    echo "❌ Ambiente virtual não encontrado. Execute dentro do diretório do projeto."
    exit 1
fi

# Ativar ambiente
source .venv/bin/activate

echo ""
echo "🔄 REPROCESSADOR DE MEMÓRIA → GRAFO"
echo "======================================"
echo ""

# Executar com argumentos passados
python reprocess_memory_to_graph.py "$@"
