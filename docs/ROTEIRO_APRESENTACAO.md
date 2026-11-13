# Roteiro da apresentação (~4 min 30 s)

Falas: **João** = João Vitor Jardim Machado Pontes · **Elter** = Elter Rodrigues · **Gabriel** = Gabriel Duarte Marques. Cada um apresenta a parte que desenvolveu (ver [relatório, seção 8](RELATORIO_FINAL.md#8-integrantes-e-distribuição-das-tarefas)).

| Tempo | Fala | Bloco | O que mostrar |
|---|---|---|---|
| 0:00–0:25 | Elter | Abertura | Objetivo, integrantes e diagrama do [README](../README.md#arquitetura). |
| 0:25–1:05 | João | Evolução da API | `DELETE /tasks/<id>` (204/404) e `PATCH` de título; testes em `tests/test_api.py`; `pytest` passando. |
| 1:05–1:50 | Elter | PR e CI | [PR #1](https://github.com/jpontesdev/Computacao-em-Nuvem/pull/1): branch `feature/ci`, revisão, checks verdes (`test`, `build`; `publish` **ignorado**), merge. CI na `main` com `publish` e a tag SHA no pacote GHCR. |
| 1:50–2:40 | Gabriel | Infraestrutura | EC2 `t3.micro`, Security Group (SSH só `/32`, 80/443 públicas), IP elástico, Caddy/HTTPS e runner auto-hospedado como serviço. |
| 2:40–3:25 | Gabriel | CD e API | Merge → CI → CD verde (`deploy` + `verify-https`); `curl https://32-193-56-180.sslip.io/health` e `/tasks`; `docker inspect` mostrando o SHA implantado. |
| 3:25–3:55 | Gabriel | Persistência | Tarefa criada com a imagem `ccd2664` continua listada após o CD #14 recriar o contêiner com `d8238ad`. |
| 3:55–4:30 | Elter | Bônus e encerramento | Rollback automático (teste com falha forçada), alarme CloudWatch/SNS, dificuldades, custos e plano de encerramento dos recursos. |

## Preparação

- Abas abertas: PR #1, Actions (CI #17, CD #14), pacote GHCR, console EC2/Security Group, terminal SSH na instância, pasta [evidencias](evidencias/).
- Confirmar antes: `DEPLOY_ENABLED=true`, runner online em *Settings → Actions → Runners*, `/health` respondendo 200.
- Para o deploy ao vivo, deixar uma PR pequena já aprovada; se o tempo for curto, mostrar as execuções já gravadas (CD #13–#16).
- Se a EC2 estiver indisponível no momento, usar as capturas de `docs/evidencias/` (10–20) para os blocos de CD, persistência e rollback.

## Após a apresentação

1. Desativar `DEPLOY_ENABLED` e remover o runner auto-hospedado do repositório.
2. Encerrar a instância, excluir o volume EBS, liberar o IP elástico e remover alarme e tópico SNS.
3. Registrar o custo efetivo (Billing/Cost Explorer) e anexar a evidência de encerramento na seção 6 do relatório.
