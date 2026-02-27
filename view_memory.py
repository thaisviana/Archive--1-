#!/usr/bin/env python3
"""
Script para visualizar blocos de memória salvos no banco de dados.
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from references.sqlalchemy_models import MemoryBlock, get_session

ROOT_DIR = Path(__file__).resolve()
load_dotenv(ROOT_DIR.parent / ".env")

def view_all_memory():
    """Exibe todos os blocos de memória."""
    session = get_session()
    blocks = session.query(MemoryBlock).all()
    
    if not blocks:
        print("❌ Nenhum bloco de memória encontrado.")
        return
    
    print("\n" + "="*80)
    print("📚 BLOCOS DE MEMÓRIA SALVOS")
    print("="*80 + "\n")
    
    for block in blocks:
        print(f"📌 {block.label.upper()}")
        print(f"   Limite: {block.char_limit} caracteres")
        print(f"   Read-only: {'✅ Sim' if block.read_only else '❌ Não'}")
        print(f"   Criado em: {block.created_at}")
        print(f"   Atualizado em: {block.updated_at}")
        print(f"\n   Conteúdo ({len(block.content)} chars):")
        print("   " + "-"*76)
        
        # Mostrar conteúdo com indentação
        for line in block.content.split("\n"):
            print(f"   {line}")
        
        print("   " + "-"*76)
        
        # Mostrar histórico
        if block.history:
            print(f"\n   📜 Histórico ({len(block.history)} versões):")
            for i, hist in enumerate(block.history[-3:], 1):  # Últimas 3 versões
                print(f"      v{len(block.history)-i}: {hist.created_at}")
        
        print("\n" + "="*80 + "\n")
    
    session.close()

def view_conversation_log():
    """Exibe apenas o log de conversas."""
    session = get_session()
    block = session.query(MemoryBlock).filter_by(label="conversation_log").first()
    
    if not block:
        print("❌ Nenhuma conversa registrada ainda.")
        session.close()
        return
    
    print("\n" + "="*80)
    print("💬 LOG DE CONVERSAS")
    print("="*80 + "\n")
    print(block.content)
    print("\n" + "="*80 + "\n")
    session.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "conv":
        view_conversation_log()
    else:
        view_all_memory()
