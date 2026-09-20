## Escopo

<!-- O que este PR faz (só o card). Fora de escopo vira follow-up. -->

## Provas (cole a saída real — checkbox sem evidência não vale)

- [ ] **Base sincronizada** — `git rev-list --count HEAD..origin/main` tem que ser `0`:

  ```
  <!-- colar saída -->
  ```

- [ ] **Testes** — arquivos de teste alterados rodando (`cd api && .venv/bin/python -m pytest -q`):

  ```
  <!-- colar saída -->
  ```

- [ ] **Front compila** (se mexeu no contrato entre repos) — `npm run build` em `web/`:

  ```
  <!-- colar saída -->
  ```

- [ ] **Rota chamada de verdade** — `SEED_DEMO=true` + `curl` na rota afetada (ou TestClient):

  ```
  <!-- colar saída -->
  ```

## Follow-ups

<!-- ideias fora do escopo que ficam para depois (se houver) -->

## Regras

- [ ] Sem rodapé de IA no commit/PR
- [ ] Nada de padronizar/prod em bancos compartilhados
- [ ] Não mexi em CI/infra