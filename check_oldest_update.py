#!/usr/bin/env python3

from references.sqlalchemy_models import get_session, MemoryBlock, BlockHistory
from datetime import datetime

session = get_session()

# Buscar a criação mais antiga
oldest_block = session.query(MemoryBlock).order_by(MemoryBlock.created_at).first()
oldest_history = session.query(BlockHistory).order_by(BlockHistory.created_at).first()

print("\n" + "="*80)
print("🕐 HISTÓRICO DE ATUALIZAÇÕES")
print("="*80 + "\n")

if oldest_block:
    print(f"📦 Bloco mais antigo:")
    print(f"   {oldest_block.label}")
    print(f"   Criado em: {oldest_block.created_at}")
    print(f"   Atualizado em: {oldest_block.updated_at}")

if oldest_history:
    print(f"\n📜 Versão mais antiga no histórico:")
    print(f"   Bloco: {oldest_history.block.label}")
    print(f"   Data: {oldest_history.created_at}")
    print(f"   Tamanho: {len(oldest_history.content)} caracteres")
else:
    print(f"\n📜 Nenhuma versão no histórico ainda")

# Mostrar timeline
print(f"\n⏱️ TIMELINE COMPLETA")
print("-"*80)

all_blocks = session.query(MemoryBlock).order_by(MemoryBlock.created_at).all()
for block in all_blocks:
    print(f"   {block.created_at} - {block.label} criado")

print("\n" + "="*80 + "\n")

session.close()
