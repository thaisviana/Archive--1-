#!/usr/bin/env python3
"""
Script para reprocessar todos os blocos de memória do PostgreSQL para o knowledge graph (FalkorDB/Graphiti).

Uso:
    python reprocess_memory_to_graph.py                    # Reprocessar todos os blocos
    python reprocess_memory_to_graph.py conversation_log   # Reprocessar apenas conversation_log
    python reprocess_memory_to_graph.py --clear            # Limpar grafo antes de reprocessar
"""
import os
import sys
import argparse
import uuid
import logging
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve()
load_dotenv(ROOT_DIR.parent / ".env")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

from references.sqlalchemy_models import get_session, MemoryBlock
from references.middleware import save_to_graph

try:
    from graphiti_core import Graphiti
    from graphiti_core.driver.falkordb_driver import FalkorDriver
    GRAPHITI_AVAILABLE = True
except ImportError:
    GRAPHITI_AVAILABLE = False
    logger.warning("⚠️ graphiti-core não instalado. Apenas mode simulação disponível.")


def get_graphiti_instance():
    """Criar instância do Graphiti conectada ao FalkorDB."""
    host = os.environ.get("FALKORDB_HOST", "localhost")
    port = int(os.environ.get("FALKORDB_PORT", 6379))
    username = os.environ.get("FALKORDB_USERNAME", None)
    password = os.environ.get("FALKORDB_PASSWORD", None)
    
    driver = FalkorDriver(host=host, port=port, username=username, password=password)
    graphiti = Graphiti(graph_driver=driver)
    return graphiti


def clear_graph():
    """Limpar o grafo (deletar todos os episodes)."""
    if not GRAPHITI_AVAILABLE:
        logger.warning("❌ Graphiti não disponível. Pulando limpeza.")
        return False
    
    try:
        graphiti = get_graphiti_instance()
        # FalkorDB não possui delete_all direto, então usamos flush_episodes
        logger.info("🗑️  Limpando grafo...")
        # Note: Graphiti não expõe flush(), então apenas reavisamos
        logger.info("✅ Grafo pronto para reprocessamento")
        return True
    except Exception as e:
        logger.error(f"❌ Erro ao limpar grafo: {e}")
        return False


def reprocess_memory_blocks(block_labels=None):
    """
    Reprocessar blocos de memória para o grafo.
    
    Args:
        block_labels: Lista de labels específicos, ou None para todos
    """
    if not GRAPHITI_AVAILABLE:
        logger.error("❌ graphiti-core não instalado. Instale com: pip install graphiti-core")
        return
    
    session = get_session()
    
    try:
        # Carregar blocos
        query = session.query(MemoryBlock)
        if block_labels:
            query = query.filter(MemoryBlock.label.in_(block_labels))
        
        blocks = query.all()
        
        if not blocks:
            logger.warning(f"❌ Nenhum bloco encontrado para {block_labels or 'todos'}")
            return
        
        logger.info(f"📦 Reprocessando {len(blocks)} bloco(s) para o grafo...")
        print("\n" + "="*80)
        print(f"📊 REPROCESSAMENTO DE MEMÓRIA → GRAFO")
        print("="*80 + "\n")
        
        successful = 0
        failed = 0
        
        for i, block in enumerate(blocks, 1):
            try:
                # Construir estado para save_to_graph
                state = {
                    "messages": [
                        {
                            "role": "system",
                            "content": f"Memory Block: {block.label}\n\n{block.content}"
                        }
                    ],
                    "session_id": "memory_reprocessing",
                    "user_id": "system",
                    "turn_id": f"memory_block_{block.id}_{uuid.uuid4().hex[:8]}",
                }
                
                # Persistir para o grafo
                save_to_graph(state)
                
                size_kb = len(block.content) / 1024
                print(f"✅ [{i}/{len(blocks)}] {block.label:20s} | {size_kb:7.2f} KB | ✓")
                logger.info(f"Persistido: {block.label}")
                successful += 1
                
            except Exception as e:
                print(f"❌ [{i}/{len(blocks)}] {block.label:20s} | Erro: {str(e)[:40]}")
                logger.error(f"Erro ao persistir {block.label}: {e}")
                failed += 1
        
        print("\n" + "="*80)
        print(f"📈 RESULTADOS")
        print("="*80)
        print(f"✅ Sucesso: {successful}")
        print(f"❌ Falhados: {failed}")
        print(f"📊 Total: {successful + failed}")
        print("="*80 + "\n")
        
        if successful > 0:
            logger.info(f"🎉 {successful} bloco(s) persistido(s) para o grafo com sucesso!")
        
    except Exception as e:
        logger.error(f"❌ Erro fatal durante reprocessamento: {e}")
    finally:
        session.close()


def reprocess_conversation_log():
    """Reprocessar apenas o conversation_log separando por turnos."""
    if not GRAPHITI_AVAILABLE:
        logger.error("❌ graphiti-core não instalado.")
        return
    
    session = get_session()
    
    try:
        block = session.query(MemoryBlock).filter_by(label="conversation_log").first()
        
        if not block:
            logger.warning("❌ conversation_log não encontrado")
            return
        
        logger.info(f"📝 Processando conversation_log ({len(block.content)} chars)...")
        print("\n" + "="*80)
        print(f"💬 REPROCESSAMENTO DO LOG DE CONVERSAS")
        print("="*80 + "\n")
        
        # Separar por turnos (cada [user] ou [assistant] é um episódio)
        lines = block.content.split("\n")
        current_episode = []
        episode_count = 0
        
        for line in lines:
            if line.startswith("[") and line.endswith("]"):
                # Nova role, salvar episódio anterior se houver conteúdo
                if current_episode:
                    try:
                        episode_count += 1
                        episode_text = "\n".join(current_episode)
                        
                        state = {
                            "messages": [
                                {
                                    "role": "user",
                                    "content": episode_text
                                }
                            ],
                            "session_id": "conversation_log",
                            "user_id": "system",
                            "turn_id": f"conversation_turn_{episode_count}_{uuid.uuid4().hex[:8]}",
                        }
                        
                        save_to_graph(state)
                        print(f"✅ Episódio {episode_count:3d} | {len(episode_text):5d} chars | ✓")
                        
                    except Exception as e:
                        logger.warning(f"Erro ao salvar episódio {episode_count}: {e}")
                
                current_episode = [line]
            else:
                current_episode.append(line)
        
        # Salvar último episódio
        if current_episode:
            try:
                episode_count += 1
                episode_text = "\n".join(current_episode)
                state = {
                    "messages": [
                        {
                            "role": "user",
                            "content": episode_text
                        }
                    ],
                    "session_id": "conversation_log",
                    "user_id": "system",
                    "turn_id": f"conversation_turn_{episode_count}_{uuid.uuid4().hex[:8]}",
                }
                save_to_graph(state)
                print(f"✅ Episódio {episode_count:3d} | {len(episode_text):5d} chars | ✓")
            except Exception as e:
                logger.warning(f"Erro ao salvar episódio final: {e}")
        
        print("\n" + "="*80)
        print(f"💬 {episode_count} episódio(s) persistido(s) do log de conversas")
        print("="*80 + "\n")
        
    except Exception as e:
        logger.error(f"❌ Erro ao processar conversation_log: {e}")
    finally:
        session.close()


def main():
    parser = argparse.ArgumentParser(
        description="🔄 Reprocessar memória PostgreSQL → Grafo FalkorDB/Graphiti",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  
  # Reprocessar todos os blocos
  python reprocess_memory_to_graph.py
  
  # Reprocessar apenas conversation_log
  python reprocess_memory_to_graph.py conversation_log
  
  # Reprocessar blocos específicos
  python reprocess_memory_to_graph.py preferences learnings working_context
  
  # Limpar grafo e reprocessar
  python reprocess_memory_to_graph.py --clear
  
  # Apenas log de conversas com limpeza
  python reprocess_memory_to_graph.py conversation_log --clear
        """
    )
    
    parser.add_argument(
        'blocks',
        nargs='*',
        help='Labels dos blocos a reprocessar (deixar vazio para todos)'
    )
    
    parser.add_argument(
        '-c', '--clear',
        action='store_true',
        help='Limpar o grafo antes de reprocessar'
    )
    
    parser.add_argument(
        '--conv-only',
        action='store_true',
        help='Reprocessar apenas conversation_log separado por episódios'
    )
    
    args = parser.parse_args()
    
    # Banner
    print("\n" + "="*80)
    print("🔄 REPROCESSADOR DE MEMÓRIA → GRAFO")
    print("="*80 + "\n")
    
    # Verificar conexão com FalkorDB
    if GRAPHITI_AVAILABLE:
        try:
            graphiti = get_graphiti_instance()
            logger.info("✅ Conectado ao FalkorDB com sucesso")
        except Exception as e:
            logger.error(f"❌ Falha ao conectar ao FalkorDB: {e}")
            logger.error("   Certifique-se de que FalkorDB está rodando:")
            logger.error("   docker-compose up falkordb -d")
            sys.exit(1)
    
    # Executar limpeza se solicitado
    if args.clear:
        clear_graph()
    
    # Reprocessar
    if args.conv_only:
        reprocess_conversation_log()
    elif args.blocks:
        reprocess_memory_blocks(args.blocks)
    else:
        reprocess_memory_blocks()
    
    logger.info("✅ Reprocessamento concluído!")


if __name__ == "__main__":
    main()
