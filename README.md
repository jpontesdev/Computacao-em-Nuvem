# Cloud Tasks API — Projeto Final de Computação em Nuvem

API Flask/SQLite de tarefas usada como objeto de uma **esteira completa de CI/CD**: testes e build no GitHub Actions, imagem Docker versionada por SHA no GitHub Container Registry (GHCR) e entrega contínua em AWS EC2 com verificação de `/health` via HTTPS.

> **Situação:** esteira completa em funcionamento — CI em PRs, publicação no GHCR por SHA, CD automático na EC2 com health check, persistência comprovada e rollback automático. Aplicação: <https://32-193-56-180.sslip.io/health> (disponível enquanto a infraestrutura estiver ativa).

## Integrantes e responsabilidades

| Integrante | Matrícula | Responsabilidades |
|---|---|---|
| João Vitor Jardim Machado Pontes | 22307063 | Criação do repositório a partir da base; `DELETE /tasks/<id>`; melhoria de edição de título via `PATCH`; testes da evolução funcional |
| Elter Rodrigues | 22309480 | Workflow de CI (PR #1); publicação no GHCR; robustez do CD (PR #2); README, relatório e roteiro (PR #3); checklist |
| Gabriel Duarte Marques | 22303292 | EC2, Security Group e IP elástico; Docker e Caddy (HTTPS); runner auto-hospedado e adaptação do CD; evidências de deploy e persistência; observabilidade (CloudWatch/SNS); rollback automático |

## Objetivos e requisitos acadêmicos

Fluxo exigido pelo [enunciado](ENUNCIADO_ALUNOS.md): branch `feature/...` → Pull Request → CI → merge na `main` → imagem no GHCR (tag = SHA) → CD na EC2 → `GET /health`. Também são exigidos: Security Group documentado e SSH restrito (sem `0.0.0.0/0`), secrets fora do código/logs, `DELETE /tasks/<id>` e mais uma melhoria com testes, persistência após recriar o contêiner e encerramento dos recursos AWS. O acompanhamento item a item está em [TODO.md](TODO.md).

## Tecnologias

| Camada | Tecnologia |
|---|---|
| API | Python 3.12, Flask 3, SQLite, Gunicorn |
| Testes | pytest |
| Contêiner | Docker (`python:3.12-slim`, usuário sem privilégios), Docker Compose (uso local) |
| CI/CD | GitHub Actions (`ci.yml`, `cd.yml`) com runner auto-hospedado na EC2 |
| Registry | GitHub Container Registry — `ghcr.io/jpontesdev/computacao-em-nuvem` |
| Nuvem | AWS EC2 `t3.micro` (us-east-1), Amazon Linux 2023, IP elástico, Caddy (HTTPS), CloudWatch + SNS |

## Arquitetura

```mermaid
flowchart LR
    Dev[feature/...] --> PR[Pull Request]
    PR --> CI["CI: pytest + docker build"]
    CI -->|merge| Main[main]
    Main --> Pub["CI: publish<br/>ghcr.io/...:SHA"]
    Pub --> CD["CD: workflow_run<br/>runner self-hosted na EC2"]
    CD -->|deploy.sh| APP["cloud-tasks-api<br/>127.0.0.1:8000"]
    U[Usuário] -->|HTTPS 443| CADDY["Caddy :80/:443"]
    CADDY --> APP
    CD --> H["verify-https<br/>GET /health"]
```

Detalhes no [relatório técnico](docs/RELATORIO_FINAL.md).

## Estrutura de diretórios

```text
.github/workflows/ci.yml   # testes, build e publicação no GHCR
.github/workflows/cd.yml   # deploy na EC2 (runner self-hosted) + verificação HTTPS
app/main.py                # API Flask + SQLite
app/wsgi.py                # entrada do Gunicorn
tests/test_api.py          # testes pytest
scripts/deploy.sh          # deploy com health check e rollback automático
scripts/setup-ec2-ubuntu.sh# instalação de Docker (guia original, Ubuntu)
docs/CONFIGURACAO.md       # guia AWS + GitHub
docs/RELATORIO_FINAL.md    # relatório técnico
docs/ROTEIRO_APRESENTACAO.md
docs/evidencias/           # capturas de tela (EC2, SG, deploy, persistência, rollback)
Dockerfile, compose.yaml, requirements.txt, requirements-dev.txt, pytest.ini
```

## Execução local

```bash
python -m venv .venv
# Linux/macOS: source .venv/bin/activate  |  Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
python -m flask --app app.main run --port 5000
```

Sem `DB_PATH` definido, o banco fica em `/tmp/cloud_tasks.db`. No Windows, defina `DB_PATH` para um caminho existente (ex.: `set DB_PATH=%TEMP%\tasks.db`).

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
| PATCH | `/tasks/<id>` | Atualiza título e/ou conclusão (`{"title":"..."}`, `{"done":true}`) — **melhoria** |
| DELETE | `/tasks/<id>` | Remove tarefa (`204` se removida, `404` se inexistente) |

```bash
curl -X POST https://32-193-56-180.sslip.io/tasks -H 'Content-Type: application/json' -d '{"title":"Minha tarefa"}'
curl https://32-193-56-180.sslip.io/tasks
curl -X DELETE -i https://32-193-56-180.sslip.io/tasks/1
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

## CD na EC2

[`cd.yml`](.github/workflows/cd.yml) é disparado por `workflow_run` quando a CI termina e só executa se **todas** as condições valerem: `DEPLOY_ENABLED == 'true'`; CI concluída com sucesso, originada de `push` na `main` do próprio repositório.

1. **`deploy`** — roda no runner auto-hospedado da EC2 (`[self-hosted, linux, x64, deploy-ec2]`). Ignora o deploy se o SHA não for mais o topo da `main` e executa [`deploy.sh`](scripts/deploy.sh): `docker pull` da imagem por SHA → preserva o contêiner atual como `-previous` → sobe a nova versão no mesmo volume → health check local. Se o health check falhar, **restaura automaticamente** a versão anterior.
2. **`verify-https`** — roda em runner hospedado do GitHub e checa `https://<APP_URL>/health` de fora da EC2, com tentativas e timeout limitados.

Como o runner se conecta ao GitHub apenas por conexão de saída, o deploy **não precisa de SSH de entrada**. Deploys são serializados (`concurrency`) e limitados a 15 min.

## Persistência de dados

O banco SQLite fica em `/data/tasks.db`, montado no volume nomeado `cloud-tasks-data`. A cada deploy o contêiner é recriado com a nova imagem, mas o volume é preservado. **Comprovado na EC2:** a tarefa criada com a imagem `ccd2664` continuou listada após o CD #14 recriar o contêiner com a imagem `d8238ad` (evidências 11–14 em [docs/evidencias](docs/evidencias/)).

## Links

- Repositório: <https://github.com/jpontesdev/Computacao-em-Nuvem>
- Aplicação: <https://32-193-56-180.sslip.io/health>
- Pull Requests: [#1 — CI](https://github.com/jpontesdev/Computacao-em-Nuvem/pull/1) · [#2 — CD](https://github.com/jpontesdev/Computacao-em-Nuvem/pull/2) · [#3 — documentação](https://github.com/jpontesdev/Computacao-em-Nuvem/pull/3)
- CI aprovada em PR: [run #4](https://github.com/jpontesdev/Computacao-em-Nuvem/actions/runs/43163185365) · CI aprovada na `main` com publish: [run #17](https://github.com/jpontesdev/Computacao-em-Nuvem/actions/runs/43424541858)
- CD aprovado: [run #14](https://github.com/jpontesdev/Computacao-em-Nuvem/actions/runs/43424701915) · [run #16](https://github.com/jpontesdev/Computacao-em-Nuvem/actions/runs/43431044247)
- Relatório técnico: [docs/RELATORIO_FINAL.md](docs/RELATORIO_FINAL.md) · Roteiro: [docs/ROTEIRO_APRESENTACAO.md](docs/ROTEIRO_APRESENTACAO.md)

## Situação atual e pendências

| Etapa | Situação |
|---|---|
| CI em PRs (test + build, sem publish) | ✅ PRs #1, #2 e #3 |
| Publicação no GHCR por SHA | ✅ |
| `DELETE /tasks/<id>` + melhoria (`PATCH` de título) + testes | ✅ |
| EC2, Security Group (SSH restrito a um IP `/32`), IP elástico e HTTPS | ✅ |
| CD automático + `/health` local e HTTPS externo | ✅ CD #13–#16 |
| Persistência após recriar o contêiner | ✅ |
| Bônus: domínio/TLS, observabilidade (CloudWatch/SNS), rollback automático | ✅ |
| Gravação do vídeo / demonstração | ⏳ |
| Registro do custo efetivo e encerramento dos recursos AWS | ⏳ Após a apresentação |

## Segurança e limitações

Deploy didático: sem TLS, balanceamento, rollback automático ou alta disponibilidade; há alguns segundos de indisponibilidade na troca do contêiner. Não usar dados reais. O grupo `docker` na EC2 equivale a privilégios de root. O runner hospedado do GitHub não tem IP fixo: **SSH nunca deve ser liberado para `0.0.0.0/0`**; a solução de acesso depende de orientação docente (ver [CONFIGURACAO.md](docs/CONFIGURACAO.md)).


## Integrantes do Grupo
- Gabriel Duarte - 22303292
- João Vitor Jardim Machado Pontes - 22307063
- Elter Rodrigues - 22309480
