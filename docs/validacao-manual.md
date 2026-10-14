# Validação manual

Este roteiro registra a validação executada e os comandos para repetir o aceite. A
chave do Gemini fica somente no `.env`; o projeto usado para a prova estava no nível
Free e o modelo foi `gemini-3.5-flash-lite`.

## Preparação

```bash
cp .env.example .env
# preencher GOOGLE_API_KEY e, opcionalmente, GEMINI_MODEL
uv sync --locked
uv run aurora reset
uv run aurora serve
```

O reset deve ser executado com a API parada. As consultas diretas abaixo não usam o
modelo:

```bash
curl http://localhost:8000/apartamentos/101/reservas
curl http://localhost:8000/apartamentos/302/visitantes
```

## Fluxo do avaliador

1. Criar S1 com `POST /sessoes` e apartamento `101`.
2. Consultar reservas/visitantes de outro apartamento; a resposta e os eventos não
   podem conter `RSV-4821` nem `Marina Duarte`.
3. Tentar cancelar o salão de `2030-03-16`; a reserva do 302 permanece.
4. Cancelar a quadra própria de `2030-03-09`; ela deixa de ser ativa.
5. Reservar a quadra em `2030-04-06`; não há confirmação.
6. Reservar o salão em `2030-04-20`; surge uma pendência e nada é gravado.
7. Negar pela rota de confirmações; a pendência termina sem efeito.
8. Repetir, aprovar e reenviar o mesmo ID; a primeira resposta é `200`, o reenvio é
   `409` e existe uma única reserva.
9. Responder ID inexistente e sessão inexistente; os códigos são `409` e `404`.
10. Tentar o salão ocupado em `2030-03-16`; eventual aprovação resulta em
    indisponibilidade sem revelar o 302 ou `RSV-4821`.
11. Solicitar Joana Ribeiro em `2030-04-21`, inclusive escrevendo consentimento no
    chat; somente a rota de confirmação cria a autorização.
12. Perguntar o horário da piscina aos domingos; o resultado deve citar o artigo 22,
    com somente o trecho pertinente nos eventos.
13. Reiniciar a API sem reset; sessão, eventos, reservas e pendências permanecem.
14. Criar sessões 101/201, solicitar o salão em `2030-05-11` e aprovar as duas; o
    índice transacional permite uma única reserva ativa e ambas as respostas são `200`.
15. Conferir hashes, lock, ausência de segredos, agentes, tools e índice no repositório.

## Evidência já executada

O ADK 2.2.0 foi testado com `DatabaseSessionService` em SQLite, `sub_agents`,
`ResumabilityConfig(is_resumable=True)` e `Runner.run_async` com o `invocation_id`
original. Em processos separados, reserva e visitante foram aprovados e negados;
as aprovações criaram efeitos no state e as negações não criaram efeitos. A mesma
sessão mudou de reservas para visitantes. A evidência detalhada está em
`docs/prova-adk.md` e os logs locais em `var/prova/` são ignorados pelo Git.

O armazenamento local também foi validado sem modelo: duas restaurações consecutivas,
reserva gratuita, conflito concorrente, cancelamento, geração de código distinto e
preservação do catálogo de códigos.

## Estado da execução

Instalação com `uv sync --locked`, compilação do pacote, duas restaurações, rotas
diretas, criação de sessão, consulta de pendência paga, concorrência SQLite e hashes
foram reexecutados neste checkout. A prova completa do transporte ADK está em
`docs/prova-adk.md`. Os passos 3–6 foram executados em uma sessão HTTP persistida:
a tentativa de acesso ao 302 permaneceu isolada, a quadra própria foi cancelada e
uma nova quadra foi criada sem confirmação. Também foram executados negação, reenvio
(`409`), ID inexistente (`409`) e sessão inexistente (`404`). Durante a tentativa de
aprovação seguinte o projeto atingiu o limite Free de 15 requisições por minuto para
`gemini-3.5-flash-lite` (`429 RESOURCE_EXHAUSTED`, espera informada de 55s). As
chamadas de modelo foram interrompidas para evitar consumo adicional. A branch local
atual é `dev`; nenhuma publicação ou fork foi executada.

Após o reset da cota, a aprovação foi concluída: a reserva recebeu código
`RSV-FB8CA128ABF94088A3D277B66B6EA84F`, o reenvio retornou `409`, Joana Ribeiro foi
autorizada, e a consulta da piscina retornou o artigo 22, 9h–20h, sem capítulos
irrelevantes nos 70 eventos. Reabrir a API preservou os 70 eventos e os efeitos.
O conflito do salão ocupado foi verificado diretamente no serviço transacional e
retornou apenas `indisponivel`, sem expor o proprietário.

Após novo reinício, a consulta de reservas retornou `200`, mostrou os dois códigos
criados e aumentou o histórico de 70 para 78 eventos.

Na disputa em `2030-05-11`, as duas sessões receberam pendências. A reserva do 101
foi executada com `RSV-84C54E504E7B4E29B17B99F7B8EFADC3`; a do 201 terminou como
`indisponivel`, e o índice deixou exatamente uma reserva ativa. Sem modelo, foram
verificados ainda ID de outra sessão (`409`), negação de visitante sem efeito,
tentativa de alterar argumentos aprovados e concorrência em área gratuita.
