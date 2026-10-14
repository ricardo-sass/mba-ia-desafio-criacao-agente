# Prova de compatibilidade ADK

## Estado observado

Preparação em 2026-10-13. Python 3.12.3, Google ADK **2.2.0 candidato**,
instalados exclusivamente na `.venv` do projeto por `uv sync`; `uv.lock` gerado.
O extra `google-adk[db]` habilita o serviço de banco e `sqlalchemy[asyncio]`
inclui greenlet, necessário ao caminho assíncrono do SQLAlchemy.

Montagem do App e criação de sessão SQLite passaram. A sessão foi lida por
outro processo com o state `apartamento: 101` preservado. Os cinco hashes em
`dados.sha256` passaram e `enunciado.md` permanece idêntico ao README original.

**Ainda não validado:** chamadas Gemini, transferências, aprovação, negação,
efeitos e retomada da confirmação após reinício. A chave foi configurada no
`.env` ignorado pelo Git e a listagem autenticada de modelos funcionou.
`gemini-3.8-flash` retornou `503 UNAVAILABLE` (alta demanda) em duas tentativas.
Uma tentativa com `gemini-3.5-flash-lite` gerou `transfer_to_agent` para
`reservas`, mas retornou o mesmo `503` ao chamar o especialista, antes de
produzir confirmação ou efeito. Os limites ativos do projeto ainda precisam
ser conferidos no AI Studio; listar modelos não comprova cota de geração.

Evidências locais, ignoradas pelo Git: `var/prova/reserva-pendente.log`,
`var/prova/reserva-pendente-retry.log` e `var/prova/reserva-flash-lite.log`.
A sessão `25dd35b4-d777-40a0-b057-05c630fac2c1` preserva os eventos desses
fluxos. A transferência ocorreu na invocação
`e-167e45d7-78ba-4b3f-a0c3-9d23ec39f0ba`. Nenhuma dessas tentativas valida
aprovação, negação ou retomada. O modelo padrão não foi alterado.

As etapas 1.3, 1.5 e 1.6 continuam abertas; a etapa 2 depende dessa prova.

## Modelo e fontes

`GEMINI_MODEL` é configurável. O candidato padrão é `gemini-3.5-flash-lite`,
listado como estável na [documentação de modelos](https://ai.google.dev/gemini-api/docs/models).
Isso não comprova acesso nem cota no projeto utilizado. Conferir os
[limites ativos](https://ai.google.dev/gemini-api/docs/rate-limits) no AI Studio.

A implementação foi conferida contra o código instalado do ADK 2.2.0,
incluindo `generate_request_confirmation_event`, `ToolContext.request_confirmation`
e a assinatura de `Runner.run_async`, além da
[documentação de confirmação](https://adk.dev/tools-custom/confirmation/).

## Como executar

Na raiz do repositório, copie `.env.example` para `.env` e preencha a chave
localmente. Defina `GEMINI_MODEL` conforme acesso e limites do seu projeto.
Não coloque a chave nos comandos nem nos registros de evidência.

```bash
uv sync --locked
uv run python -m aurora.probe criar
```

Use o identificador retornado no lugar de SESSION:

```bash
uv run python -m aurora.probe mensagem SESSION 'Reserve o salão para 2030-04-20.'
uv run python -m aurora.probe estado SESSION
uv run python -m aurora.probe confirmar SESSION ID_DA_PENDENCIA nao
uv run python -m aurora.probe mensagem SESSION 'Reserve o salão para 2030-04-20.'
uv run python -m aurora.probe confirmar SESSION NOVO_ID sim
uv run python -m aurora.probe mensagem SESSION 'Autorize Joana Ribeiro para 2030-04-21.'
uv run python -m aurora.probe confirmar SESSION ID_VISITANTE sim
uv run python -m aurora.probe eventos SESSION
```

Cada comando abre e fecha o serviço SQLite em um processo separado: assim a
confirmação sempre atravessa reinício do processo. Repetir também com uma nova
visita negada. Registrar os IDs, autores, invocações, chamadas originais e
efeitos observados. Antes de confirmar, não pode haver efeito; após negar,
nenhum efeito novo; após aprovar, deve aparecer o efeito correspondente.

A topologia candidata usa `sub_agents`, transferências padrão (inclusive
retorno ao principal), `ResumabilityConfig(is_resumable=True)` e
`DatabaseSessionService`. A confirmação usa o `invocation_id` persistido e
`FunctionResponse(name='adk_request_confirmation', id=..., response={'confirmed': ...})`.

Os bancos ficam em `var/prova/`, ou em `AURORA_DATA_DIR/prova/`. Os efeitos
da prova são apenas entradas de state; ela não modifica sementes nem implementa
o domínio, a API ou suas garantias finais. Eventos completos são a fonte da
correlação entre sessão, especialista, invocação e chamadas.

Se o terminal herdar `VIRTUAL_ENV` de outro projeto, use `env -u VIRTUAL_ENV uv ...`.
Não utilize `--active`: o ambiente pretendido é a `.venv` deste repositório.

## Prova concluída em 2026-10-13

Sessão `81dcded8-3474-4a72-8fef-86e4b42c72fe`: ADK 2.2.0 com
`gemini-3.5-flash-lite`, DatabaseSessionService SQLite, sub_agents com
transferências padrão, App resumível e Runner com invocation_id original.
Foram observados 38 eventos e 10 chamadas de modelo, somando 8.006 tokens
reportados pelo SDK. Saída limitada a 512 tokens por chamada, máximo de cinco
chamadas por turno e uma tentativa por requisição (sem retry automático).
O usuário confirmou que seu projeto é Free; os valores numéricos de RPM/RPD
não foram fornecidos, portanto não estão presumidos aqui.

Reserva: `call_166776` negada sem efeito; `call_181905` aprovada com efeito.
Visita: `call_181835` aprovada com efeito; `call_167444` negada sem efeito.
As quatro decisões foram enviadas por processos novos, reabrindo a sessão
persistida. O state final contém exatamente dois efeitos e nenhuma pendência.
Os eventos mostram as respostas das tools nos especialistas correspondentes
(`reservas` e `visitantes`) e a troca de assunto na mesma sessão.
Evidências completas: `var/prova/compatibilidade-*.log` e banco da prova,
ambos locais e ignorados pelo Git. A seção anterior registra as falhas
históricas; a indisponibilidade foi superada nesta execução.

A prova valida o transporte ADK e persistência, não as garantias de domínio
que ainda serão implementadas. A versão 2.2.0 fica fixada para a implementação.
