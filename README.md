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

