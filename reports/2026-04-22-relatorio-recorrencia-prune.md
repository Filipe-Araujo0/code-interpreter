# Relatorio de recorrencia e correcao operacional - 2026-04-22

## Resumo
- Problema observado: nova falha no `test:code-interpreter` por ausencia da imagem `code-interpreter-py:latest`.
- Erro retornado pelo servico: tentativa de `pull` da imagem com `pull access denied`.
- Causa provavel da recorrencia: uso de fluxo manual documentado no `README.md` que reconstruia a imagem sem `label keep=true` e sem recriar explicitamente o keeper.
- Correcao aplicada: execucao do fluxo resiliente via `docker compose` para rebuild do keeper e refresh do servico.
- Correcao preventiva aplicada no repositorio: `README.md` atualizado para documentar o fluxo correto e remover a instrucao insegura.
- Validacao concluida: o usuario executou o comando recomendado e confirmou que voltou a funcionar.

## Contexto inicial informado
- O teste executado em `~/AI_UI/backend` voltou a falhar ao chamar `http://localhost:3405/v1/execute`.
- O stderr indicou:
  - `Failed to pull required Docker image: code-interpreter-py:latest`
  - `pull access denied for code-interpreter-py`
- Havia um relatorio anterior no repositorio registrando o mesmo tipo de incidente em `2026-04-08`.

## Investigacao realizada
- Confirmado no codigo do executor que, quando a imagem configurada nao existe localmente, o servico tenta fazer `pull` remoto:
  - arquivo: `app/services/docker_executor.py`
  - comportamento: `inspect` da imagem seguido de `pull` em caso de `404`
- Confirmado no host que o prune periodico continua ativo:
  - timer: `docker-system-prune.timer`
  - script: `/usr/local/sbin/docker-system-prune.sh`
  - comando configurado: `docker system prune -a --volumes -f --filter "label!=keep=true"`
- Confirmado no relatorio anterior que o risco residual ja identificado era:
  - rebuild da imagem sem `--label keep=true`
  - remocao manual de keeper/labels
- Confirmado no repositorio que `compose.yml` ja contem a mitigacao correta:
  - servico `code-interpreter-py-keeper`
  - label `keep=true` no build da imagem
  - label `keep=true` no container keeper
- Confirmado que o `README.md` ainda documentava, ate esta data, um fluxo manual inseguro:
  - `docker build -t code-interpreter-py:latest -f docker/python-exec.Dockerfile .`
  - esse fluxo nao aplicava `keep=true`
  - esse fluxo tambem nao recriava explicitamente o keeper

## Causa provavel da recorrencia
- A mitigacao do incidente anterior ficou implementada no `compose.yml`, mas a documentacao principal continuou sugerindo um procedimento manual que contornava essa protecao.
- Isso tornava possivel reconstruir `code-interpreter-py:latest` sem a label de preservacao, deixando a imagem novamente elegivel para o `docker system prune`.
- Depois da remocao da imagem local, o servico tentou `pull` remoto ao executar codigo, mas a imagem e local e nao existe em registry publico.
- Resultado final: recorrencia do mesmo erro observado em `2026-04-08`.

## Acoes executadas
1. Revisao do `README.md` e do relatorio anterior para comparar a mitigacao aplicada com o fluxo operacional documentado.
2. Revisao do `compose.yml` para confirmar a existencia do keeper e das labels `keep=true`.
3. Identificacao da divergencia entre:
   - mitigacao operacional correta no `compose.yml`
   - instrucao insegura ainda presente no `README.md`
4. Recomendacao do comando operacional correto para restaurar o ambiente:
   - `docker compose build code-interpreter-py-keeper && docker compose up -d code-interpreter-py-keeper code-interpreter`
5. Atualizacao do `README.md` para que:
   - o fluxo principal passe a usar `docker compose build code-interpreter-py-keeper`
   - o restart passe a usar `docker compose up -d code-interpreter-py-keeper code-interpreter`
   - a alternativa manual permaneça documentada apenas na forma segura, com `--label keep=true` e recriacao do keeper

## Resultados observados
- O usuario executou o comando recomendado e confirmou que o fluxo voltou a funcionar.
- A documentacao do repositorio deixou de orientar o rebuild inseguro que reabria o incidente.
- O repositorio passou a alinhar:
  - documentacao operacional
  - mitigacao implementada no `compose.yml`
  - risco residual ja registrado no relatorio anterior

## Estado final ate o momento
- Problema operacional restaurado no ambiente atual.
- Causa de recorrencia identificada e documentada.
- Correcao preventiva aplicada na documentacao para reduzir repeticao do erro.
- Risco residual principal:
  - execucao futura de rebuild manual fora do fluxo documentado
  - remocao manual do keeper ou de labels `keep=true`
  - alteracoes operacionais fora deste repositorio que ignorem o `compose.yml`

## Observacoes adicionais
- Nao houve necessidade de alterar codigo Python do servico; a recorrencia foi explicada por divergencia entre operacao documentada e protecao ja existente no ambiente.
- Foi aplicado um principio do Programador Pragmatico ao preferir o fluxo automatizado do `docker compose` em vez de procedimento manual fragil: reduzir variabilidade operacional e mover o conhecimento critico para a automacao reutilizavel.
