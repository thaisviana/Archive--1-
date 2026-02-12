# 🤖 Sistema de Memória Persistente para Agentes com LLM

Uma solução completa de **armazenamento de memória persistente** para agentes de IA que mantêm contexto sobre usuários, preferências e histórico de interações.

## 📋 Objetivo do Projeto

Este projeto implementa um sistema robusto que permite agentes de IA:

- **Armazenar informações persistentes** sobre usuários em blocos de memória versionados  
- **Acessar contexto dinamicamente** via middleware que injeta memória antes de chamadas ao LLM  
- **Gerenciar tokens** e comprimir memória quando necessário  
- **Rastrear histórico completo** de todas as edições e mudanças  
- **Integrar com OpenAI GPT** para respostas inteligentes baseadas em memória  
- **Funcionar offline** com consultas diretas ao banco sem dependência de LLM  

- **Exemplo prático**: Um agente conhece João Silva, sabe que ele é Software Engineer, lembra-se de suas preferências e histórico de interações passadas, e usa essas informações para fornecer respostas mais precisas e contextualizadas.

---

##  Guia de Instalação Rápida

### Pré-requisitos

-  **Python 3.12+** (não funciona com 3.9.x)
-  **Docker Desktop** instalado e rodando
-  **OpenAI API Key** (opcional, apenas para testes com LLM)
-  **macOS/Linux/Windows** com terminal/PowerShell

### Instalação em 5 passos


#### 2️⃣ Criar ambiente virtual

```bash
cd /path/para/seu/projeto
python3.12 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# ou
.venv\Scripts\activate     # Windows
```

#### 3️⃣ Instalar dependências

```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

#### 4️⃣ Configurar variáveis de ambiente

```bash
cp .env.example .env
# Edite .env e adicione suas credenciais:
# DATABASE_URL=postgresql://user:password@localhost:5432/agent_memory
# OPENAI_API_KEY=sk-proj-seu-api-key-aqui
```

#### 5️⃣ Iniciar PostgreSQL e banco de dados

```bash
# Criar container PostgreSQL
docker run --name agent_pg \
  -e POSTGRES_USER=user \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=agent_memory \
  -p 5432:5432 \
  -d postgres:15-alpine

# Aguardar alguns segundos e inicializar banco
sleep 5
PYTHONPATH=. python references/sqlalchemy_models.py
```


---

## 🧪 Rodando os Testes

Todos os testes podem ser executados individualmente para verificar diferentes aspectos do sistema:

### Teste: Ingestão de Dados de Memória

Popula os 6 blocos padrão com dados de exemplo (João Silva):

```bash
PYTHONPATH=. python test_memory_ingestion.py
```

**Resultado esperado:**
```
✅ Memória inicializada com 6 blocos padrão
  • persona
  • user_profile
  • preferences
  • working_context
  • learnings
  • custom

✅ Dados ingestionados: João Silva (Software Engineer)
📊 Estatísticas:
   - Total de blocos: 6
   - Históricos de edição: 1
```

### Teste 2️⃣: Consulta de Memória (SEM LLM) ⭐ RECOMENDADO

Consulta o banco de dados diretamente (não requer OpenAI API):

```bash
PYTHONPATH=. python test_memory_direct.py
```

**Resultado esperado:**
```
🔍 Consultando: "Qual é o role profissional de João?"

✅ Agente responde:
"O role profissional de João é Software Engineer. 
Ele trabalha com desenvolvimento de software, código limpo e arquitetura de sistemas."
```

### Teste 3️⃣: Teste de Middleware

Valida injeção de contexto, contagem de tokens e compressão:

```bash
PYTHONPATH=. python test_middleware.py
```

**Resultado esperado:**
```
✅ MemoryInjectionMiddleware: OK (contexto injetado)
✅ TokenManagementMiddleware: OK (16 tokens contados)
✅ MemoryRethinkMiddleware: OK (bloco marcado para compressão)
```

### Teste 4️⃣: Verificação de Montagem do Agente

Confirma que o agente está assemblado corretamente com todas as ferramentas:

```bash
PYTHONPATH=. python test_deepagents_ready.py
```

**Resultado esperado:**
```
✅ Agente montado com sucesso
✅ 8 ferramentas de memória carregadas:
   1. view_memory_blocks
   2. insert_memory_block
   3. replace_memory_content
   4. rethink_memory_block
   5. create_memory_block
   6. delete_memory_block
   7. rename_memory_block
   8. finish_memory_edits
```

### Teste 5️⃣: Integração com LLM (Requer OpenAI API Key)

Executa o ciclo completo com chamada ao LLM OpenAI:

```bash
set -a && source .env && set +a
PYTHONPATH=. python test_agent_query.py
```

**Resultado esperado:**
```
🤖 Agente inicializado com sucesso
💬 Pergunta: "Qual é o role profissional de João?"

✅ Resposta via LLM (GPT-4):
[Resposta completa contextualizada]
```

**Nota**: Se receber erro SSL, use o **Teste 2** como alternativa (funciona sem API).

---

## 📦 Dependências Principais

| Pacote | Versão | Propósito |
|--------|--------|----------|
| **deepagents** | 0.4.1 | Orquestração e middleware de agentes |
| **langchain** | 1.2.10 | Chains e engines de LLM |
| **langgraph** | 1.0.8 | Graphs e state management |
| **llama-index** | 0.14.14 | Framework RAG |
| **sqlalchemy** | 2.0.46 | ORM e queries SQL |
| **psycopg** | 3.3.2 | Driver PostgreSQL |
| **asyncpg** | 0.31.0 | PostgreSQL assíncrono |
| **pgvector** | 0.4.2 | Suporte a embeddings |
| **graphiti-core** | 0.27.1 | Knowledge graph (FalkorDB) |
| **tiktoken** | 0.12.0 | Contagem de tokens |
| **python-dotenv** | 1.2.1 | Variáveis de ambiente |
| **langfuse** | 3.14.1 | Observabilidade de LLM |
| **pytest** | 9.0.2 | Framework de testes |

**Lista completa:** Ver [requirements.txt](requirements.txt) (recomendado para instalar)  
**Todas as dependências transitivas:** Ver [requirements-full.txt](requirements-full.txt)


## 🧠 Sistema de Memória

O agente mantém **6 blocos de memória versionados** que armazenam informações sobre usuários:

| Bloco | Limite | Descrição | Read-Only |
|-------|--------|-----------|-----------|
| **persona** | 2000 chars | Personalidade e objetivo do agente | ✅ Sim |
| **user_profile** | 4000 chars | Informações pessoais e profissionais do usuário | ❌ Não |
| **preferences** | 1500 chars | Preferências de comunicação, idioma, formato | ❌ Não |
| **working_context** | 3000 chars | Contexto atual, tarefas em andamento | ❌ Não |
| **learnings** | 2500 chars | Fatos aprendidos sobre o usuário | ❌ Não |
| **custom** | 5000 chars | Campo extensível para dados customizados | ❌ Não |

Cada bloco inclui:
- ✅ **Versionamento completo** - Histórico de todas as edições
- 🔒 **Flag de read-only** - Proteção contra modificação acidental
- ⏰ **Timestamps** - Criação e modificação
- 📊 **Limite de caracteres** - Evita crescimento descontrolado

### 8️⃣ Ferramentas de Memória Disponíveis

O agente pode usar estas ferramentas para manipular memória:

#### 1. `view_memory_blocks(block_name=None)`
Visualiza conteúdo de blocos específicos ou todos

```python
# Ver um bloco
view_memory_blocks("user_profile")

# Ver todos os blocos
view_memory_blocks()
```

#### 2. `insert_memory_block(block_name, content)`
Adiciona conteúdo ao final de um bloco

```python
insert_memory_block("user_profile", "Novo fato sobre João")
```

#### 3. `replace_memory_content(block_name, old_text, new_text)`
Substitui um trecho específico

```python
replace_memory_content("user_profile", "Engineer", "Senior Engineer")
```

#### 4. `rethink_memory_block(block_name, new_content)`
Reescreve completamente um bloco (cria nova versão)

```python
rethink_memory_block("user_profile", "Novo conteúdo reescrito completamente")
```

#### 5. `create_memory_block(name, limit=3000, readonly=False)`
Cria um novo bloco customizado

```python
create_memory_block("customer_interactions", limit=3000)
```

#### 6. `delete_memory_block(block_name)`
Deleta um bloco

```python
delete_memory_block("custom")
```

#### 7. `rename_memory_block(old_name, new_name)`
Renomeia um bloco

```python
rename_memory_block("custom", "notes")
```

#### 8. `finish_memory_edits(summary)`
Marca fim de sessão com resumo

```python
finish_memory_edits("Atualizado email e role de João")
```

---

## 🏗️ Arquitetura

```
┌──────────────────────────────────────────────────────────────┐
│                   Pergunta do Usuário                         │
│              "Qual é o role profissional de João?"           │
└──────────────────┬───────────────────────────────────────────┘
                   │
                   ▼
        ┌─────────────────────────┐
        │  MemoryInjection        │  Carrega blocos do PostgreSQL
        │  Middleware             │  Formata como contexto
        └──────────┬──────────────┘  Prepende à mensagem
                   │
                   ▼
        ┌─────────────────────────┐
        │  TokenManagement        │  Conta tokens (tiktoken)
        │  Middleware             │  Alerta se > 8000 tokens
        └──────────┬──────────────┘  Dispara compressão
                   │
                   ▼
        ┌─────────────────────────┐
        │   Agente DeepAgents     │  Raciocina com LLM (OpenAI)
        │   com 8 ferramentas     │  Decide quais ferramentas usar
        └──────────┬──────────────┘  Gera resposta
                   │
                   ▼
        ┌─────────────────────────┐
        │  MemoryRethink          │  Monitora tamanho dos blocos
        │  Middleware             │  Marca para compressão @ 80%
        └──────────┬──────────────┘  Atualiza histórico
                   │
                   ▼
        ┌─────────────────────────┐
        │  PostgreSQL + SQAlchemy │  Persiste mudanças
        │  + Version Control      │  Mantém histórico completo
        └─────────────────────────┘

        ✅ Resposta: "Software Engineer"
```

---

## 💻 Como Executar Diferentes Cenários

### Cenário 1: Apenas Memória (Offline, sem LLM)

```bash
PYTHONPATH=. python test_memory_direct.py
```

➕ **Vantagens:**
- Sem dependência de API OpenAI
- Sem problemas de SSL
- Funciona offline
- Rápido

❌ **Limitações:**
- Respostas não são geradas por LLM
- Apenas consultas diretas

### Cenário 2: Com LLM (Requer OpenAI API Key)

```bash
set -a && source .env && set +a
PYTHONPATH=. python test_agent_query.py
```

➕ **Vantagens:**
- Respostas inteligentes com raciocínio do LLM
- Contexto injetado automaticamente
- Middleware gerencia tokens

❌ **Limitações:**
- Requer OpenAI API Key válida
- Custos por token
- Possíveis erros SSL (resolver com certificados)

### Cenário 3: Desenvolvimento (Adicionar Novas Funcionalidades)

```bash
# Editar seu código
vim references/memory_tools.py

# Testar middlware
PYTHONPATH=. python test_middleware.py

# Testar agente assembly
PYTHONPATH=. python test_deepagents_ready.py

# Ingerir dados
PYTHONPATH=. python test_memory_ingestion.py

# Testar resultado
PYTHONPATH=. python test_memory_direct.py
```

---

## 🛠️ Development & Customização

### Adicionar Nova Dependência

```bash
# 1. Instalar
pip install novo-pacote==1.2.3

# 2. Atualizar requirements.txt manualmente
echo "novo-pacote==1.2.3" >> requirements.txt

# 3. Atualizar requirements-full.txt
pip freeze > requirements-full.txt

# 4. Commitar
git add requirements*.txt
git commit -m "Add: novo-pacote==1.2.3"
```

### Adicionar Nova Ferramenta de Memória

1. Edite `references/memory_tools.py`
2. Use decorator `@tool` do LangChain
3. Adicione docstring clara
4. Teste com `test_middleware.py`
5. Execute `test_memory_ingestion.py` para validar

Exemplo:
```python
from langchain_core.tools import tool

@tool
def minha_nova_ferramenta(param1: str) -> str:
    """Descrição clara da ferramenta."""
    # Sua implementação
    return resultado
```

### Adicionar Novo Bloco de Memória

Edite `references/sqlalchemy_models.py`:

```python
def init_default_blocks():
    # Adicione seu bloco
    novo_bloco = MemoryBlock(
        name="meu_bloco",
        content="Conteúdo inicial",
        char_limit=3000,
        read_only=False
    )
    session.add(novo_bloco)
    session.commit()
```

---

## ❌ Resolução de Problemas

### Problema: "connection refused" ao conectar PostgreSQL

```bash
# Verificar se container está rodando
docker ps | grep agent_pg

# Se não estiver, criar:
docker run --name agent_pg \
  -e POSTGRES_USER=user \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=agent_memory \
  -p 5432:5432 \
  -d postgres:15-alpine

# Aguardar inicialização
sleep 5

# Testar conexão
PYTHONPATH=. python test_memory_ingestion.py
```

### Problema: "ModuleNotFoundError: No module named 'references'"

```bash
# Certifique-se de estar na raiz do projeto
pwd

# Execute COM PYTHONPATH
PYTHONPATH=. python test_memory_ingestion.py

# OU adicione ao seu shell profile:
export PYTHONPATH=.:$PYTHONPATH
```

### Problema: "CERTIFICATE_VERIFY_FAILED" com OpenAI

Solução 1 - Usar versão offline (recomendado):
```bash
PYTHONPATH=. python test_memory_direct.py
```

Solução 2 - Instalar certificados (macOS):
```bash
/Applications/Python\ 3.12/Install\ Certificates.command
```

Solução 3 - Atualizar certifi:
```bash
pip install --upgrade certifi
```

### Problema: "ImportError: cannot import name 'DeepAgents'"

```bash
# Verificar instalação
pip list | grep deepagents

# Se não estiver:
pip install deepagents==0.4.1

# Verificar Python version
python --version  # Deve ser 3.12+
```

### Problema: Banco inconsistente ou corrupto

Reset completo:
```bash
# Parar container
docker stop agent_pg
docker rm agent_pg

# Recriar
docker run --name agent_pg \
  -e POSTGRES_USER=user \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=agent_memory \
  -p 5432:5432 \
  -d postgres:15-alpine

sleep 5

# Reinitializar
PYTHONPATH=. python references/sqlalchemy_models.py

# Reingerir dados
PYTHONPATH=. python test_memory_ingestion.py
```

---

## 📚 Documentação Completa

| Arquivo | Conteúdo |
|---------|----------|
| [SKILL.md](SKILL.md) | Visão geral geral e diagrams |
| [references/architecture-overview.md](references/architecture-overview.md) | Arquitetura técnica |
| [references/memory-system.md](references/memory-system.md) | Especificação do sistema de memória |
| [references/agent-orchestration.md](references/agent-orchestration.md) | Orquestração de agente |
| [references/rag-pipeline.md](references/rag-pipeline.md) | Pipeline RAG (embeddings) |

---
