# Sistema de Senhas para Clínica Médica

Aplicação desktop modular em **Python 3.x + SQLite**, pensada para organizar a chegada, a priorização, a chamada e o encaminhamento de pacientes em seis especialidades.

O projeto é dividido por responsabilidades. Cada parte possui uma finalidade e seus próprios arquivos Python.

---

## Parte 1 — Fundação, banco de dados e regras de domínio

### Objetivo

Implementar a base técnica do sistema, no modelo **offline-first**, usando Python 3.x e SQLite. Esta parte entrega o banco de dados, as entidades, as regras de negócio da fila e o cálculo de métricas, de forma independente de qualquer interface.

### O que foi implementado

- Criação e configuração do banco SQLite.
- Definição das entidades do sistema.
- Operações CRUD.
- Cadastro dos dados iniciais (seed).
- Validação de especialidades, profissionais, consultórios e usuários.
- Geração de senhas sequenciais.
- Validação de prioridades.
- Ordenação da fila.
- Controle dos estados das senhas.
- Registro de atendimentos.
- Cálculo de métricas de atendimento.

### Estrutura de arquivos da Parte 1

```text
clinica_senhas/
├── app.py
├── config.py
├── database/
│   ├── connection.py
│   ├── models.py
│   └── repositories.py
├── domain/
│   ├── numbering_service.py
│   ├── priority_service.py
│   ├── queue_service.py
│   └── metrics_service.py
├── tests/
│   └── test_database.py
└── data/
    └── clinic.db
```

---

## Detalhamento dos arquivos

### 1.1 — Configuração geral

**Arquivo:** `config.py`

Centraliza os parâmetros do sistema:

- Caminho do banco de dados.
- Diretório de dados.
- Tempo médio padrão de atendimento.
- Alternância entre senhas preferenciais e normais.
- Intervalo de rechamada.
- Especialidades padrão.
- Pesos das prioridades.

### 1.2 — Ponto de entrada

**Arquivo:** `app.py`

Inicializa o sistema e executa o teste inicial do backend:

- Inicializa o banco de dados.
- Verifica as especialidades ativas.
- Verifica os consultórios ativos.
- Executa o teste inicial do backend.

### 1.3 — Conexão e estrutura do banco

**Arquivo:** `database/connection.py`

Responsável pela infraestrutura do banco de dados:

- Abre a conexão com o SQLite.
- Ativa as chaves estrangeiras.
- Cria as tabelas.
- Cria os índices.
- Cria os triggers de integridade.
- Executa o seed inicial, que inclui:
  - as **6 especialidades**;
  - os **18 consultórios**;
  - as **configurações padrão**.

### 1.4 — Modelos de dados

**Arquivo:** `database/models.py`

Define as entidades e as enumerações usadas em todo o sistema.

**Entidades**

| Entidade | Finalidade |
| --- | --- |
| `Especialidade` | Representa cada especialidade atendida |
| `Profissional` | Profissionais vinculados às especialidades |
| `Consultorio` | Consultórios de destino dos atendimentos |
| `Senha` | Senhas que compõem a fila |
| `Atendimento` | Registro do atendimento de cada senha |
| `Usuario` | Usuários do sistema |
| `Configuracao` | Parâmetros configuráveis |

**Enumerações**

- `TipoSenha`
- `Prioridade`
- `StatusSenha`
- `PerfilUsuario`

### 1.5 — Repositórios de dados

**Arquivo:** `database/repositories.py`

Camada de persistência, com as operações de acesso ao banco:

- Cadastro de especialidades.
- Cadastro de consultórios.
- Cadastro de profissionais.
- Cadastro de senhas.
- Cadastro de atendimentos.
- Cadastro de usuários.
- Cadastro de configurações.
- Consultas de fila.
- Atualização de status.
- Validações básicas de persistência.

### 1.6 — Geração de senhas

**Arquivo:** `domain/numbering_service.py`

Gera os códigos das senhas no formato `ESPECIALIDADE-TIPO-NÚMERO`:

```text
CG-P-001
CG-N-002
PSI-P-001
```

A sequência é **reiniciada diariamente para cada especialidade**.

### 1.7 — Prioridades

**Arquivo:** `domain/priority_service.py`

Valida as prioridades e define a hierarquia utilizada na fila:

| Código | Categoria | Peso |
| --- | --- | --- |
| P1 | Idoso com 80 anos ou mais | 1 |
| P2 | Idoso abaixo de 80 anos | 2 |
| P3 | Pessoa com deficiência | 3 |
| P4 | Gestante | 4 |
| P5 | Pessoa obesa | 5 |
| P6 | Criança de colo | 6 |

### 1.8 — Fila e estados

**Arquivo:** `domain/queue_service.py`

Concentra as regras de funcionamento da fila:

- Seleciona a próxima senha.
- Prioriza de P1 até P6.
- Aplica a alternância com senhas normais.
- Chama a senha.
- Inicia o atendimento.
- Finaliza o atendimento.
- Marca o paciente como ausente.
- Cancela a senha.
- Valida as transições de estado.

**Fluxo principal**

```text
Aguardando
    -> Chamando
    -> Em atendimento
    -> Finalizada
```

**Fluxos alternativos**

```text
Chamando -> Ausente
Aguardando -> Cancelada
Chamando -> Cancelada
Em atendimento -> Cancelada
Ausente -> Chamando
Ausente -> Cancelada
```

Qualquer transição fora dessas listas é rejeitada.

### 1.9 — Métricas

**Arquivo:** `domain/metrics_service.py`

Calcula os indicadores de atendimento:

- Quantidade de atendimentos finalizados.
- Tempo médio geral.
- Tempo médio por especialidade.

### 1.10 — Testes da Parte 1

**Arquivo:** `tests/test_database.py`

Valida:

- Criação das tabelas.
- Seed das especialidades.
- Seed dos consultórios.
- Limite de três profissionais ativos por especialidade.
- Ordem da fila.
- Restrição entre tipo e prioridade.

---

## Resumo da Parte 1

| Camada | Arquivos | Papel |
| --- | --- | --- |
| Configuração | `config.py`, `app.py` | Parâmetros e inicialização |
| Banco de dados | `database/connection.py`, `database/models.py`, `database/repositories.py` | Estrutura, entidades e persistência |
| Domínio | `domain/numbering_service.py`, `domain/priority_service.py`, `domain/queue_service.py`, `domain/metrics_service.py` | Regras de negócio |
| Testes | `tests/test_database.py` | Validação da base |

Ao final desta parte, o sistema já possui um backend funcional e testável, sobre o qual as próximas partes (interface e painel administrativo) poderão ser construídas.

