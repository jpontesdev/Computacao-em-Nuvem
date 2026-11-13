# TODO — Trabalho final: Esteira de CI/CD para API na AWS

> Checklist derivado de [ENUNCIADO_ALUNOS.md](ENUNCIADO_ALUNOS.md). Prazo: 14 dias corridos. Valor: 100 pontos (+ bônus até 10).
> Fluxo-alvo: branch → Pull Request → CI (GitHub Actions) → merge na `main` → imagem no GHCR (tag = SHA) → CD na EC2 → checagem `/health`.

---

## 1. Preparação e repositório (Dias 1–3) — *Git/branches/PR e organização: 10 pts*

- [X] Criar repositório próprio a partir do repositório-base fornecido pelo professor (Req. 1)
- [ ] Conceder acesso ao professor, caso o repositório seja privado
- [x] Clonar o repositório e compreender a API existente
- [x] Rodar os testes localmente com `pytest`
- [x] Construir e executar a aplicação com Docker localmente
- [x] Atualizar o README com os integrantes (Req. 1)
- [ ] Atualizar o README com instruções de uso (Req. 1)
- [ ] Garantir que nenhuma chave privada, token ou dado real esteja versionado (Regras)

## 2. Evolução funcional da API (Dias 4–5) — *Evolução funcional com testes: 10 pts*

- [X] Criar ao menos 1 branch no padrão `feature/...` para o desenvolvimento (Req. 8)
- [X] Implementar `DELETE /tasks/<id>` (Req. 7)
  - [X] Retornar HTTP `204` quando a tarefa existir e for removida
  - [X] Retornar HTTP `404` quando a tarefa não existir
- [X] Escrever no mínimo 2 testes para `DELETE /tasks/<id>` (ex.: caso 204 e caso 404) (Req. 7)
- [X] Implementar mais 1 melhoria na API (Req. 7)
  - [X] Permitir editar o título da tarefa via `PATCH /tasks/<id>` (`{"title":"..."}`)
- [X] Escrever teste para a melhoria implementada (Req. 7)
- [X] Confirmar que todos os testes passam localmente com `pytest`

## 3. Infraestrutura AWS EC2 (Dias 4–5) — *Infraestrutura EC2, rede e segurança: 15 pts*

- [x] Provisionar instância EC2 Linux (Req. 2)
- [x] Instalar e validar Docker funcional na instância (Req. 2)
- [x] Configurar Security Group (Req. 2)
  - [x] Liberar porta HTTP necessária para acesso à aplicação
  - [x] Restringir acesso SSH — **não** utilizar `0.0.0.0/0` (Req. 6 / Regras)
  - [x] Aplicar a solução segura para runners de deploy orientada pelo professor / guia fornecido (Req. 6 / Regras)
- [x] Documentar o Security Group (regras, portas e origens) (Req. 2)
- [x] Confirmar que a aplicação está acessível via HTTP (Req. 2)
- [x] Monitorar custos dos recursos AWS durante o trabalho (Regras)

## 4. Integração Contínua — CI (Dias 6–7) — *Testes e CI funcionando nos PRs: 20 pts*

- [x] Criar workflow de CI no GitHub Actions (Req. 3) — `.github/workflows/ci.yml`
  - [x] Etapa de instalação de dependências (com cache pip)
  - [x] Etapa de execução do `pytest`
  - [x] Etapa de build da imagem Docker (`push: false`, sem login)
- [x] Garantir que a CI execute em Pull Requests (Req. 3)
- [x] Garantir que execução em PR **não** publique imagem (Req. 3) — job `publish` com `if` restrito a push na `main`
- [x] Garantir que execução em PR **não** dispare deploy (Req. 3) — CD só roda após CI de `push` na `main`
- [x] Abrir ao menos 1 Pull Request da branch `feature/...` para `main` (Req. 8)
- [x] Realizar revisão do PR (própria, se trabalho individual) (Req. 8)
- [x] Comprovar CI aprovada no PR (Req. 8)
- [x] Fazer merge do PR na `main` (Req. 8)

## 5. Publicação de imagem no GHCR (Dias 8–10) — *Docker e publicação versionada: 15 pts*

- [x] Configurar publicação no GitHub Container Registry (Req. 4)
- [x] Versionar a imagem com o **SHA do commit** como tag (Req. 4)
- [x] Publicar a imagem **somente** quando mudanças entrarem na `main` (Req. 4)
- [x] Verificar no GHCR a imagem publicada com a tag correspondente ao SHA

## 6. Entrega Contínua — CD (Dias 8–10) — *CD automático e verificação de saúde: 20 pts*

- [x] Configurar Secrets/Variables no GitHub (Req. 6)
  - [x] Não expor credenciais ou chaves no código — tudo via `secrets`/`vars`; `.gitignore` bloqueia `*.pem`/`*.key`
  - [x] Não expor credenciais ou chaves nos logs — workflow não ecoa secrets e apaga a chave ao final; confirmar no primeiro run real
  - [x] Não expor credenciais ou chaves no README
- [x] Criar workflow de CD no GitHub Actions (Req. 5) — `.github/workflows/cd.yml`, desativado até `DEPLOY_ENABLED=true`
  - [x] Condicionar a execução do CD ao sucesso da CI (Req. 5) — `workflow_run` + `conclusion == success` + `event == push` na `main`
  - [x] Implantar na EC2 a imagem correspondente ao SHA do commit (Req. 5) — `ghcr.io/<repo>:<head_sha>`; execução na EC2 pendente
  - [x] Checar o endpoint `/health` após o deploy (Req. 5) — local no `deploy.sh` e externa no workflow, com tentativas e timeout limitados
  - [x] Evitar deploys simultâneos e versões antigas sobrescrevendo novas — `concurrency` + checagem do topo da `main`
- [ ] Realizar o primeiro deploy automatizado com sucesso

## 7. Validação e estabilização (Dias 11–12)

- [x] Corrigir problemas encontrados na esteira — auditoria sem AWS (timeouts, concorrência, chave SSH em `$RUNNER_TEMP`); revisar após o primeiro deploy
- [x] Demonstrar a implantação de uma nova versão pela esteira
- [x] Validar resposta do `/health` na EC2 após o deploy
- [x] Demonstrar que os dados persistem após a recriação do contêiner (Req. 9)
- [x] Registrar evidências da persistência (prints/logs)

## 8. Documentação, evidências e apresentação (Dias 13–14) — *10 pts*

- [ ] README atualizado (integrantes + instruções de uso) — instruções de uso prontas; faltam nomes dos integrantes
- [ ] Relatório curto (máx. 4 páginas ou Markdown no repositório) contendo: — `docs/RELATORIO_FINAL.md` criado, com campos a preencher
  - [x] Diagrama da arquitetura/esteira
  - [x] Infraestrutura e portas utilizadas
  - [x] Registro de custos e recursos utilizados — estrutura pronta; depende da EC2
  - [x] Dificuldades encontradas
  - [ ] Evidências da persistência de dados — mecanismo descrito; evidência depende da EC2
  - [ ] Integrantes e distribuição das tarefas — campos criados; faltam nomes
- [ ] Preparar vídeo de 3–5 min **ou** demonstração de até 5 min mostrando PR, Actions e API funcionando (a critério do docente) — roteiro em `docs/ROTEIRO_APRESENTACAO.md`; gravação pendente
- [ ] Garantir que todos os integrantes saibam explicar suas contribuições (Regras)

## 9. Encerramento de recursos (Dias 13–14)

- [ ] Encerrar/excluir os recursos AWS utilizados após a apresentação (Req. 10)
- [ ] Apresentar evidências do encerramento dos recursos (Req. 10)

## 10. Entrega no Moodle

- [ ] URL do repositório GitHub (com acesso concedido ao professor, se privado)
- [ ] URL ou IP da aplicação (enquanto estiver disponível)
- [ ] Link do Pull Request
- [ ] Link de ao menos 1 run de CI aprovado
- [ ] Link de ao menos 1 run de CD aprovado
- [ ] README atualizado
- [ ] Relatório curto
- [ ] Integrantes e distribuição das tarefas
- [ ] Vídeo ou demonstração

## 11. Bônus (opcional — até 10 pts, respeitando teto do docente)

- [x] Configurar domínio/TLS com justificativa
- [ ] Observabilidade adicional
- [ ] Rollback automatizado seguro
