#!/usr/bin/env python3
"""
Script de teste para validar se a integração com Graphiti/FalkorDB está funcionando.
"""
import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve()
load_dotenv(ROOT_DIR.parent / ".env")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("\n" + "="*80)
print("🔍 VALIDAÇÃO DE GRAPHITI/FALKORDB")
print("="*80 + "\n")

# 1. Verificar env vars
print("1️⃣ Verificando variáveis de ambiente...")
falkordb_host = os.environ.get("FALKORDB_HOST", "localhost")
falkordb_port = os.environ.get("FALKORDB_PORT", "6379")
print(f"   FALKORDB_HOST: {falkordb_host}")
print(f"   FALKORDB_PORT: {falkordb_port}")

# 2. Verificar imports
print("\n2️⃣ Verificando imports...")
try:
    from graphiti_core import Graphiti
    print("   ✅ graphiti_core importado")
except ImportError as e:
    print(f"   ❌ graphiti_core não instalado: {e}")
    sys.exit(1)

try:
    from graphiti_core.driver.falkordb_driver import FalkorDriver
    print("   ✅ FalkorDriver importado")
except ImportError as e:
    print(f"   ❌ FalkorDriver não instalado: {e}")
    sys.exit(1)

# 3. Testar conexão
print("\n3️⃣ Testando conexão com FalkorDB...")
try:
    driver = FalkorDriver(host=falkordb_host, port=int(falkordb_port))
    print(f"   ✅ Conectado ao FalkorDB ({falkordb_host}:{falkordb_port})")
except Exception as e:
    print(f"   ❌ Falha na conexão: {e}")
    print("\n   💡 Certifique-se de que FalkorDB está rodando:")
    print("      docker-compose up falkordb -d")
    sys.exit(1)

# 4. Testar Graphiti
print("\n4️⃣ Testando Graphiti...")
try:
    graphiti = Graphiti(graph_driver=driver)
    print("   ✅ Graphiti inicializado")
except Exception as e:
    print(f"   ❌ Erro ao inicializar Graphiti: {e}")
    sys.exit(1)

# 5. Testar save_to_graph
print("\n5️⃣ Testando save_to_graph...")
try:
    from references.middleware import save_to_graph
    print("   ✅ save_to_graph importado")
    
    # Teste simples
    test_state = {
        "messages": [
            {"role": "user", "content": "Test message"},
            {"role": "assistant", "content": "Test response"}
        ],
        "session_id": "test_session",
        "user_id": "test_user",
    }
    
    result = save_to_graph(test_state)
    print("   ✅ save_to_graph() executado com sucesso")
    
except Exception as e:
    print(f"   ❌ Erro ao testar save_to_graph: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 6. Verificar banco de dados PostgreSQL
print("\n6️⃣ Verificando PostgreSQL...")
try:
    from references.sqlalchemy_models import get_session, MemoryBlock
    session = get_session()
    block_count = session.query(MemoryBlock).count()
    session.close()
    print(f"   ✅ PostgreSQL conectado ({block_count} bloco(s) de memória)")
except Exception as e:
    print(f"   ❌ Erro ao conectar PostgreSQL: {e}")
    sys.exit(1)

# Resumo
print("\n" + "="*80)
print("✅ TODAS AS VALIDAÇÕES PASSARAM!")
print("="*80)
print("\n💡 Próximos passos:")
print("   1. Reprocessar memória existente:")
print("      python reprocess_memory_to_graph.py")
print("   2. Ou usar o script:")
print("      ./reprocess_memory.sh")
print("\n")
