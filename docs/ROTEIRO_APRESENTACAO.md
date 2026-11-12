# Roteiro da apresentação (~4 min)

Legenda: ✅ pode ser gravado agora · ⏳ depende da EC2 / CD habilitado.

| Tempo | Bloco | O que mostrar | Status |
|---|---|---|---|
| 0:00–0:30 | Apresentação | Objetivo, API de tarefas e diagrama do [README](../README.md#arquitetura); integrantes e responsabilidades. | ✅ |
| 0:30–1:15 | Pull Requests | PR #1 e PR #2: branch `feature/...`, revisão, checks verdes, merge na `main`. Destacar `test` e `build` aprovados e `publish` **ignorado** na PR. | ✅ |
| 1:15–1:45 | GitHub Actions | Execuções de CI #5 e #8 na `main` com `publish` aprovado; execução do CD **ignorada** enquanto `DEPLOY_ENABLED` não está ativo. | ✅ |
| 1:45–2:05 | GHCR | Pacote `ghcr.io/jpontesdev/computacao-em-nuvem` público com tags iguais ao SHA dos commits (`33ae081…`, `93d3754…`). | ✅ |
| 2:05–3:00 | CD e API | Merge de uma nova mudança → CI → CD verde (passos SSH, deploy, verificação de `/health`); `curl http://<IP>/health` e `/tasks`; `docker inspect` mostrando o SHA implantado. | ⏳ |
| 3:00–3:40 | Persistência | `POST /tasks` → recriar contêiner (`docker rm -f` + deploy) → `GET /tasks` mantém a tarefa. | ⏳ |
| 3:40–4:00 | Encerramento | Segurança (SSH restrito, secrets, `DEPLOY_ENABLED`), dificuldades, custos e evidência de encerramento dos recursos AWS. | ⏳ (custos/encerramento) |

## Preparação

- Abrir antes as abas: PRs #1 e #2, Actions (CI e CD), página do pacote GHCR, terminal.
- Para os blocos ⏳: EC2 provisionada, acesso do runner definido pelo professor, secrets configurados e `DEPLOY_ENABLED=true` (ver [CONFIGURACAO.md](CONFIGURACAO.md)).
- Ter uma mudança pequena já em PR aprovada para fazer o merge ao vivo, ou gravar a execução previamente.
- Após a gravação: desativar `DEPLOY_ENABLED` e encerrar os recursos AWS.

## Se a EC2 não estiver disponível

Apresentar os blocos ✅, mostrar o trecho de `cd.yml` com as condições de execução e o mecanismo de persistência do [relatório](RELATORIO_FINAL.md#7-persistência), deixando claro que o deploy ainda não foi executado.
