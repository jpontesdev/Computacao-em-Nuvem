# Relatório técnico — Esteira CI/CD da Cloud Tasks API

**Disciplina:** Computação em Nuvem · **Repositório:** <https://github.com/jpontesdev/Computacao-em-Nuvem> · **Imagem:** `ghcr.io/jpontesdev/computacao-em-nuvem`

> Situação deste relatório: CI e publicação no GHCR **comprovadas**; CD **implementado e desativado**; deploy na EC2 e persistência **ainda não validados** (infraestrutura não provisionada). Campos `[a preencher]` serão completados após o deploy.

## 1. Introdução

O objetivo é transformar uma API Python que funciona localmente em um serviço entregue automaticamente na nuvem: cada mudança passa por Pull Request e testes, gera uma imagem Docker imutável identificada pelo SHA do commit e, quando integrada à `main`, é implantada em uma instância AWS EC2 com verificação de saúde.

A **Cloud Tasks API** (Flask + SQLite, servida por Gunicorn) oferece `GET /`, `GET /health` (testa o banco; 200 ou 503), `GET /tasks`, `POST /tasks` (título não vazio, até 120 caracteres) e `PATCH /tasks/<id>` (campo `done` booleano). `DELETE /tasks/<id>` e a melhoria adicional estão sob responsabilidade de outro integrante.

## 2. Arquitetura

```mermaid
flowchart LR
    A[Desenvolvimento] --> B[branch feature/...]
    B --> C[Pull Request]
    C --> D["GitHub Actions CI<br/>test + build"]
    D -->|merge| E[main]
    E --> F["CI publish<br/>GHCR :SHA"]
    F --> G["GitHub Actions CD<br/>workflow_run"]
    G -->|"SSH + deploy.sh"| H["AWS EC2<br/>Docker :80→8000<br/>volume cloud-tasks-data"]
    H --> I["GET /health"]

    classDef ok fill:#d4edda,stroke:#2e7d32,color:#1b1b1b
    classDef off fill:#fff3cd,stroke:#b8860b,color:#1b1b1b
    classDef pend fill:#eeeeee,stroke:#777,stroke-dasharray:5 5,color:#1b1b1b
    class A,B,C,D,E,F ok
    class G off
    class H,I pend
```

Legenda: **verde** — implementado e comprovado; **amarelo** — implementado, desativado por `DEPLOY_ENABLED`; **cinza tracejado** — planejado, sem infraestrutura provisionada.

## 3. Infraestrutura e segurança

| Componente | Configuração (conforme arquivos do repositório) |
|---|---|
| GitHub Actions — CI | `ci.yml`: `pull_request` e `push` em `main`. Permissão padrão `contents: read`; `packages: write` só no job `publish`, que tem `if` restrito a push na `main`. Concorrência por ref, cancelando execuções antigas apenas em PR. |
| GHCR | Tag = SHA completo do commit; login com `GITHUB_TOKEN`; pacote público (pull sem credencial na EC2). |
| GitHub Actions — CD | `cd.yml`: `workflow_run` da CI; `contents: read`; `environment: production`; `concurrency: cd-production` (sem cancelar deploy em andamento); `timeout-minutes: 15`; pula o deploy se o SHA não for mais o topo da `main`. |
| AWS EC2 (planejada) | Ubuntu Server 24.04 LTS, **x86_64** (a imagem é amd64), IP público; Docker instalado por `scripts/setup-ec2-ubuntu.sh`. |
| Docker | `python:3.12-slim`, usuário `appuser`, Gunicorn com 2 workers em `0.0.0.0:8000`; `--restart unless-stopped`. |
| Portas | Contêiner `8000`; EC2 `80:8000` (`deploy.sh`); local `8080:8000` (`compose.yaml`). |
| Volume | EC2: `cloud-tasks-data:/data`; local: `task_data:/data`; `DB_PATH=/data/tasks.db`. |

**Security Group planejado** (a confirmar com o professor):

| Regra | Porta | Origem |
|---|---|---|
| HTTP | TCP 80 | Fontes permitidas para teste/avaliação `[a preencher]` |
| SSH | TCP 22 | Somente IPs confiáveis (`/32`) e o acesso do runner definido pelo professor — **nunca `0.0.0.0/0`** |

**Restrição de SSH:** o runner hospedado do GitHub não tem IP fixo. As alternativas previstas em [CONFIGURACAO.md](CONFIGURACAO.md) — runner auto-hospedado em rede permitida, acesso temporário supervisionado ou SSM — dependem de orientação docente.

**Secrets e variables** (nomes; nenhum valor versionado):

| Nome | Tipo | Uso |
|---|---|---|
| `EC2_HOST` | secret | IP/DNS público da EC2 (validado por regex) |
| `EC2_SSH_KEY` | secret | Chave privada dedicada ao deploy |
| `EC2_KNOWN_HOSTS` | secret | Identidade do host, conferida com a fingerprint real (`StrictHostKeyChecking=yes`) |
| `EC2_USER` | variable | Usuário SSH (`ubuntu`) |
| `DEPLOY_ENABLED` | variable (repositório) | Interruptor do CD |

A chave é gravada em `$RUNNER_TEMP` com permissão restrita, usada com `IdentitiesOnly` e removida em um passo `always()`. Secrets são mascarados nos logs e nenhum passo usa `set -x`.

**Proteção `DEPLOY_ENABLED`:** o job `deploy` só roda se a variável valer `true`. Ausente ou com outro valor, o job é **ignorado** (não falha), preservando a CI e a publicação no GHCR.

## 4. Resultados comprovados

| Evidência | Resultado | Referência |
|---|---|---|
| CI na PR #1 (`feature/ci`) | `test` e `build` aprovados; `publish` ignorado | <https://github.com/jpontesdev/Computacao-em-Nuvem/pull/1> |
| CI na PR #2 (`feature/cd`) | `test` e `build` aprovados; `publish` ignorado | <https://github.com/jpontesdev/Computacao-em-Nuvem/pull/2> |
| CI #5 — merge da PR #1 | `test`, `build` e `publish` aprovados; primeira publicação | `ghcr.io/jpontesdev/computacao-em-nuvem:33ae081e9fa00cfcacb790e5a12884986f9b0ac3` |
| CI #8 — merge da PR #2 | Publicação após as melhorias do CD | `ghcr.io/jpontesdev/computacao-em-nuvem:93d3754574aa53e903de084e9251b744754b1231` |
| CD após os merges | Ignorado corretamente (`DEPLOY_ENABLED` não definido) | [workflow CD](https://github.com/jpontesdev/Computacao-em-Nuvem/actions/workflows/cd.yml) |

Links diretos das execuções #5 e #8: `[a preencher]`. Capturas de tela: `[a preencher]`.

**Ainda não comprovado:** deploy na EC2, `/health` remoto, implantação de nova versão e persistência após recriar o contêiner.

## 5. Custos e recursos

A infraestrutura EC2 **ainda não foi provisionada** para este trabalho, por limitação de créditos AWS. Não há, até o momento, registro de custos a apresentar.

| Item | Valor |
|---|---|
| Tipo de instância / região | `[a preencher]` |
| Armazenamento (EBS) | `[a preencher]` |
| Endereço IPv4 público | `[a preencher]` |
| Período de utilização (início → encerramento) | `[a preencher]` |
| Custo efetivo (Billing / Cost Explorer) | `[a preencher]` |
| Evidência de encerramento (instância, EBS, IP) | `[a preencher]` |

## 6. Dificuldades e soluções

| Dificuldade | Solução adotada |
|---|---|
| Computador da faculdade sem Docker instalado | O build Docker é validado pelo job `build` da CI em cada PR, sem depender da máquina local. |
| CD existente antes da EC2 | Interruptor `DEPLOY_ENABLED`: o CD é ignorado sem falhar, mantendo CI e GHCR automáticos. |
| SSH a partir de runner sem IP fixo | SSH nunca aberto para `0.0.0.0/0`; `known_hosts` obrigatório; método de acesso aguardando orientação docente. |
| Limitação de créditos AWS | Esteira preparada e validada até o GHCR; provisionamento adiado para o período de demonstração. |
| Robustez do CD (PR #2) | `concurrency` para deploys serializados; descarte de deploy de commit desatualizado; timeouts em SSH e `curl`; `/health` com tentativas limitadas (local e externa) e falha do job se não saudável; chave SSH em diretório temporário removido ao final. |

## 7. Persistência

O SQLite fica em `/data/tasks.db`. O `deploy.sh` cria (de forma idempotente) o volume nomeado `cloud-tasks-data` e o monta em `/data`. A cada deploy o contêiner é removido com `docker rm -f` — que não remove volumes — e recriado com a nova imagem, reutilizando o mesmo volume. O diretório `/data` pertence ao usuário `appuser` na imagem, e essa permissão é herdada pelo volume na criação. Os dados só se perdem se o volume ou o disco da instância forem removidos.

**Procedimento de evidência (a executar na EC2):** criar tarefa com `POST /tasks` → `docker rm -f cloud-tasks-api` → recriar com `deploy.sh` ou via nova versão pela esteira → `GET /tasks` deve listar a tarefa.

| Evidência | Registro |
|---|---|
| Tarefa criada antes da recriação | `[a preencher]` |
| Imagem/SHA antes e depois (`docker inspect`) | `[a preencher]` |
| `GET /tasks` após a recriação | `[a preencher]` |
| `docker volume inspect cloud-tasks-data` | `[a preencher]` |

## 8. Integrantes

| Integrante | Responsabilidades |
|---|---|
| `[nome]` | `[responsabilidades]` |
| `[nome]` | Evolução funcional da API — `[detalhar]` |
| `[nome, se houver]` | `[responsabilidades]` |

## 9. Conclusão

Foi validado o trecho da esteira que não depende de infraestrutura paga: PRs executam testes e build sem publicar imagem; integrações na `main` publicam no GHCR imagens imutáveis identificadas pelo SHA; e o CD, já implementado com controles de segurança e confiabilidade, permanece desativado sem gerar falhas. Dependem da EC2 e da orientação do professor: definição do acesso SSH do runner, primeiro deploy automático, verificação remota de `/health`, demonstração de nova versão, prova de persistência e o registro de custos e encerramento dos recursos.
