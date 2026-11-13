# Cloud Tasks API — Projeto Final de Computação em Nuvem

API Flask/SQLite de tarefas usada como objeto de uma **esteira completa de CI/CD**: testes e build no GitHub Actions, imagem Docker versionada por SHA no GitHub Container Registry (GHCR) e entrega contínua planejada para AWS EC2 com verificação de `/health`.

> **Situação:** CI e publicação no GHCR implantadas e comprovadas. O CD está implementado, mas **desativado** (`DEPLOY_ENABLED`) até a EC2 ser provisionada. Ver [Situação atual](#situação-atual-e-pendências).

## Objetivos e requisitos acadêmicos

Fluxo exigido pelo [enunciado](ENUNCIADO_ALUNOS.md): branch `feature/...` → Pull Request → CI → merge na `main` → imagem no GHCR (tag = SHA) → CD na EC2 → `GET /health`. Também são exigidos: Security Group documentado e SSH restrito (sem `0.0.0.0/0`), secrets fora do código/logs, `DELETE /tasks/<id>` e mais uma melhoria com testes, persistência após recriar o contêiner e encerramento dos recursos AWS. O acompanhamento item a item está em [TODO.md](TODO.md).

## Tecnologias

| Camada | Tecnologia |
|---|---|
| API | Python 3.12, Flask 3, SQLite, Gunicorn |
| Testes | pytest |
| Contêiner | Docker (`python:3.12-slim`, usuário sem privilégios), Docker Compose (uso local) |
| CI/CD | GitHub Actions (`ci.yml`, `cd.yml`) |
| Registry | GitHub Container Registry — `ghcr.io/jpontesdev/computacao-em-nuvem` |
| Nuvem (planejada) | AWS EC2 Ubuntu 24.04 x86_64 |

## Integrantes e responsabilidades

| Integrante | Responsabilidades |
|---|---|
| _[nome]_ | CI, publicação no GHCR, CD e documentação da esteira |
| _[nome]_ | Evolução funcional da API (`DELETE /tasks/<id>`, melhoria adicional e testes) |
| _[nome, se houver]_ | _[responsabilidades]_ |

## Arquitetura

```mermaid
flowchart LR
    Dev[feature/...] --> PR[Pull Request]
    PR --> CI["CI: pytest + docker build"]
    CI -->|merge| Main[main]
    Main --> Pub["CI: publish<br/>ghcr.io/...:SHA"]
    Pub --> CD["CD: workflow_run<br/>(DEPLOY_ENABLED)"]
    CD -->|SSH + docker run| EC2["EC2 :80 → contêiner :8000"]
    EC2 --> H["GET /health"]
    classDef pend stroke-dasharray:5 5
    class CD,EC2,H pend
```
Linhas tracejadas: implementado no código, ainda não executado em infraestrutura real. Detalhes no [relatório técnico](docs/RELATORIO_FINAL.md).

## Estrutura de diretórios

```text
.github/workflows/ci.yml   # testes, build e publicação no GHCR
.github/workflows/cd.yml   # deploy na EC2 (desativado até DEPLOY_ENABLED=true)
app/main.py                # API Flask + SQLite
app/wsgi.py                # entrada do Gunicorn
tests/test_api.py          # testes pytest
scripts/deploy.sh          # executado na EC2 via SSH pelo CD
scripts/setup-ec2-ubuntu.sh# instala Docker na EC2 (execução manual)
docs/CONFIGURACAO.md       # guia AWS + GitHub (secrets, SG, GHCR)
docs/RELATORIO_FINAL.md    # relatório técnico
docs/ROTEIRO_APRESENTACAO.md
Dockerfile, compose.yaml, requirements.txt, requirements-dev.txt, pytest.ini
```

## Execução local

```bash
python -m venv .venv
# Linux/macOS: source .venv/bin/activate  |  Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
python -m flask --app app.main run --port 5000
```
Sem `DB_PATH` definido, o banco fica em `/tmp/cloud_tasks.db`.

### Testes

```bash
python -m pytest -q
```
Os testes usam um banco temporário por teste (`tmp_path`) e também rodam na CI a cada PR.

### Docker

```bash
docker compose up --build
curl http://localhost:8080/health
```
O Compose mapeia `8080 → 8000` e guarda o banco no volume `task_data` (`DB_PATH=/data/tasks.db`).

## API

| Método | Rota | Função |
|---|---|---|
| GET | `/` | Informações do serviço |
| GET | `/health` | Saúde da aplicação/banco (200 ou 503) |
| GET | `/tasks` | Lista tarefas |
| POST | `/tasks` | Cria tarefa (`{"title":"..."}`, até 120 caracteres) |
| PATCH | `/tasks/<id>` | Atualiza título e/ou conclusão (`{"title":"..."}`, `{"done":true}`) |
| DELETE | `/tasks/<id>` | Remove tarefa (`204` se removida, `404` se inexistente) |

`DELETE /tasks/<id>` e a melhoria adicional estão a cargo de outro integrante e ainda não constam no código.

```bash
curl -X POST http://localhost:8080/tasks -H 'Content-Type: application/json' -d '{"title":"Minha tarefa"}'
curl http://localhost:8080/tasks
```

## CI em Pull Requests

[`ci.yml`](.github/workflows/ci.yml) roda em `pull_request` e `push` para `main`:

| Job | PR | Push na `main` |
|---|---|---|
| `test` — instala dependências (cache pip) e roda `pytest` | ✅ | ✅ |
| `build` — `docker build` sem login e sem push | ✅ | ✅ |
| `publish` — login no GHCR e push da imagem | ignorado | ✅ |

PRs nunca recebem `packages: write`, nunca publicam imagem e não disparam o CD.

## Publicação no GHCR

Após push na `main`, o job `publish` publica `ghcr.io/jpontesdev/computacao-em-nuvem:<SHA completo do commit>`. A tag é imutável e identifica exatamente o código implantado. O pacote é público, permitindo `docker pull` na EC2 sem credenciais.

## CD na EC2 (previsto)

[`cd.yml`](.github/workflows/cd.yml) é disparado por `workflow_run` quando a CI termina e só executa se **todas** as condições valerem:

- variável de repositório `DEPLOY_ENABLED == 'true'`;
- CI concluída com sucesso, originada de `push` na `main`;
- o commit ainda é o topo da `main` (evita que versão antiga sobrescreva a nova).

Passos: grava chave SSH e `known_hosts` em diretório temporário do job → executa [`deploy.sh`](scripts/deploy.sh) na EC2 (`docker pull`, recria o contêiner, checa `/health` local) → checa `http://EC2_HOST/health` a partir do runner com tentativas e timeout limitados → apaga o material SSH. Deploys são serializados (`concurrency`) e o job tem limite de 15 min. Configuração de secrets e Security Group: [docs/CONFIGURACAO.md](docs/CONFIGURACAO.md).

## Persistência de dados

O banco SQLite fica em `/data/tasks.db` dentro do contêiner. Na EC2, `deploy.sh` monta o volume nomeado `cloud-tasks-data` em `/data`; ao publicar nova versão, o contêiner é removido com `docker rm -f` (sem `-v`) e recriado, mas o volume é preservado. Localmente, o Compose usa o volume `task_data`. Evidência na EC2: pendente.

## Links

- Pull Request #1 — CI: <https://github.com/jpontesdev/Computacao-em-Nuvem/pull/1>
- Pull Request #2 — melhorias do CD: <https://github.com/jpontesdev/Computacao-em-Nuvem/pull/2>
- Workflow CI: <https://github.com/jpontesdev/Computacao-em-Nuvem/actions/workflows/ci.yml>
- Workflow CD: <https://github.com/jpontesdev/Computacao-em-Nuvem/actions/workflows/cd.yml>
- Relatório técnico: [docs/RELATORIO_FINAL.md](docs/RELATORIO_FINAL.md)
- Roteiro da apresentação: [docs/ROTEIRO_APRESENTACAO.md](docs/ROTEIRO_APRESENTACAO.md)
- URL/IP da aplicação: _[a preencher quando a EC2 estiver ativa]_

## Situação atual e pendências

| Etapa | Situação |
|---|---|
| CI em PRs (test + build, sem publish) | ✅ Comprovada nas PRs #1 e #2 |
| Publicação no GHCR por SHA | ✅ Comprovada (CI #5 e #8) |
| CD implementado e protegido por `DEPLOY_ENABLED` | ✅ Ignorado corretamente após os merges |
| EC2, Security Group e acesso SSH do runner | ⏳ Aguardando créditos AWS e orientação do professor |
| Primeiro deploy, `/health` remoto e nova versão | ⏳ Depende da EC2 |
| Persistência após recriar o contêiner | ⏳ Depende da EC2 |
| `DELETE /tasks/<id>` + melhoria + testes | ⏳ Em desenvolvimento por outro integrante |
| Encerramento dos recursos AWS | ⏳ Após a apresentação |

## Segurança e limitações

Deploy didático: sem TLS, balanceamento, rollback automático ou alta disponibilidade; há alguns segundos de indisponibilidade na troca do contêiner. Não usar dados reais. O grupo `docker` na EC2 equivale a privilégios de root. O runner hospedado do GitHub não tem IP fixo: **SSH nunca deve ser liberado para `0.0.0.0/0`**; a solução de acesso depende de orientação docente (ver [CONFIGURACAO.md](docs/CONFIGURACAO.md)).


## Integrantes do Grupo
- Gabriel Duarte - 22303292
- João Vitor Jardim Machado Pontes - 22307063
- Elter Rodrigues - 22309480


TESTE PULL REQUEST