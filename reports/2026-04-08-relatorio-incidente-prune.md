# Relatorio de incidente e validacao - 2026-04-08

## Resumo
- Problema observado: falha no `test:code-interpreter` por ausencia da imagem `code-interpreter-py:latest`.
- Erro retornado pelo servico: tentativa de `pull` da imagem com `pull access denied`.
- Causa raiz identificada: imagem local de execucao havia sido removida e nao existia keeper ativo.
- Correcao aplicada: rebuild da imagem com `label keep=true` e criacao do container `keep-code-interpreter-py` com `label keep=true`.
- Validacao concluida: `docker-system-prune.service` foi executado manualmente e a imagem/keeper permaneceram presentes.

## Contexto inicial informado
- O teste executado em `~/AI_UI/backend` falhou ao chamar `http://localhost:3405/v1/execute`.
- O stderr indicou:
  - `Failed to pull required Docker image: code-interpreter-py:latest`
  - `pull access denied for code-interpreter-py`
- Foi informado historico de recorrencia: normalmente rebuild da imagem resolvia temporariamente.

## Investigacao realizada
- Confirmado compose em execucao via labels do container `code-interpreter`:
  - `compose_files=/home/app/code-interpreter/compose.yml`
- Confirmado timer de limpeza ativo:
  - `docker-system-prune.timer` habilitado e ativo
  - script: `/usr/local/sbin/docker-system-prune.sh`
  - comando de limpeza: `docker system prune -a --volumes -f --filter "label!=keep=true"`
- Primeira rodada de diagnostico mostrou:
  - imagem `code-interpreter-py:latest` ausente
  - keeper `keep-code-interpreter-py` ausente

## Acoes executadas
1. Criado script de diagnostico em `/home/app/AI_UI/backend/t.sh` para verificar:
   - compose ativo
   - estado da imagem `code-interpreter-py:latest`
   - estado do keeper `keep-code-interpreter-py`
   - filtros do prune e status do systemd
   - logs recentes e resumo de risco
2. Rebuild da imagem interna com label de preservacao:
   - `sudo /snap/bin/docker build --label keep=true -t code-interpreter-py:latest -f docker/python-exec.Dockerfile .`
3. Criacao do keeper com label de preservacao:
   - `sudo /snap/bin/docker create --name keep-code-interpreter-py --label keep=true code-interpreter-py:latest true`
4. Reexecucao do diagnostico (`t.sh`) para confirmar estado protegido.
5. Teste de resiliencia real:
   - `sudo systemctl start docker-system-prune.service`
   - `sudo systemctl status docker-system-prune.service --no-pager -l`
   - `sudo bash /home/app/AI_UI/backend/t.sh`

## Resultados observados
- Servico de limpeza executou com sucesso (status `0/SUCCESS`).
- Apos a limpeza forcada:
  - imagem `code-interpreter-py:latest` presente
  - `keep_label=true` na imagem
  - keeper `keep-code-interpreter-py` presente (status `created`)
  - `keep_label=true` no keeper
  - resumo final do diagnostico: `[OK] Keep labels + prune filter are in place.`

## Estado final ate o momento
- Ambiente operacional validado contra o prune configurado atualmente.
- Causa imediata do erro inicial foi mitigada.
- Risco residual principal:
  - remover manualmente keeper/labels
  - rebuild da imagem sem `--label keep=true`

## Observacoes adicionais
- Durante a sessao, `compose.prod.yml` foi removido manualmente do repositorio (`rm /home/app/code-interpreter/compose.prod.yml`).
- Como o ambiente ativo usa `compose.yml`, essa remocao nao impactou o teste concluido acima.
