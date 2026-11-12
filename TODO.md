# TODO — Trabalho final: Esteira de CI/CD para API na AWS

> Checklist derivado de [ENUNCIADO_ALUNOS.md](ENUNCIADO_ALUNOS.md). Prazo: 14 dias corridos. Valor: 100 pontos (+ bônus até 10).
> Fluxo-alvo: branch → Pull Request → CI (GitHub Actions) → merge na `main` → imagem no GHCR (tag = SHA) → CD na EC2 → checagem `/health`.

---

## 1. Preparação e repositório (Dias 1–3) — *Git/branches/PR e organização: 10 pts*

- [ ] Criar repositório próprio a partir do repositório-base fornecido pelo professor (Req. 1)
- [ ] Conceder acesso ao professor, caso o repositório seja privado
- [ ] Clonar o repositório e compreender a API existente
- [ ] Rodar os testes localmente com `pytest`
- [ ] Construir e executar a aplicação com Docker localmente
- [ ] Atualizar o README com os integrantes (Req. 1)
- [ ] Atualizar o README com instruções de uso (Req. 1)
- [ ] Garantir que nenhuma chave privada, token ou dado real esteja versionado (Regras)

## 2. Evolução funcional da API (Dias 4–5) — *Evolução funcional com testes: 10 pts*

- [ ] Criar ao menos 1 branch no padrão `feature/...` para o desenvolvimento (Req. 8)
- [ ] Implementar `DELETE /tasks/<id>` (Req. 7)
  - [ ] Retornar HTTP `204` quando a tarefa existir e for removida
  - [ ] Retornar HTTP `404` quando a tarefa não existir
- [ ] Escrever no mínimo 2 testes para `DELETE /tasks/<id>` (ex.: caso 204 e caso 404) (Req. 7)
- [ ] Implementar mais 1 melhoria na API (Req. 7)
- [ ] Escrever teste para a melhoria implementada (Req. 7)
- [ ] Confirmar que todos os testes passam localmente com `pytest`

## 3. Infraestrutura AWS EC2 (Dias 4–5) — *Infraestrutura EC2, rede e segurança: 15 pts*

- [ ] Provisionar instância EC2 Linux (Req. 2)
- [ ] Instalar e validar Docker funcional na instância (Req. 2)
- [ ] Configurar Security Group (Req. 2)
  - [ ] Liberar porta HTTP necessária para acesso à aplicação
  - [ ] Restringir acesso SSH — **não** utilizar `0.0.0.0/0` (Req. 6 / Regras)
  - [ ] Aplicar a solução segura para runners de deploy orientada pelo professor / guia fornecido (Req. 6 / Regras)
- [ ] Documentar o Security Group (regras, portas e origens) (Req. 2)
- [ ] Confirmar que a aplicação está acessível via HTTP (Req. 2)
- [ ] Monitorar custos dos recursos AWS durante o trabalho (Regras)

## 4. Integração Contínua — CI (Dias 6–7) — *Testes e CI funcionando nos PRs: 20 pts*

- [x] Criar workflow de CI no GitHub Actions (Req. 3) — `.github/workflows/ci.yml`
  - [x] Etapa de instalação de dependências (com cache pip)
  - [x] Etapa de execução do `pytest`
  - [x] Etapa de build da imagem Docker (`push: false`, sem login)
- [x] Garantir que a CI execute em Pull Requests (Req. 3)
- [x] Garantir que execução em PR **não** publique imagem (Req. 3) — job `publish` com `if` restrito a push na `main`
- [x] Garantir que execução em PR **não** dispare deploy (Req. 3) — CD só roda após CI de `push` na `main`
- [ ] Abrir ao menos 1 Pull Request da branch `feature/...` para `main` (Req. 8)
- [ ] Realizar revisão do PR (própria, se trabalho individual) (Req. 8)
- [ ] Comprovar CI aprovada no PR (Req. 8)
- [ ] Fazer merge do PR na `main` (Req. 8)

## 5. Publicação de imagem no GHCR (Dias 8–10) — *Docker e publicação versionada: 15 pts*

- [ ] Configurar publicação no GitHub Container Registry (Req. 4)
- [ ] Versionar a imagem com o **SHA do commit** como tag (Req. 4)
- [ ] Publicar a imagem **somente** quando mudanças entrarem na `main` (Req. 4)
- [ ] Verificar no GHCR a imagem publicada com a tag correspondente ao SHA

## 6. Entrega Contínua — CD (Dias 8–10) — *CD automático e verificação de saúde: 20 pts*

- [ ] Configurar Secrets/Variables no GitHub (Req. 6)
  - [ ] Não expor credenciais ou chaves no código
  - [ ] Não expor credenciais ou chaves nos logs
  - [ ] Não expor credenciais ou chaves no README
- [ ] Criar workflow de CD no GitHub Actions (Req. 5)
  - [ ] Condicionar a execução do CD ao sucesso da CI (Req. 5)
  - [ ] Implantar na EC2 a imagem correspondente ao SHA do commit (Req. 5)
  - [ ] Checar o endpoint `/health` após o deploy (Req. 5)
- [ ] Realizar o primeiro deploy automatizado com sucesso

## 7. Validação e estabilização (Dias 11–12)

- [ ] Corrigir problemas encontrados na esteira
- [ ] Demonstrar a implantação de uma nova versão pela esteira
- [ ] Validar resposta do `/health` na EC2 após o deploy
- [ ] Demonstrar que os dados persistem após a recriação do contêiner (Req. 9)
- [ ] Registrar evidências da persistência (prints/logs)

## 8. Documentação, evidências e apresentação (Dias 13–14) — *10 pts*

- [ ] README atualizado (integrantes + instruções de uso)
- [ ] Relatório curto (máx. 4 páginas ou Markdown no repositório) contendo:
  - [ ] Diagrama da arquitetura/esteira
  - [ ] Infraestrutura e portas utilizadas
  - [ ] Registro de custos e recursos utilizados
  - [ ] Dificuldades encontradas
  - [ ] Evidências da persistência de dados
  - [ ] Integrantes e distribuição das tarefas
- [ ] Preparar vídeo de 3–5 min **ou** demonstração de até 5 min mostrando PR, Actions e API funcionando (a critério do docente)
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

- [ ] Configurar domínio/TLS com justificativa
- [ ] Observabilidade adicional
- [ ] Rollback automatizado seguro
