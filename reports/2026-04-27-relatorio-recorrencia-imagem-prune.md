# Relatorio de recorrencia e mitigacao - imagem de execucao indisponivel - 2026-04-27

## Resumo
- Problema observado: recorrencia do erro em que a imagem local `code-interpreter-py:latest` fica indisponivel para o container de execucao.
- Sintoma esperado no servico: tentativa de `pull` remoto da imagem local e falha com `pull access denied`.
- Correcao anterior: build da imagem com `label keep=true` e criacao de keeper via `docker compose`.
- Reavaliacao feita nesta data: a causa continua relacionada a imagem indisponivel, nao aos containers efemeros de execucao.
- Ajuste aplicado: o keeper `code-interpreter-py-keeper` passou a ficar em execucao continua com `sleep infinity` e `restart: unless-stopped`.
- Objetivo do ajuste: manter uma referencia viva para `code-interpreter-py:latest`, reduzindo a dependencia apenas de labels e de um container keeper parado.

## Contexto
- O usuario informou que o mesmo erro voltou a acontecer e esclareceu que o problema era a imagem, nao o container efemero criado para executar codigo.
- Havia um report anterior em `reports/2026-04-22-relatorio-recorrencia-prune.md` indicando que o risco residual era rebuild manual sem `keep=true` ou remocao manual do keeper/labels.
- O prune ativo documentado no ambiente usa:
  - `docker system prune -a --volumes -f --filter "label!=keep=true"`

## Investigacao realizada
- O report de 2026-04-22 foi revisado para confirmar a causa ja registrada: imagem local removida e tentativa posterior de `pull` remoto.
- O `compose.yml` foi revisado e ja continha:
  - build da imagem `code-interpreter-py:latest` pelo servico `code-interpreter-py-keeper`
  - label `keep=true` no build da imagem
  - label `keep=true` no keeper
- O estado anterior do keeper era:
  - `command: ["true"]`
  - `restart: "no"`
  - resultado: container criado pelo compose terminava imediatamente e permanecia parado.
- Uma hipotese inicial de adicionar labels aos containers efemeros de execucao foi descartada porque nao atacava o sintoma informado: imagem local ausente.

## Consulta a documentacao oficial do Docker
- Foi consultada a documentacao oficial de `docker system prune`:
  - `https://docs.docker.com/reference/cli/docker/system/prune/`
- Tambem foram consultadas as referencias oficiais relacionadas a prune de imagens e containers:
  - `https://docs.docker.com/reference/cli/docker/image/prune/`
  - `https://docs.docker.com/reference/cli/docker/container/prune/`
- Entendimento aplicado:
  - `docker system prune -a` remove recursos Docker nao utilizados, incluindo imagens nao utilizadas.
  - o filtro `label!=keep=true` remove apenas recursos que nao possuem a label `keep=true`.
  - uma imagem usada por container em execucao nao deve ser classificada como imagem nao utilizada.
  - manter o keeper em execucao e com label torna a protecao menos dependente de um container parado e mais alinhada ao criterio de uso da imagem.

## Causa provavel da recorrencia
- A protecao anterior dependia de a imagem e o keeper parado estarem corretamente rotulados.
- Na pratica operacional, a imagem ainda podia voltar a ficar vulneravel quando:
  - ocorria rebuild manual sem `--label keep=true`
  - o keeper era removido ou nao recriado corretamente
  - o ambiente executava uma limpeza enquanto a imagem nao tinha referencia viva suficiente
- Como a imagem `code-interpreter-py:latest` e local e nao existe em registry publico, a ausencia local leva o executor a tentar `pull`, resultando em `pull access denied`.

## Acoes executadas
1. Revertida a alteracao inicial que adicionava labels aos containers efemeros de execucao, por nao resolver o problema de imagem ausente.
2. Atualizado `compose.yml` para manter o keeper vivo:
   - antes: `command: ["true"]` e `restart: "no"`
   - depois: `command: ["sleep", "infinity"]` e `restart: unless-stopped`
3. Atualizado o comentario do keeper no `compose.yml` para refletir que ele mantem uma referencia viva a imagem.
4. Atualizado o `README.md` para que o fluxo manual equivalente use `docker run -d ... sleep infinity`, em vez de `docker create ... true`.
5. Atualizado o comentario operacional no `docker/python-exec.Dockerfile` para documentar keeper em execucao continua.

## Validacao realizada
- Executado `docker compose config` no repositorio.
- Resultado: configuracao do compose valida.
- Nao foi possivel inspecionar o estado real de imagens/containers no Docker daemon a partir desta sessao porque:
  - o usuario atual nao tem permissao no socket Docker
  - `sudo` exige senha interativa

## Estado final esperado
- Apos executar o fluxo de restauracao no host com permissao Docker, o ambiente deve manter:
  - imagem `code-interpreter-py:latest` reconstruida com `keep=true`
  - keeper `keep-code-interpreter-py` em execucao continua
  - keeper com `restart: unless-stopped`
  - API `code-interpreter` atualizada para depender do keeper
- Com esse estado, a imagem nao deve ser removida pelo prune ativo porque:
  - possui `keep=true`
  - esta referenciada por container em execucao
  - o keeper tambem possui `keep=true`

## Comando operacional recomendado
```bash
cd ~/code-interpreter
docker compose build code-interpreter-py-keeper
docker compose up -d --force-recreate code-interpreter-py-keeper code-interpreter
```

## Riscos residuais
- Remocao manual do keeper ou da imagem.
- Rebuild manual da imagem sem `--label keep=true`.
- Alteracao do script de prune para ignorar ou remover recursos com `keep=true`.
- Execucao de `docker compose down` sem posterior `docker compose up -d code-interpreter-py-keeper code-interpreter`.

## Observacoes adicionais
- Foi aplicado o principio pragmatico de reduzir variabilidade operacional: o conhecimento critico saiu de um procedimento manual fragil e foi reforcado no `compose.yml`.
- A solucao tambem segue o principio de tornar estados importantes explicitos: a imagem de execucao deve estar simultaneamente rotulada e em uso por um keeper vivo.
