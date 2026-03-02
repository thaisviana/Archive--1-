# 🤖 Sistema de Memória Persistente para Agentes com LLM

Uma solução  **armazenamento de memória persistente** para agentes de IA que mantêm contexto sobre usuários, preferências e histórico de interações.

## 📋 Objetivo do Projeto

Este projeto implementa um sistema robusto que permite agentes de IA:

- **Armazenar informações persistentes** sobre usuários em blocos de memória versionados  
- **Acessar contexto dinamicamente** via middleware que injeta memória antes de chamadas ao LLM  
- **Gerenciar tokens** e comprimir memória quando necessário  
- **Rastrear histórico completo** de todas as edições e mudanças  
- **Integrar com OpenAI GPT** para respostas inteligentes baseadas em memória  
- **Funcionar offline** com consultas diretas ao banco sem dependência de LLM  
- **Interface de chat web** com upload de PDFs e persistência de conversas
- **Busca inteligente por LLM** para consultar memória em linguagem natural

- **Exemplo prático**: Um agente conhece João Silva, sabe que ele é Software Engineer, lembra-se de suas preferências e histórico de interações passadas, e usa essas informações para fornecer respostas mais precisas e contextualizadas. Além disso, você pode fazer upload de PDFs através da interface web e depois perguntar "qual foi o último PDF que enviei?" - o agente responderá baseado no histórico de conversas salvo.

---

##  Guia de Instalação Rápida

### Pré-requisitos

-  **Python 3.12+** (não funciona com 3.9.x)
-  **Docker Desktop** instalado e rodando
-  **OpenAI API Key** (opcional, apenas para testes com LLM)
-  **macOS/Linux/Windows** com terminal/PowerShell

### Instalação 


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

## 📦 Dependências 

**Lista completa:** Ver [requirements.txt](requirements.txt) (recomendado para instalar)  
**Todas as dependências transitivas:** Ver [requirements-full.txt](requirements-full.txt)


## 🧠 Sistema de Memória

O agente mantém **blocos de memória versionados** que armazenam informações sobre usuários e conversas:

| Bloco | Limite | Descrição | Read-Only |
|-------|--------|-----------|-----------|
| **persona** | 2000 chars | Personalidade e objetivo do agente | ✅ Sim |
| **user_profile** | 3000 chars | Informações pessoais e profissionais do usuário | ❌ Não |
| **preferences** | 2000 chars | Preferências de comunicação, idioma, formato | ❌ Não |
| **working_context** | 4000 chars | Contexto atual, tarefas em andamento | ❌ Não |
| **learnings** | 3000 chars | Fatos aprendidos sobre o usuário | ❌ Não |
| **conversation_log** | 6000 chars | Log das conversas recentes e arquivos enviados | ❌ Não |

### 💬 Chat com Upload de PDFs

O sistema inclui uma interface web de chat que permite:

- **Conversar com o agente** através de interface web amigável
- **Fazer upload de arquivos PDF** que são extraídos e salvos na memória
- **Persistência automática** das conversas no bloco `conversation_log`
- **Contexto conversacional** - o agente acessa histórico de mensagens anteriores

#### Iniciar o servidor de chat

```bash
# Ativar ambiente virtual e iniciar servidor
source .venv/bin/activate
./start_chat.sh

# Ou manualmente na porta 8080
cd chat && python chat_server.py
```

Acesse em: **http://localhost:8080**

### 🔍 Busca Inteligente na Memória

Use o script `search_memory.py` para consultar a memória usando **linguagem natural com LLM**:

```bash
# Fazer perguntas sobre conversas anteriores
python search_memory.py "qual foi o último PDF enviado?"
python search_memory.py "sobre o que conversamos?"
python search_memory.py "o que está no log de conversas?"

# Buscar em blocos específicos
python search_memory.py "preferências do usuário" --blocks preferences user_profile

# Ver resultados brutos sem LLM (busca por regex)
python search_memory.py "agente" --raw

# Listar todos os blocos disponíveis
python search_memory.py --list

# Buscar blocos atualizados hoje
python search_memory.py --date-from "2026-02-27"

# Incluir histórico de versões na busca
python search_memory.py "o que aprendi?" --history
```

**Modos de operação:**
- **Modo LLM (padrão)**: Usa gpt-4o-mini para analisar blocos e responder perguntas naturalmente
- **Modo Raw (`--raw`)**: Busca por padrões/regex e exibe correspondências destacadas
- **Filtros disponíveis**: `--blocks`, `--case-sensitive`, `--history`, `--no-context`

### 📊 Visualizar Memória

```bash
# Ver todos os blocos
python view_memory.py

# Ver apenas log de conversas
python view_memory.py conv
```

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

## 🌐 Recursos Adicionais

### Interface Web de Chat

- Localização: `chat/chat_server.py` + `chat/static/`
- Porta: 8080 (configurável via `.env`)
- Funcionalidades:
  - Chat em tempo real com o agente
  - Upload de arquivos PDF (extração automática de texto)
  - Persistência de conversas no bloco `conversation_log`
  - Sessões únicas por navegador (UUID)
  
### Script de Busca Inteligente

- Arquivo: `search_memory.py`
- Funcionalidades:
  - Perguntas em linguagem natural (usa LLM para responder)
  - Busca por regex/padrões (modo `--raw`)
  - Filtros por bloco, data, histórico
  - Listagem de blocos disponíveis
  - Análise contextual com gpt-4o-mini

### Utilitários de Visualização

- `view_memory.py`: Visualiza blocos formatados no terminal
- `view_memory.py conv`: Exibe apenas o log de conversas

---

## 🔧 Troubleshooting

### Erro SSL Certificate

Se encontrar erros de certificado SSL:

```bash
python fix_ssl.py
```

### Chat não salva na memória

Verifique se os blocos padrão foram inicializados:

```bash
python references/sqlalchemy_models.py
python search_memory.py --list
```

### LLM não responde com contexto

Confirme que a memória está sendo carregada:

```bash
python search_memory.py "o que está na memória?" --blocks conversation_log
```