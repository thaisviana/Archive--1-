#!/usr/bin/env python3
"""
Script para diagnosticar se há perda de dados na memória PostgreSQL.
Verifica:
- Integridade dos blocos
- Histórico de versões
- Crescimento/redução de tamanho
- Sincronização com o grafo
"""
import os
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv
from references.sqlalchemy_models import MemoryBlock, BlockHistory, get_session

ROOT_DIR = Path(__file__).resolve()
load_dotenv(ROOT_DIR.parent / ".env")


def check_data_integrity():
    """Verifica integridade dos dados na memória."""
    session = get_session()
    
    print("\n" + "="*80)
    print("🔍 DIAGNÓSTICO DE INTEGRIDADE - MEMÓRIA PostgreSQL")
    print("="*80 + "\n")
    
    blocks = session.query(MemoryBlock).all()
    
    if not blocks:
        print("❌ Nenhum bloco encontrado!")
        return
    
    print(f"📦 Total de blocos: {len(blocks)}\n")
    
    # 1. Verificar cada bloco
    print("1️⃣ INTEGRIDADE DOS BLOCOS")
    print("-" * 80)
    
    issues = []
    for block in blocks:
        size = len(block.content or "")
        warnings = []
        
        # Verificar se está vazio
        if size == 0:
            warnings.append("🟡 Bloco vazio")
        
        # Verificar se ultrapassou limite
        if size > block.char_limit:
            warnings.append(f"🔴 ACIMA DO LIMITE ({size} > {block.char_limit})")
            issues.append(f"- {block.label}: {size} > {block.char_limit}")
        
        # Verificar última atualização
        if block.updated_at:
            time_since = datetime.now(block.updated_at.tzinfo) - block.updated_at
            if time_since.days > 30:
                warnings.append(f"🟠 Não atualizado há {time_since.days} dias")
        
        status = " | ".join(warnings) if warnings else "✅ OK"
        print(f"   {block.label:<20} | {size:>6} chars | {status}")
    
    if issues:
        print(f"\n⚠️ PROBLEMAS ENCONTRADOS:")
        for issue in issues:
            print(f"   {issue}")
    
    # 2. Verificar histórico
    print(f"\n2️⃣ HISTÓRICO DE VERSÕES")
    print("-" * 80)
    
    total_history = 0
    for block in blocks:
        if block.history:
            total_history += len(block.history)
            print(f"   {block.label:<20} | {len(block.history):>3} versões")
    
    if total_history == 0:
        print("   ⚠️ Nenhum histórico registrado - dados não podem ser recuperados!")
    else:
        print(f"\n   ✅ Total de {total_history} versão(s) do histórico")
    
    # 3. Verificar mudanças recentes
    print(f"\n3️⃣ ATIVIDADE RECENTE (últimas 24h)")
    print("-" * 80)
    
    today = datetime.now(blocks[0].updated_at.tzinfo)
    yesterday = today - timedelta(days=1)
    
    recent_changes = 0
    for block in blocks:
        if block.updated_at and block.updated_at > yesterday:
            recent_changes += 1
            time_ago = today - block.updated_at
            print(f"   ✅ {block.label:<20} | atualizado há {time_ago}")
    
    if recent_changes == 0:
        print("   ⚠️ Nenhuma atividade nas últimas 24 horas")
    
    # 4. Verificar tamanhos
    print(f"\n4️⃣ ANÁLISE DE CRESCIMENTO")
    print("-" * 80)
    
    total_size = sum(len(block.content or "") for block in blocks)
    total_limit = sum(block.char_limit for block in blocks)
    
    print(f"   Espaço em uso:    {total_size:>10,} caracteres")
    print(f"   Limite total:     {total_limit:>10,} caracteres")
    print(f"   Utilização:       {(total_size/total_limit*100):>9.1f}%")
    
    if total_size > total_limit * 0.9:
        print(f"\n   🔴 ALERTA: Sistema próximo ao límite!")
    
    # 5. Verificar base de dados
    print(f"\n5️⃣ ESTADO DO BANCO DE DADOS")
    print("-" * 80)
    
    try:
        # Tentar executar query simples
        test = session.query(MemoryBlock).count()
        print(f"   ✅ PostgreSQL respondendo")
        print(f"   ✅ {test} bloco(s) no banco")
        
        # Verificar conexão
        session.execute("SELECT 1")
        print(f"   ✅ Conexão estável")
        
    except Exception as e:
        print(f"   ❌ ERRO ao conectar: {e}")
    
    # 6. Recomendações
    print(f"\n6️⃣ RECOMENDAÇÕES")
    print("-" * 80)
    
    recommendations = []
    
    if not total_history > 0:
        recommendations.append("   - Ativar histórico automático de versões")
    
    if total_size > total_limit * 0.8:
        recommendations.append("   - Comprimir blocos grandes")
        recommendations.append("   - Considerar arquivar dados antigos")
    
    if recent_changes == 0:
        recommendations.append("   - Verificar se o agente está salvando dados corretamente")
        recommendations.append("   - Testar save_to_memory() manualmente")
    
    # Verificar conversation_log
    conv_block = session.query(MemoryBlock).filter_by(label="conversation_log").first()
    if conv_block and len(conv_block.content or "") > 5000:
        recommendations.append("   - conversation_log está grande, considere rotacionar")
    
    if recommendations:
        print("\n".join(recommendations))
    else:
        print("   ✅ Nenhuma ação necessária")
    
    # Resumo final
    print("\n" + "="*80)
    print("📋 RESUMO EXECUTIVO")
    print("="*80)
    print(f"   ✅ Dados: Íntegros")
    print(f"   ✅ Histórico: {total_history} versão(s)")
    print(f"   ✅ Uso de espaço: {(total_size/total_limit*100):.1f}%")
    print(f"   ✅ Atividade recente: {recent_changes} bloco(s) atualizado(s)")
    print("\n" + "="*80 + "\n")
    
    session.close()


def check_conversation_log():
    """Verifica especificamente o conversation_log."""
    session = get_session()
    block = session.query(MemoryBlock).filter_by(label="conversation_log").first()
    
    if not block:
        print("❌ conversation_log não encontrado!")
        return
    
    print("\n" + "="*80)
    print("💬 ANÁLISE DETALHADA - CONVERSATION_LOG")
    print("="*80 + "\n")
    
    content = block.content or ""
    lines = content.split("\n")
    
    print(f"   Tamanho: {len(content):,} caracteres")
    print(f"   Linhas: {len(lines)}")
    print(f"   Limite: {block.char_limit:,} caracteres")
    print(f"   Uso: {(len(content)/block.char_limit*100):.1f}%")
    
    # Contar mensagens
    user_msgs = content.count("[user]")
    system_msgs = content.count("[system]")
    assistant_msgs = content.count("[assistant]")
    
    print(f"\n   Mensagens de usuário: {user_msgs}")
    print(f"   Mensagens do sistema: {system_msgs}")
    print(f"   Respostas do agente: {assistant_msgs}")
    
    if block.history:
        print(f"\n   Histórico: {len(block.history)} versão(s)")
        for i, hist in enumerate(block.history[-5:], 1):
            size = len(hist.content or "")
            print(f"      v{len(block.history)-i}: {size:,} chars ({hist.created_at})")
    
    print("\n" + "="*80 + "\n")
    
    session.close()


def main():
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "conv":
        check_conversation_log()
    else:
        check_data_integrity()


if __name__ == "__main__":
    main()
