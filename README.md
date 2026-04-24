# ADCRS — Ambiente Digital de Criticidade e Resiliência Setorial

[![CI](https://github.com/anatel/adcrs/actions/workflows/ci.yml/badge.svg)](https://github.com/anatel/adcrs/actions/workflows/ci.yml)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com/)
[![React 18](https://img.shields.io/badge/react-18.x-61DAFB.svg)](https://react.dev/)
[![PostgreSQL 16](https://img.shields.io/badge/postgres-16-336791.svg)](https://www.postgresql.org/)
[![Licença MIT](https://img.shields.io/badge/licen%C3%A7a-MIT-green.svg)](LICENSE)
[![Status: Alpha](https://img.shields.io/badge/status-alpha-orange.svg)]()

> **Plataforma digital para identificação, classificação e consolidação setorial de ativos críticos de telecomunicações**, operacionalizando a **Metodologia de Joias da Coroa (MACA V2.0)** em conformidade com a Resolução ANATEL nº 740/2020 e o NIST Cybersecurity Framework 2.0.

---

## Sumário

- [Visão Geral](#visão-geral)
- [Arquitetura](#arquitetura)
- [Módulos](#módulos)
- [Stack Tecnológica](#stack-tecnológica)
- [Como Rodar Localmente](#como-rodar-localmente)
- [Integração com Qlik Sense e Coleta-ANATEL](#integração-com-qlik-sense-e-coleta-anatel)
- [Estrutura do Repositório](#estrutura-do-repositório)
- [Roadmap em Fases](#roadmap-em-fases)
- [Documentação](#documentação)
- [Licença](#licença)

---

## Visão Geral

O **ADCRS** transforma a **Metodologia de Joias da Coroa — IC Telecom** de um artefato regulatório-estático (Word, PDF, planilhas) em uma **plataforma contínua, auditável e analítica** para identificação e gestão de ativos críticos no setor de telecomunicações brasileiro.

A metodologia **MACA** permanece como **motor regulatório**: é ela quem define pilares, indicadores, fórmulas, classes e cláusulas de inclusão direta. O ADCRS é a camada digital que executa essa metodologia de forma reproduzível, cria o Catálogo Setorial de Ativos Críticos (CSAC) de forma contínua e transforma os dados em **dashboards e insights automáticos** para GT-Ciber, ANATEL e prestadoras.

### Problema que o ADCRS resolve

Hoje a identificação de ativos críticos no setor sofre de:

- **Heterogeneidade** — cada prestadora aplica critérios próprios, impedindo consolidação;
- **Fricção** — submissão via planilhas e textos dispersos, sem trilha de auditoria;
- **Latência** — o ciclo é anual, quando o cenário de ameaças evolui diariamente;
- **Opacidade** — interdependências intra e intersetoriais ficam invisíveis no formato atual.

### O que o ADCRS entrega

- **Porta única de submissão** por prestadora, com formulários baseados na FIA (Anexo V);
- **Motor de cálculo determinístico** que aplica MACA uniformemente em todo o setor;
- **Grafo de dependências** que revela SPOFs setoriais e concentrações de risco;
- **Dashboards em dois níveis** (estratégico ANATEL/GT-Ciber e operacional prestadoras);
- **Motor de regras declarativo** (YAML) que gera alertas e recomendações automáticos;
- **Exportação nativa para Qlik Sense** e integração com o sistema COLETA-ANATEL.

---

## Arquitetura

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              CAMADA DE APRESENTAÇÃO                          │
│  ┌────────────────────┐  ┌────────────────────┐  ┌─────────────────────┐    │
│  │  Dashboard ANATEL  │  │ Dashboard Oper.    │  │  Qlik Sense ANATEL  │    │
│  │  (React SPA)       │  │ (React SPA)        │  │  (via QVD/OData)    │    │
│  └─────────┬──────────┘  └─────────┬──────────┘  └──────────┬──────────┘    │
└────────────┼────────────────────────┼─────────────────────────┼─────────────┘
             │                        │                         │
             ▼                        ▼                         ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                            CAMADA DE API (FastAPI)                           │
│   /fia   /maca   /csac   /rules   /insights   /qlik   /coleta   /audit       │
│                                                                              │
│   Autenticação ICP-Brasil · RBAC · Rate limit · Audit log imutável           │
└──────────────────────────────────────────────────────────────────────────────┘
             │              │              │              │           │
             ▼              ▼              ▼              ▼           ▼
┌────────────────┐ ┌────────────────┐ ┌──────────────┐ ┌─────────┐ ┌──────────┐
│  Motor MACA    │ │ Motor de       │ │  Consolid.   │ │ Qlik    │ │  Coleta  │
│  (scoring)     │ │ Regras (YAML)  │ │  Setorial    │ │ Export  │ │  Bridge  │
│  PP, PFA, FI,  │ │ Insights       │ │  CSAC, SPOF, │ │ QVD/    │ │  XML/    │
│  FD, PFA*,     │ │ automáticos    │ │  Grafo       │ │ OData   │ │  JSON    │
│  Cláusulas A   │ │                │ │              │ │         │ │          │
└────────┬───────┘ └────────┬───────┘ └──────┬───────┘ └────┬────┘ └────┬─────┘
         │                  │                │              │           │
         ▼                  ▼                ▼              ▼           ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                         CAMADA DE DADOS (PostgreSQL 16)                      │
│   ativos · prestadoras · fia · pontuacoes · dependencias · incidentes        │
│   perfis_nist_csf · planos_acao · auditoria · regras · insights_gerados      │
│                                                                              │
│   Extensões: PostGIS (georreferenciamento), pgaudit (trilha), pg_cron        │
└──────────────────────────────────────────────────────────────────────────────┘
```

A [visão completa, com fluxos e controle de sigilo, está em `docs/arquitetura/visao-geral.md`](docs/arquitetura/visao-geral.md).

---

## Módulos

### 1. Módulo de Entrada de Dados (`backend/app/api/v1/fia.py`)
Formulários estruturados baseados na FIA (Anexo V). Porta única de submissão com versionamento, assinatura digital ICP-Brasil e trilha de auditoria integral.

### 2. Motor de Cálculo MACA (`backend/app/services/maca/`)
Núcleo puro e testável que implementa as fórmulas do Anexo III:
- **PP** = 0,70 × máx + 0,30 × média (por pilar)
- **PFA** = Σ (PPₙ × pesoₙ)
- **FI** ≤ 0,20 (5 componentes somáveis)
- **FD** por faixa de RTO (0,00 a 0,10)
- **PFA\*** = mín(PFA × (1 + FI + FD); 5,00)
- **7 cláusulas de inclusão direta** para Classe A

### 3. Consolidação Setorial (`backend/app/services/consolidacao/`)
CSAC vivo, identificação automática de SPOFs setoriais, grafo de dependências intra e intersetoriais, mapas de concentração de risco por UF.

### 4. Dashboards (6 painéis especificados)
1. **Criticidade Setorial** — ativos por classe/prestadora/região/tecnologia
2. **Interdependências** — grafo de dependências, SPOFs
3. **Resiliência** — RTO, FD, cobertura de contingência
4. **PC-Telecom / NIST CSF** — gaps perfil atual vs alvo por função
5. **Ameaças e Exposição** — cruzamento com IOCs/TTPs do ISAC-Telecom
6. **Executivo** — Top 10 riscos setoriais, decisões regulatórias

### 5. Motor de Regras (`rules/definicoes/*.yaml`)
Sistema declarativo que gera alertas e recomendações. Exemplo:

```yaml
- id: REG-001
  nome: "Classe B com alto FI e RTO longo"
  condicao:
    classe: "B"
    fi_min: 0.12
    rto_horas_min: 24
  severidade: alta
  recomendacao: "Priorizar redundância geográfica ou acordo de reciprocidade setorial"
```

### 6. Integrações (`backend/app/integrations/`)
- **Qlik Sense ANATEL** — export QVD nativo e feed OData
- **Sistema COLETA-ANATEL** — JSON/XML conforme padrões Anatel, auth por ICP-Brasil
- **ISAC-Telecom** — ingestão contínua de IOCs/TTPs (Fase 3)

---

## Stack Tecnológica

| Camada | Tecnologia | Por quê |
|---|---|---|
| Backend | **Python 3.12 + FastAPI** | Tipagem forte, OpenAPI automático, ecossistema maduro |
| Banco | **PostgreSQL 16 + PostGIS** | ACID, JSONB, geoespacial, pgaudit para sigilo |
| ORM | **SQLAlchemy 2 + Alembic** | Migrations versionadas, type-safe |
| Motor MACA | **Python puro + Pydantic** | Determinístico, 100% testável, sem dependência de framework |
| Regras | **YAML + jsonschema** | Editável pelo GT-Ciber sem deploy de código |
| Frontend | **React 18 + Vite + TypeScript** | SPA performática, ecossistema robusto |
| UI | **Tailwind CSS + Recharts + D3** | Dashboards e grafos de dependência |
| Mapas | **Leaflet + React-Leaflet** | Mapas de concentração por UF |
| Auth | **OAuth2 + JWT + ICP-Brasil (PKCS#11)** | Conformidade com exigência regulatória |
| Testes | **pytest + Vitest + Playwright** | Cobertura de unidade, integração e E2E |
| CI/CD | **GitHub Actions** | Lint, test, build, coverage, security scan |
| Containers | **Docker + Docker Compose** | Onboarding em um comando |
| Orquestração | **Kubernetes (Helm)** | Pronto para ambiente produtivo ANATEL |

---

## Como Rodar Localmente

### Pré-requisitos

- Docker 24+ e Docker Compose v2
- (Opcional para desenvolvimento nativo) Python 3.12, Node.js 20, PostgreSQL 16

### Subir o ambiente completo

```bash
git clone https://github.com/anatel/adcrs.git
cd adcrs
cp .env.example .env
docker compose up -d
```

Serviços disponíveis após o boot:

| Serviço | URL | Credenciais |
|---|---|---|
| Backend API | http://localhost:8000 | — |
| Swagger UI | http://localhost:8000/docs | — |
| Frontend | http://localhost:3000 | admin@adcrs.local / troque_em_prod |
| PostgreSQL | localhost:5432 | adcrs / adcrs_dev |
| Adminer | http://localhost:8080 | — |

### Carregar dados sintéticos de demonstração

```bash
docker compose exec backend python -m app.scripts.seed_demo
```

Isso cria 5 prestadoras fictícias, 47 ativos distribuídos nas 4 classes, incluindo um cabo submarino, um IXP e dois backbones compartilhados para demonstrar grafos de interdependência.

### Rodar a suíte de testes

```bash
docker compose exec backend pytest -v --cov=app --cov-report=term-missing
docker compose exec frontend npm test
```

---

## Integração com Qlik Sense e Coleta-ANATEL

O ADCRS **não substitui** o Qlik Sense da ANATEL nem o sistema COLETA — ele os **alimenta**.

### Para Qlik Sense ANATEL

Três caminhos suportados, descritos em [`docs/integracao-qlik.md`](docs/integracao-qlik.md):

1. **Export QVD agendado** — arquivos `.qvd` gerados em `/exports/qlik/` conforme schedule (diário/semanal)
2. **Feed OData REST** — endpoint `/api/v1/qlik/odata` consumível pelo Qlik Data Gateway
3. **Conexão direta PostgreSQL** — via Qlik ODBC connector (somente leitura, view materializada)

Modelo tabular associativo pré-otimizado para Qlik em [`backend/app/services/qlik/modelo_tabular.py`](backend/app/services/qlik/modelo_tabular.py).

### Para Sistema COLETA-ANATEL

Conformidade com os padrões de troca de dados da ANATEL descritos em [`docs/integracao-coleta.md`](docs/integracao-coleta.md):

- XML Schema (XSD) para submissão estruturada de FIAs
- Autenticação por certificado digital ICP-Brasil A3
- Assinatura XMLDSig para garantir não-repúdio
- Mapeamento bidirecional entre o schema interno do ADCRS e o COLETA

---

## Estrutura do Repositório

```
adcrs/
├── README.md                       ← você está aqui
├── LICENSE
├── CHANGELOG.md
├── CONTRIBUTING.md
├── SECURITY.md
├── docker-compose.yml
├── .env.example
├── .github/
│   ├── workflows/                  ← CI/CD (lint, test, build, release)
│   └── ISSUE_TEMPLATE/
├── backend/                        ← FastAPI + SQLAlchemy + Motor MACA
│   ├── app/
│   │   ├── api/v1/                 ← endpoints REST
│   │   ├── core/                   ← config, security, logging
│   │   ├── db/                     ← sessão, migrations
│   │   ├── models/                 ← modelos SQLAlchemy
│   │   ├── schemas/                ← DTOs Pydantic
│   │   ├── services/
│   │   │   ├── maca/               ← MOTOR DE CÁLCULO MACA (puro)
│   │   │   ├── rules/              ← motor de regras YAML
│   │   │   ├── qlik/               ← exportação Qlik
│   │   │   └── coleta/             ← integração COLETA-ANATEL
│   │   └── integrations/
│   └── tests/                      ← pytest (unit + integration)
├── frontend/                       ← React 18 + TypeScript + Vite
│   └── src/
│       ├── components/dashboards/  ← os 6 dashboards
│       ├── pages/
│       └── services/
├── database/
│   ├── schema/                     ← DDL completo
│   ├── seeds/                      ← dados sintéticos de demonstração
│   └── migrations/                 ← Alembic
├── rules/                          ← DEFINIÇÕES YAML DE INSIGHTS
│   ├── definicoes/
│   └── testes/
├── infra/
│   ├── docker/                     ← Dockerfiles
│   ├── k8s/                        ← Helm charts
│   └── terraform/                  ← IaC para ambiente ANATEL
├── docs/
│   ├── arquitetura/                ← C4, ADRs, diagramas
│   ├── adr/                        ← Architecture Decision Records
│   └── fases/                      ← Roadmap 4 fases
├── samples/fia/                    ← exemplos de FIA em JSON
├── exports/
│   ├── qlik/
│   └── coleta/
└── scripts/                        ← utilitários operacionais
```

Descrição detalhada em [`docs/estrutura-repositorio.md`](docs/estrutura-repositorio.md).

---

## Roadmap em Fases

O ADCRS evolui em **4 fases de maturidade** alinhadas à metodologia MACA V2.0:

| Fase | Nome | Duração | Entrega Principal |
|---|---|---|---|
| **1** | Digitalização Mínima Viável | 3 meses | Dicionário MACA, formulários, cálculo automático, dashboard básico, submissão única |
| **2** | Consolidação Inteligente | 3 meses | Grafo de interdependências, SPOFs setoriais, motor de regras Classe A, 6 dashboards |
| **3** | Integração Contínua ISAC | 3 meses | Ingestão de IOCs/TTPs, cruzamento criticidade × ameaça ativa, priorização dinâmica |
| **4** | Camada Analítica Avançada | 3 meses | ML para priorização, simulação cascata, geração automática de minutas de relatório |

Detalhamento completo em [`docs/fases/`](docs/fases/).

---

## Documentação

- [Visão de Arquitetura](docs/arquitetura/visao-geral.md)
- [ADRs (Architecture Decision Records)](docs/adr/)
- [Dicionário de Dados MACA](docs/dicionario-dados-maca.md)
- [Motor de Cálculo MACA](docs/motor-maca.md)
- [Motor de Regras e Insights](docs/motor-regras.md)
- [Integração Qlik Sense](docs/integracao-qlik.md)
- [Integração COLETA-ANATEL](docs/integracao-coleta.md)
- [Política de Sigilo e Segurança](SECURITY.md)
- [Guia de Contribuição](CONTRIBUTING.md)

---

## Governança do Projeto

O ADCRS é um projeto **institucional do GT-Ciber**, com apoio da SCO/ANATEL. Contribuições técnicas seguem o processo em [CONTRIBUTING.md](CONTRIBUTING.md). Decisões arquiteturais são formalizadas via [ADRs](docs/adr/).

Este repositório **não contém dados reais de prestadoras**. Todos os dados de exemplo são sintéticos e claramente marcados como tal em `samples/` e `database/seeds/`.

---

## Licença

Código-fonte sob licença MIT (ver [LICENSE](LICENSE)). Metodologia MACA sob licença institucional ANATEL/GT-Ciber. O uso deste software em produção regulatória exige adesão ao Termo de Uso do GT-Ciber.

---

**Projeto**: Ambiente Digital de Criticidade e Resiliência Setorial (ADCRS)
**Mantenedor**: GT-Ciber / ANATEL
**Versão do Documento**: 1.0 — Abril/2026
**Metodologia Base**: Joias da Coroa IC Telecom V2.0
