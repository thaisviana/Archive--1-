#!/usr/bin/env python3
"""
Script para testar o agente com memória sem o chat.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))
load_dotenv(ROOT_DIR / ".env")

# Configurar SSL
import certifi
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

from references.agent_assembly import run_agent
from references.agent_init import get_agent
from references.sqlalchemy_models import MemoryBlock, get_session

def test_agent():
    print("\n" + "="*80)
    print("🧪 TESTE DE AGENTE COM MEMÓRIA")
    print("="*80 + "\n")
    
    # Ver memória antes
    session = get_session()
    blocks = session.query(MemoryBlock).all()
    print(f"📚 Blocos de memória disponíveis: {len(blocks)}")
    for block in blocks:
        print(f"   - {block.label}: {len(block.content)} chars")
    session.close()
    
    print("\n" + "-"*80)
    
    # Montar agente
    print("🤖 Montando agente...")
    try:
        agent = get_agent()
        print("✅ Agente montado com sucesso\n")
    except Exception as e:
        print(f"❌ Erro ao montar agente: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Fazer pergunta
    user_input = "Qual é o role profissional registrado na memória? Responda em português."
    print(f"👤 Pergunta: {user_input}\n")
    print("-"*80)
    
    try:
        result = run_agent(
            agent=agent,
            user_input=user_input,
            session_id="test_session",
            user_id="test_user"
        )
        
        print("\n" + "-"*80)
        print("\n🤖 Resposta do agente:\n")
        
        # Extrair resposta
        messages = result.get("messages", []) if isinstance(result, dict) else []
        assistant_reply = ""
        for msg in reversed(messages):
            if isinstance(msg, dict) and msg.get("role") == "assistant":
                assistant_reply = msg.get("content", "")
                break
        
        if assistant_reply:
            print(assistant_reply)
        else:
            print("❌ Nenhuma resposta do assistente encontrada")
            print(f"Resultado completo: {result}")
        
        print("\n" + "="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Erro ao executar agente: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_agent()
