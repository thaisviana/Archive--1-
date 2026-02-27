#!/usr/bin/env python3
"""
Script para buscar conteúdo nos blocos de memória do agente.
"""
import os
import re
import argparse
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
from references.sqlalchemy_models import MemoryBlock, BlockHistory, get_session

ROOT_DIR = Path(__file__).resolve()
load_dotenv(ROOT_DIR.parent / ".env")

# Inicializar cliente OpenAI
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


def highlight_match(text, pattern, case_sensitive=False):
    """Destaca o termo de busca no texto."""
    flags = 0 if case_sensitive else re.IGNORECASE
    
    def replacer(match):
        return f"🔍 [{match.group()}] 🔍"
    
    return re.sub(pattern, replacer, text, flags=flags)


def get_context(text, match_pos, context_chars=100):
    """Retorna o contexto ao redor de uma correspondência."""
    start = max(0, match_pos - context_chars)
    end = min(len(text), match_pos + context_chars)
    
    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(text) else ""
    
    return prefix + text[start:end] + suffix


def summarize_with_llm(query, results):
    """
    Usa LLM para resumir os resultados da busca e responder à pergunta.
    
    Args:
        query: A pergunta ou termo de busca do usuário
        results: Lista de dicionários com 'block' e 'matches'
    
    Returns:
        Resposta formatada pela LLM
    """
    # Construir contexto com os blocos encontrados
    context_parts = []
    
    for result in results:
        block = result['block']
        context_parts.append(f"\n## Bloco: {block.label}")
        context_parts.append(f"Atualizado em: {block.updated_at}")
        context_parts.append(f"Conteúdo completo:\n{block.content}")
        context_parts.append("-" * 80)
    
    context = "\n".join(context_parts)
    
    # Preparar prompt para a LLM
    system_prompt = """Você é um assistente especializado em analisar blocos de memória de um agente de IA.

Sua tarefa é:
1. Analisar o conteúdo dos blocos de memória fornecidos
2. Responder à pergunta do usuário de forma concisa e precisa
3. Citar informações relevantes dos blocos quando apropriado
4. Se a informação não estiver disponível, dizer claramente

Formate sua resposta de forma clara e organizada."""
    
    user_prompt = f"""Pergunta do usuário: {query}

### Blocos de Memória Encontrados:
{context}

---

Com base nos blocos de memória acima, responda à pergunta do usuário de forma clara e objetiva."""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        return f"❌ Erro ao gerar resposta com LLM: {e}\n\nMostrando resultados brutos..."


def search_in_blocks(query, blocks=None, case_sensitive=False, show_context=True, 
                     context_chars=150, include_history=False, use_llm=True):
    """
    Busca um termo nos blocos de memória.
    
    Args:
        query: Termo de busca (pode ser regex ou pergunta natural)
        blocks: Lista de labels de blocos específicos (ou None para todos)
        case_sensitive: Se a busca deve ser case-sensitive
        show_context: Se deve mostrar contexto ao redor das correspondências
        context_chars: Número de caracteres de contexto em cada lado
        include_history: Se deve incluir histórico de versões na busca
        use_llm: Se deve usar LLM para resumir e responder (padrão: True)
    """
    session = get_session()
    results = []
    
    # Buscar blocos
    query_obj = session.query(MemoryBlock)
    if blocks:
        query_obj = query_obj.filter(MemoryBlock.label.in_(blocks))
    
    all_blocks = query_obj.all()
    
    if not all_blocks:
        print("❌ Nenhum bloco de memória encontrado.")
        session.close()
        return
    
    # Se usar LLM e query parecer uma pergunta, retornar todos os blocos para análise
    question_indicators = ['?', 'qual', 'quando', 'como', 'por que', 'porque', 'onde', 'quem', 
                           'o que', 'quantos', 'me fale', 'explique', 'descreva', 'mostre']
    is_question = use_llm and any(indicator in query.lower() for indicator in question_indicators)
    
    if is_question:
        # Para perguntas, incluir todos os blocos encontrados
        for block in all_blocks:
            results.append({
                'block': block,
                'matches': [{'type': 'current', 'position': 0, 'text': '', 'timestamp': block.updated_at}]
            })
    else:
        # Para buscas de termos específicos, fazer busca por padrão
        flags = 0 if case_sensitive else re.IGNORECASE
        try:
            pattern = re.compile(query, flags)
        except re.error as e:
            print(f"❌ Erro na expressão regular: {e}")
            session.close()
            return
        
        # Buscar em cada bloco
        for block in all_blocks:
            matches = []
            
            # Buscar no conteúdo atual
            for match in pattern.finditer(block.content):
                if show_context:
                    context = get_context(block.content, match.start(), context_chars)
                    highlighted = highlight_match(context, query, case_sensitive)
                else:
                    highlighted = highlight_match(match.group(), query, case_sensitive)
                
                matches.append({
                    'type': 'current',
                    'position': match.start(),
                    'text': highlighted,
                    'timestamp': block.updated_at
                })
            
            # Buscar no histórico se solicitado
            if include_history and block.history:
                for hist in block.history:
                    for match in pattern.finditer(hist.content):
                        if show_context:
                            context = get_context(hist.content, match.start(), context_chars)
                            highlighted = highlight_match(context, query, case_sensitive)
                        else:
                            highlighted = highlight_match(match.group(), query, case_sensitive)
                        
                        matches.append({
                            'type': 'history',
                            'position': match.start(),
                            'text': highlighted,
                            'timestamp': hist.created_at
                        })
            
            if matches:
                results.append({
                    'block': block,
                    'matches': matches
                })
    
    session.close()
    
    # Exibir resultados
    if not results:
        print(f"\n❌ Nenhuma correspondência encontrada para: '{query}'")
        return
    
    # Se usar LLM, gerar resposta inteligente
    if use_llm:
        print("\n" + "="*80)
        print(f"💬 RESPOSTA PARA: '{query}'")
        print("="*80 + "\n")
        
        answer = summarize_with_llm(query, results)
        print(answer)
        
        print("\n" + "="*80)
        print(f"📊 Baseado em {sum(len(r['matches']) for r in results)} correspondência(s) em {len(results)} bloco(s)")
        print("="*80 + "\n")
        return
    
    # Caso contrário, mostrar resultados brutos
    total_matches = sum(len(r['matches']) for r in results)
    print("\n" + "="*80)
    print(f"🔍 RESULTADOS DA BUSCA: '{query}'")
    print(f"📊 {total_matches} correspondência(s) em {len(results)} bloco(s)")
    print("="*80 + "\n")
    
    for result in results:
        block = result['block']
        matches = result['matches']
        
        print(f"📌 {block.label.upper()}")
        print(f"   {len(matches)} correspondência(s) encontrada(s)")
        print(f"   Atualizado em: {block.updated_at}")
        print("   " + "-"*76)
        
        for i, match in enumerate(matches, 1):
            match_type = "📄 Versão atual" if match['type'] == 'current' else f"📜 Histórico ({match['timestamp']})"
            print(f"\n   {i}. {match_type}")
            print(f"      Posição: {match['position']}")
            print(f"\n      {match['text']}")
        
        print("\n   " + "-"*76 + "\n")
    
    print("="*80 + "\n")


def list_available_blocks():
    """Lista os blocos de memória disponíveis."""
    session = get_session()
    blocks = session.query(MemoryBlock).all()
    
    if not blocks:
        print("❌ Nenhum bloco de memória encontrado.")
        session.close()
        return
    
    print("\n" + "="*80)
    print("📚 BLOCOS DE MEMÓRIA DISPONÍVEIS")
    print("="*80 + "\n")
    
    for block in blocks:
        size_kb = len(block.content) / 1024
        history_count = len(block.history) if block.history else 0
        
        print(f"📌 {block.label}")
        print(f"   Descrição: {block.description or 'Sem descrição'}")
        print(f"   Tamanho: {size_kb:.2f} KB ({len(block.content)} caracteres)")
        print(f"   Limite: {block.char_limit} caracteres")
        print(f"   Read-only: {'✅' if block.read_only else '❌'}")
        print(f"   Versões no histórico: {history_count}")
        print()
    
    print("="*80 + "\n")
    session.close()


def search_by_date(start_date=None, end_date=None, blocks=None):
    """Busca blocos atualizados em um período específico."""
    session = get_session()
    
    query_obj = session.query(MemoryBlock)
    if blocks:
        query_obj = query_obj.filter(MemoryBlock.label.in_(blocks))
    
    if start_date:
        query_obj = query_obj.filter(MemoryBlock.updated_at >= start_date)
    if end_date:
        query_obj = query_obj.filter(MemoryBlock.updated_at <= end_date)
    
    results = query_obj.order_by(MemoryBlock.updated_at.desc()).all()
    
    if not results:
        print("❌ Nenhum bloco encontrado no período especificado.")
        session.close()
        return
    
    print("\n" + "="*80)
    print(f"📅 BLOCOS ATUALIZADOS")
    if start_date:
        print(f"   De: {start_date}")
    if end_date:
        print(f"   Até: {end_date}")
    print("="*80 + "\n")
    
    for block in results:
        print(f"📌 {block.label}")
        print(f"   Atualizado em: {block.updated_at}")
        print(f"   Tamanho: {len(block.content)} caracteres")
        print(f"\n   Prévia:")
        preview = block.content[:200].replace("\n", " ")
        print(f"   {preview}...")
        print()
    
    print("="*80 + "\n")
    session.close()


def main():
    parser = argparse.ArgumentParser(
        description="🔍 Busca conteúdo nos blocos de memória do agente e responde perguntas usando LLM",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  
  # Fazer uma pergunta (usa LLM para responder com base na memória)
  python search_memory.py "qual foi o último PDF enviado?"
  
  # Perguntar sobre conversas anteriores
  python search_memory.py "sobre o que conversamos?"
  
  # Buscar em blocos específicos
  python search_memory.py "preferências do usuário" --blocks preferences user_profile
  
  # Ver resultados brutos sem usar LLM
  python search_memory.py "agente" --raw
  
  # Busca case-sensitive com resultados brutos
  python search_memory.py "OpenAI" --case-sensitive --raw
  
  # Incluir histórico de versões na busca
  python search_memory.py "o que aprendi sobre memória?" --history
  
  # Buscar usando regex (modo raw)
  python search_memory.py "pdf|document|arquivo" --raw
  
  # Listar blocos disponíveis
  python search_memory.py --list
  
  # Buscar blocos atualizados hoje
  python search_memory.py --date-from "2026-02-27"
  
  # Buscar sem contexto (apenas correspondências exatas)
  python search_memory.py "test" --no-context --raw
        """
    )
    
    parser.add_argument(
        'query',
        nargs='?',
        help='Pergunta em linguagem natural ou termo de busca/expressão regular'
    )
    
    parser.add_argument(
        '-b', '--blocks',
        nargs='+',
        help='Buscar apenas em blocos específicos (labels separados por espaço)'
    )
    
    parser.add_argument(
        '-c', '--case-sensitive',
        action='store_true',
        help='Busca case-sensitive (padrão: case-insensitive)'
    )
    
    parser.add_argument(
        '-n', '--no-context',
        action='store_true',
        help='Não mostrar contexto ao redor das correspondências'
    )
    
    parser.add_argument(
        '-x', '--context-size',
        type=int,
        default=150,
        help='Número de caracteres de contexto (padrão: 150)'
    )
    
    parser.add_argument(
        '-H', '--history',
        action='store_true',
        help='Incluir histórico de versões na busca'
    )
    
    parser.add_argument(
        '-r', '--raw',
        action='store_true',
        help='Mostrar resultados brutos sem usar LLM (padrão: usa LLM para resumir)'
    )
    
    parser.add_argument(
        '-l', '--list',
        action='store_true',
        help='Listar blocos de memória disponíveis'
    )
    
    parser.add_argument(
        '--date-from',
        type=str,
        help='Buscar blocos atualizados a partir desta data (YYYY-MM-DD)'
    )
    
    parser.add_argument(
        '--date-to',
        type=str,
        help='Buscar blocos atualizados até esta data (YYYY-MM-DD)'
    )
    
    args = parser.parse_args()
    
    # Listar blocos
    if args.list:
        list_available_blocks()
        return
    
    # Buscar por data
    if args.date_from or args.date_to:
        start = datetime.fromisoformat(args.date_from) if args.date_from else None
        end = datetime.fromisoformat(args.date_to) if args.date_to else None
        search_by_date(start, end, args.blocks)
        return
    
    # Busca por termo
    if not args.query:
        parser.print_help()
        return
    
    search_in_blocks(
        query=args.query,
        blocks=args.blocks,
        case_sensitive=args.case_sensitive,
        show_context=not args.no_context,
        context_chars=args.context_size,
        include_history=args.history,
        use_llm=not args.raw
    )


if __name__ == "__main__":
    main()
