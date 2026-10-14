## Context

O repositório não contém aplicação nem especificações anteriores. `README.md` é o contrato de entrega; os cinco arquivos em `dados/` são sementes imutáveis. A proposta cobre a implementação completa para moradores e a inspeção direta pelo avaliador.

Os dados existentes incluem quadra gratuita, salão com taxa de R$ 150 e churrasqueira com taxa de R$ 80. O regulamento tem 14 capítulos; o artigo 22 estabelece fechamento da piscina às 20h aos domingos e feriados. Esses valores devem vir dos arquivos e do armazenamento, nunca de fatos fixados no prompt.

## Goals / Non-Goals

**Goals:** implementar o contrato HTTP, executar operações por tools ADK, impor as cinco garantias no código, preservar conversas após reinício e permitir instalação/restauração reproduzíveis. O aceite é o fluxo manual de 15 passos, acrescido da aprovação e negação de pendências criadas antes de reiniciar.

**Non-Goals:** interface, autenticação real, pagamento/estorno, deploy, evals, suíte automatizada obrigatória e aplicação de restrições de antecedência, datas passadas, horários ou capacidade. Consultar essas regras no regulamento não as transforma em validações de reserva.

## Decisions

### 1. Estrutura e execução local

Adotar Python >= 3.12, uv, FastAPI, Uvicorn e SQLite. FastAPI organiza validação e rotas assíncronas; SQLite mantém a execução local sem serviço adicional. PostgreSQL seria uma alternativa para maior escala, mas acrescentaria infraestrutura desnecessária ao desafio. Arquivos JSON mutáveis não oferecem a exclusividade transacional exigida.

Estrutura planejada (os caminhos ainda serão criados na implementação):

| Caminho | Responsabilidade |
| --- | --- |
| `src/aurora/api.py`, `schemas.py` | Contrato HTTP, validação e serialização |
| `src/aurora/config.py` | Ambiente, caminhos e modelo Gemini |
| `src/aurora/agents.py` | Principal e especialistas |
| `src/aurora/runtime.py` | App, Runner, sessões, eventos e retomada |
| `src/aurora/identity.py` | Vínculo imutável sessão/apartamento |
| `src/aurora/confirmations.py` | Registro, correlação e ciclo das pendências |
| `src/aurora/tools/` | Tools de reservas, visitantes e regulamento |
| `src/aurora/storage.py`, `repositories.py` | Esquema, transações e consultas com escopo |
| `src/aurora/regulation.py` | Índice por capítulo/artigo e recuperação seletiva |
| `src/aurora/cli.py` | Subida e restauração explícita |
| `docs/enunciado.md`, `docs/validacao-manual.md` | Contrato original preservado e roteiro de aceite |

Comandos a implementar: `uv sync`, `uv run aurora reset` e `uv run aurora serve`, sendo o último responsável por responder em `http://localhost:8000`. Usar um worker no comando padrão e serialização assíncrona por sessão, permitindo sessões diferentes em paralelo. A integridade das reservas permanece no banco, independentemente desse lock.

Versionar `pyproject.toml`, `uv.lock` e `.env.example` com `GOOGLE_API_KEY=`, `GEMINI_MODEL=` e `AURORA_DATA_DIR=` sem valores. Documentar o modelo validado e o diretório padrão `var/`; ignorar `.env`, bancos, arquivos WAL/SHM e ambiente virtual. O modelo é configurável, com um padrão concreto escolhido na implementação. Fixar uma versão exata de ADK 2.x >= 2.2.0 após a prova inicial, sem presumir que a versão mais recente é compatível.

### 2. Principal e três especialistas

O principal distribui intenções entre `reservas`, `visitantes` e `regulamento`. Os especialistas de reservas e visitantes concentram operações com efeitos; o de regulamento isola a recuperação documental. Cada especialista tem apenas as tools de sua responsabilidade, e todos usam Gemini.

A primeira topologia a validar usa especialistas em `sub_agents`, acionados por transferência do principal, com retorno ao principal para mudança de assunto. Tools transacionais ficam no especialista que receberá a retomada. O principal não possui tools genéricas de SQL, arquivos, HTTP administrativo ou edição de state. Agente único não atende ao enunciado; `AgentTool` é uma alternativa caso a transferência não passe pela prova persistida, mas só será adotada após demonstrar a mesma correlação e continuidade. A configuração final de transferências será documentada com evidências.

### 3. Identidade fora do controle do modelo — garantia 2

Criar um identificador aleatório para cada sessão, registrar `session_id → apartamento, adk_user_id` no banco de domínio e inicializar o state ADK com o apartamento. Esse vínculo não tem operação de atualização. Cada tool resolve a sessão pelo contexto confiável, confere o state contra o vínculo persistido e obtém daí o apartamento. Divergência encerra a operação sem efeitos. Nenhuma tool recebe apartamento, usuário ADK, autorização ou confirmação como argumentos escolhidos pelo modelo.

Consultas pessoais e cancelamentos incluem o apartamento no predicado SQL. Buscar reserva por área/data ou código para cancelar sempre ocorre dentro desse escopo. Resultado vazio recebe mensagem genérica, sem revelar se a reserva existe para outra pessoa. Disponibilidade retorna apenas área, data e livre/ocupada; não carrega proprietário, nome ou código de terceiros no resultado da tool. Listas administrativas não são tools do agente.

Dados são minimizados antes de ingressarem nos eventos, pois a rota de eventos deve devolver o conteúdo completo. Ocultar dados apenas da resposta final não atende à garantia. Prompts ajudam o fluxo, mas não são usados como controle de acesso.

### 4. Persistência de domínio e sessões — garantia 3

Manter dois bancos locais no mesmo diretório: `condominio.sqlite3` para domínio e `sessoes.sqlite3` para o serviço ADK. O candidato inicial é `DatabaseSessionService` com SQLite; sua adequação à confirmação depende da prova descrita abaixo. Separar os bancos evita acoplamento das tabelas do domínio ao esquema interno do SDK. `app_name` e o mapeamento de `user_id` devem ser estáveis entre reinícios.

Esquema de domínio planejado:

- `apartamentos(numero PK, morador)` e `areas(id PK, nome, taxa_centavos)`, carregados das sementes; converter dinheiro para centavos sem cálculos em ponto flutuante.
- `reservas(codigo PK, apartamento FK, area FK, data, status, operacao_id UNIQUE nullable)`, conservando linhas canceladas.
- `codigos_emitidos(codigo PK)`, incluindo sementes e todos os códigos emitidos, conservado também pela restauração.
- `visitantes(id PK, apartamento FK, nome, data, operacao_id UNIQUE nullable)`.
- `vinculos_sessao(session_id PK, apartamento FK, adk_user_id)`.
- `confirmacoes(id PK, session_id FK, invocation_id, agente, tool_call_id, confirmation_call_id, acao, argumentos_json, status, decisao, resultado_json)`.
- `operacoes(id PK, session_id, tool_call_id, resultado_json)`, para reapresentar resultado de uma execução já efetivada.

Gerar código com UUID e registrar em `codigos_emitidos` na mesma transação da reserva; em colisão, gerar novamente. Assim a unicidade não depende apenas da probabilidade do UUID. Cancelar muda status, sem apagar o código. Uma restauração repõe as sementes, mas conserva o registro histórico de códigos novos para não reutilizá-los.

O Runner persiste todos os eventos, inclusive chamadas e respostas de tools, transferências e confirmações. A rota de eventos serializa os objetos completos, em ordem de persistência, sem sumarização nem compactação destrutiva. Subida normal só abre/inicializa o armazenamento necessário; jamais repõe sementes sobre dados existentes.

### 5. Confirmações persistidas e retomada — garantia 1

A integração ADK deve usar a confirmação de tool e responder com `FunctionResponse` de nome `adk_request_confirmation`, ID correspondente à chamada de confirmação e campo `confirmed`. Ao habilitar retomada no App, também é necessário correlacionar a invocação original. A documentação ainda declara limitações com `DatabaseSessionService`; portanto esse arranjo é uma hipótese a validar, não compatibilidade já comprovada. [Confirmação de ações do ADK](https://adk.dev/tools-custom/confirmation/).

O protocolo da aplicação será:

1. A tool valida área/data ou nome/data, resolve o apartamento e calcula a necessidade de aprovação pela taxa armazenada ou pelo tipo visitante. Taxa, apartamento e decisão não são argumentos livres do modelo.
2. Antes de qualquer efeito que exija aprovação, solicita confirmação ADK. O adaptador associa os eventos a uma pendência persistida contendo os argumentos normalizados e imutáveis, ID público, IDs ADK, invocação e especialista autor. Persistir a correlação antes de devolver a resposta HTTP.
3. A API projeta todas as pendências da sessão em `{id, acao, detalhes}`. Reservas incluem área, data e taxa; visitas incluem nome e data. Pendência não ocupa a agenda nem cria autorização de entrada.
4. A rota de confirmações verifica primeiro a existência da sessão e depois a pendência dentro dela. Um compare-and-set de `pendente` para `respondida` registra a decisão. ID alheio, desconhecido ou já respondido retorna `409`, sem chamar o Runner.
5. Somente essa rota monta a resposta estruturada ao ADK a partir dos dados persistidos; mensagens aceitam apenas texto e nunca são convertidas em `FunctionResponse`. O cliente não escolhe tool, agente, argumentos ou invocação.
6. O Runner retoma o especialista solicitante. A tool exige a decisão persistida e a correlação exata com sua operação, além do contexto ADK; uma aprovação não autoriza uma chamada diferente nem argumentos modificados. Negação finaliza sem alteração de reservas/visitantes.
7. Aprovação executa a operação numa transação curta que grava o resultado idempotente junto ao efeito. Os estados terminais são `executada`, `negada` ou `conflito`. Reexecução interna da mesma operação devolve o resultado registrado, enquanto reenvio HTTP do ID respondido continua sendo `409`.
8. Montar a resposta HTTP após conferir o resultado persistido da operação; nunca anunciar sucesso apenas porque o Runner terminou. Em disputa de agenda, devolver recusa normal e HTTP `200`.

Como os bancos ADK e de domínio não compartilham transação, `respondida` representa trabalho de retomada durável. Antes de aceitar novos turnos, o runtime reconcilia decisões sem resultado terminal com os eventos e retoma a mesma invocação. Uma operação já efetivada retorna seu resultado sem repetir o efeito. Não manter transação SQLite aberta durante chamadas Gemini. A idempotência também cobre reserva gratuita e cancelamento por identidade interna da chamada. A retomada do SDK pode repetir tools, o que reforça essa decisão. [Retomada do ADK](https://github.com/google/adk-docs/blob/main/docs/runtime/resume.md).

Na etapa inicial, executar uma prova com principal e especialistas reais, SQLite, confirmação positiva e negativa, troca de especialista e reinício antes da aprovação. Fixar versão, topologia, flags de transferência, `ResumabilityConfig` e parâmetros do Runner apenas após essa prova. Se `DatabaseSessionService` falhar, investigar a implementação da versão fixada e avaliar um serviço persistente compatível com o contrato ADK; não substituir por memória nem aprovar a operação fora do protocolo de confirmação. Registrar a decisão revisada antes de expandir a implementação.

Para mensagens recebidas enquanto há pendências, escolher comportamento simples: retornar `200` com orientação para usar a rota de confirmações e a lista atual, sem iniciar nova execução do modelo. A resposta textual, inclusive “confirmo”, não muda o estado. Uma invocação pode produzir várias pendências; cada ID mantém correlação e consumo próprios.

### 6. Exclusividade transacional — garantia 5

Criar `CREATE UNIQUE INDEX reservas_area_data_ativa ON reservas(area, data) WHERE status = 'ativa'`. A unicidade parcial preserva reservas canceladas enquanto limita as ativas. O mecanismo é suportado pelo SQLite. [Índices parciais do SQLite](https://www.sqlite.org/partialindex.html).

Tanto reserva gratuita quanto reserva paga aprovada usam o mesmo serviço transacional de inserção. Uma consulta prévia pode melhorar a resposta, mas não decide a integridade. Duas pendências podem existir para a mesma data livre; nenhuma cria bloqueio antecipado. No momento da gravação, uma transação vence e a outra traduz a violação específica do índice em `indisponivel`, sem expor dados da reserva vencedora. Outros erros de integridade não são disfarçados como indisponibilidade.

Usar transações curtas, chaves estrangeiras, `busy_timeout` e repetição limitada de operações que falhem por contenção transitória. Validar a disputa com conexões independentes e requisições simultâneas. WAL facilita convivência entre leitores e escritor, mas continua permitindo apenas um escritor por vez e não substitui a restrição de unicidade. [WAL do SQLite](https://www.sqlite.org/wal.html).

### 7. Regulamento recuperado por assunto — garantia 4

Ler o arquivo no processo para construir um índice local por capítulo e artigo, sem enviá-lo ao modelo. Manter catálogo de assuntos e sinônimos, com termos normalizados; primeiro selecionar o assunto e depois artigos pertinentes dentro dele. A tool retorna título, número do artigo e texto dos trechos selecionados. Para horário da piscina aos domingos, retornar o artigo 22 do capítulo IV, sem capítulos vizinhos.

Consultas ambíguas devolvem pedido de esclarecimento sem trechos. Se houver vários assuntos explícitos, recuperar cada um separadamente. Não oferecer fallback que devolva o documento inteiro nem busca global top-k que misture capítulos apenas por palavras genéricas. Perguntas sem suporte recebem resposta de informação não encontrada. Pedidos para despejar o regulamento inteiro recebem orientação para escolher um assunto.

O principal não recebe o regulamento nas instruções e o especialista também depende da tool para obter conteúdo. A seleção ocorre antes da resposta da tool, de modo que nenhum evento registre capítulos irrelevantes. Um banco vetorial seria possível, mas desnecessário para um documento fixo cuja estrutura já oferece segmentação precisa.

### 8. Contrato HTTP e decisões nos pontos livres

| Rota | Entrada | Resposta |
| --- | --- | --- |
| `POST /sessoes` | `{apartamento}` | `201 {session_id}` |
| `POST /sessoes/{session_id}/mensagens` | `{texto}` | `200 {resposta, confirmacoes_pendentes}` |
| `POST /sessoes/{session_id}/confirmacoes` | `{id, confirmado}` | Mesmo envelope, `200`; ID não pendente: `409` |
| `GET /sessoes/{session_id}/eventos` | — | `200` com lista completa de eventos em ordem |
| `GET /apartamentos/{apartamento}/reservas` | — | `200 [{codigo, area, data}]`, somente ativas |
| `GET /apartamentos/{apartamento}/visitantes` | — | `200 [{nome, data}]` |

Todas as rotas com sessão desconhecida retornam `404`, inclusive confirmação com ID inválido; validar sessão primeiro. `resposta` é string, podendo ser vazia; `confirmacoes_pendentes` sempre contém todas as pendências da sessão ou `[]`. Rotas de verificação consultam repositórios diretamente e não usam Gemini. Datas são ISO `AAAA-MM-DD`; validar existência da data, mas aceitar datas passadas. Adotar `404` para apartamento inexistente e `422` para payload inválido, com booleano estrito em `confirmado`. Respostas são JSON.

### 9. Restauração, documentação e rastreabilidade

`aurora reset` será documentado para execução com a API parada. Ele restaura reservas e visitantes a partir dos arquivos, limpa sessões, eventos, vínculos, operações e confirmações e preserva o catálogo de códigos já emitidos. Limpar as sessões evita que pendências antigas alterem o estado restaurado. A execução repetida deve manter os mesmos dados iniciais visíveis. Nenhum arquivo de `dados/` é regravado.

Antes de substituir o README, preservar o enunciado em `docs/enunciado.md`. O README final terá Arquitetura, Garantias e Como rodar; as referências a arquivos e funções só serão preenchidas com código existente. `docs/validacao-manual.md` mapeará os 15 passos do avaliador a resultados observados, incluindo os códigos e nomes das sementes, HTTP, eventos, reinício e concorrência. Testes automatizados podem ser uma evolução futura, sem condição adicional de entrega nesta mudança.

## Risks / Trade-offs

- Confirmação ADK funciona em memória, mas falha no especialista com sessão persistida → executar a prova antes da implementação completa e registrar versão/configuração que realmente funciona.
- Falha entre decisão, gravação de domínio e evento ADK → decisão durável, reconciliação e resultado idempotente na mesma transação do efeito.
- Texto do modelo afirma efeito não ocorrido → conferir o resultado de domínio ao responder confirmações; avaliar pelas rotas de verificação e eventos.
- Contenção de SQLite → transações curtas, WAL, espera/repetição limitada e validação com duas aprovações simultâneas; sem manter locks SQL durante chamadas externas.
- Busca lexical não resolve pergunta ambígua → pedir esclarecimento; não ampliar automaticamente o contexto para capítulos não relacionados.
- Limites Gemini variam por projeto → consultar modelos oficiais e limites do Google AI Studio na implementação, sem presumir acesso ou cota disponível.
- Sessão exposta sem autenticação real → comportamento exigido pelo enunciado; controles administrativos e identidade real permanecem fora de escopo.

## Migration Plan

Não há código legado nem banco a migrar. Preservar o enunciado e registrar hashes dos arquivos de dados; executar a prova ADK; construir armazenamento, tools e rotas; validar todos os fluxos; finalizar documentação e lock. O primeiro uso segue `uv sync`, configuração de `.env`, `uv run aurora reset`, `uv run aurora serve`.

Reinícios comuns reutilizam os bancos. Antes de futuras mudanças de esquema, copiar ambos os bancos com a API parada e manter migrações versionadas. Durante o desenvolvimento, a restauração é explícita e destrutiva para sessões e dados operacionais, não um procedimento de rollback que preserve o trabalho dos moradores. Nesta etapa de proposta, somente os artefatos OpenSpec são adicionados.

## Open Questions

- Qual versão exata ADK 2.x >= 2.2.0 passa pela prova de confirmação persistida, com qual topologia e configuração de retomada? Resolver na primeira etapa e registrar neste desenho.
- Qual modelo Gemini está disponível e tem cota suficiente no projeto usado para validar? Resolver na implementação pela documentação oficial e pelo Google AI Studio; manter configuração por ambiente.

Esses pontos têm tarefas de descoberta explícitas e não bloqueiam a elaboração da proposta. FastAPI, SQLite, três especialistas, restauração com limpeza de sessões e comportamento das mensagens pendentes são decisões propostas, não fatos sobre uma aplicação já existente.

## Decisão validada na implementação — 2026-10-13

Prova persistida aprovada com google-adk[db]==2.2.0, SQLAlchemy com extra
asyncio, DatabaseSessionService (sqlite+aiosqlite), sub_agents e transferências
padrão, ResumabilityConfig(is_resumable=True) e Runner.run_async com
invocation_id original. Aprovação e negação funcionaram nos dois especialistas
em processos separados; mudança de reservas para visitantes preservou a sessão.
Evidências e limites em `docs/prova-adk.md`. Modelo padrão escolhido:
`gemini-3.5-flash-lite`, configurável por GEMINI_MODEL. Projeto Free informado
pelo usuário; limites numéricos ainda não consultados no painel autenticado.
