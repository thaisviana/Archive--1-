# 🚀 Configurando o Repositório GitHub

Este guia te ensina a criar um repositório no GitHub e fazer upload do projeto.

## 📋 Pré-requisitos

1. ✅ Conta GitHub criada (https://github.com/signup)
2. ✅ Git instalado (`brew install git` no macOS)
3. ✅ [GitHub CLI (opcional, mas recomendado)](https://cli.github.com/)

---

## Opção 1️⃣: Via GitHub Web (Mais Fácil)

### Passo 1: Criar Repositório no GitHub

1. Vá para https://github.com/new
2. Preencha:
   - **Repository name**: `agent-memory-system` (ou seu nome preferido)
   - **Description**: `Sistema de memória persistente para agentes com LLM`
   - **Public** ou **Private**: Escolha sua preferência
3. NÃO marque "Initialize repository with README" (já temos um)
4. Clique "Create repository"

### Passo 2: Configurar Git Localmente

Na pasta do projeto:

```bash
# Entrar na pasta do projeto
cd /Users/thais.viana/Downloads/Archive\ \(1\)

# Inicializar git (se ainda não foi)
git init

# Configurar seu nome e email (primeiro vez)
git config --global user.name "Seu Nome"
git config --global user.email "seu.email@gmail.com"

# Adicionar todos os arquivos
git add .

# Fazer commit
git commit -m "Initial commit: Agent memory system with persistent storage"

# Adicionar o remote (substitua YOUR_USERNAME e REPO_NAME)
git remote add origin https://github.com/YOUR_USERNAME/agent-memory-system.git

# Fazer push para main
git branch -M main
git push -u origin main
```

---

## Opção 2️⃣: Via GitHub CLI (Mais Rápido)

Se tiver GitHub CLI instalado:

```bash
# Login (primeira vez)
gh auth login

# Criar repositório
gh repo create agent-memory-system \
  --source=. \
  --remote=origin \
  --push \
  --public \
  --description "Sistema de memória persistente para agentes com LLM"
```

---

## Opção 3️⃣: Via VS Code

1. Abra VS Code na pasta do projeto
2. Clique em **Source Control** (atalho: `Ctrl+Shift+G`)
3. Clique "Initialize Repository"
4. Faça stage de todos os arquivos
5. Escreva mensagem de commit: `"Initial commit: Agent memory system"`
6. Clique "Publish Branch"
7. Escolha "Publish to GitHub"
8. Selecione "Public" ou "Private"

---

## 🔑 Configurando Credenciais (Se Necessário)

### Opção A: HTTPS com Token (Recomendado)

1. Vá para https://github.com/settings/tokens
2. Clique "Generate new token (classic)"
3. Selecione scopes: `repo`, `workflow`, `admin:public_key`
4. Copie o token
5. Quando pedir password no git, cole o token

### Opção B: SSH (Mais Seguro)

```bash
# Gerar chave SSH
ssh-keygen -t ed25519 -C "seu.email@gmail.com"

# Aceitar tudo com Enter

# Exibir a chave pública
cat ~/.ssh/id_ed25519.pub

# Copiar a saída completa
```

1. Vá para https://github.com/settings/keys
2. Clique "New SSH key"
3. Cole a chave pública
4. Clique "Add SSH key"

Depois use:
```bash
git remote add origin git@github.com:YOUR_USERNAME/agent-memory-system.git
```

---

## ✅ Verificar que Funcionou

```bash
# Ver remote configurado
git remote -v

# Deve mostrar algo como:
# origin  https://github.com/YOUR_USERNAME/agent-memory-system.git (fetch)
# origin  https://github.com/YOUR_USERNAME/agent-memory-system.git (push)

# Ver status
git status
```

---

## 📤 Fazendo Pushes Futuros

```bash
# Depois de fazer mudanças
git add .
git commit -m "Descrição clara da mudança"
git push origin main
```

---

## 🔒 Variáveis Sensíveis (IMPORTANTE!)

**NUNCA faça commit de:**
- `.env` ✅ (protegido por .gitignore)
- Arquivos com senhas ✅ (protegido)
- API keys ✅ (protegido)

Se acidentalmente fizer commit, remova com:

```bash
# Remover arquivo do git mas manter localmente
git rm --cached .env
git commit -m "Remove .env from tracking"
git push
```

---

## 🌟 Próximos Passos

Após fazer o primeiro push:

1. **Branch de desenvolvimento:**
   ```bash
   git checkout -b develop
   git push -u origin develop
   ```

2. **CI/CD (Github Actions)** - Criar `.github/workflows/tests.yml`

3. **Releases** - Tag de versões:
   ```bash
   git tag -a v1.0.0 -m "Version 1.0.0"
   git push origin v1.0.0
   ```

4. **Colaboradores** - Settings → Collaborators

---

## 📞 Troubleshooting

### Erro: "fatal: not a git repository"

```bash
git init
git add .
git commit -m "Initial commit"
```

### Erro: "authentication failed"

Verifique credenciais em GitHub Settings → Developer settings → Personal access tokens

### Erro: "remote already exists"

```bash
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/...
```

---

## 🎥 Resumo dos Comandos Essenciais

```bash
# Setup inicial
git init
git config --global user.name "Seu Nome"
git config --global user.email "seu@email.com"

# Commit e push
git add .
git commit -m "Mensagem descritiva"
git remote add origin https://github.com/seu-usuario/seu-repo.git
git branch -M main
git push -u origin main

# Próximos pushes (após mudanças)
git add .
git commit -m "Descrição da mudança"
git push
```

---

**Dúvidas?** Consulte: https://docs.github.com/pt/get-started/quickstart/set-up-git
