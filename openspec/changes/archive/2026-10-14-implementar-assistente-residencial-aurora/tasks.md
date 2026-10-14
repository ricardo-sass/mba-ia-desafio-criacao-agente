## 1. Preparação e prova de compatibilidade

- [x] 1.1 Preservar o README original em `docs/enunciado.md` e registrar hashes dos cinco arquivos de `dados/` para comparação na entrega.
- [x] 1.2 Criar o pacote `src/aurora`, `pyproject.toml` com Python >= 3.12 e uv; selecionar uma versão candidata exata ADK 2.x >= 2.2.0 e instalar dependências para a prova.
- [x] 1.3 Consultar modelos Gemini na documentação oficial e limites do projeto Google AI Studio; definir um modelo configurável, criar `.env.example` sem valores e ignorar segredos/arquivos de execução no Git.
- [x] 1.4 Montar prova mínima com principal, especialistas de reservas e visitantes, App, Runner, serviço de sessão persistente SQLite e confirmação de tool correlacionada por sessão/chamada/invocação.
- [x] 1.5 Executar manualmente aprovação e negação no especialista correto, troca de assunto e retomada após reinício; verificar efeito e eventos, registrando versão ADK, topologia, transferências e configuração de retomada que passaram.
- [x] 1.6 Resolver eventuais incompatibilidades de persistência/retomada antes de prosseguir; atualizar `design.md`, fixar a versão exata validada e gerar `uv.lock`. A etapa 2 depende da conclusão desta prova.

## 2. Armazenamento e restauração

- [x] 2.1 Implementar esquema de domínio com apartamentos, áreas, reservas, visitantes, vínculos de sessão, confirmações, operações e catálogo histórico de códigos; armazenar taxas em centavos e dados operacionais fora de `dados/`.
- [x] 2.2 Criar índice único parcial de reservas ativas por área/data e restrições de códigos/identificadores de operações; configurar chaves estrangeiras, WAL, espera de lock e transações curtas.
- [x] 2.3 Implementar carga inicial e `uv run aurora reset`, repondo reservas/visitantes, limpando sessões/eventos/pendências e preservando códigos emitidos; verificar duas restaurações consecutivas com a API parada.
- [x] 2.4 Implementar geração e registro transacional de códigos, cancelamento por status e leitura apenas de reservas ativas; verificar que código cancelado não pode ser reutilizado.
- [x] 2.5 Configurar o serviço persistente ADK validado na etapa 1 e nomes/identidades estáveis; verificar que subir novamente não apaga nem recarrega dados existentes.

## 3. Identidade e serviços de domínio

- [x] 3.1 Criar o vínculo imutável sessão/apartamento e resolver identidade pelo contexto confiável, conferindo state contra vínculo persistido; impedir atualização da identidade por tools.
- [x] 3.2 Implementar consultas próprias e cancelamento por código ou área/data com filtro de apartamento no armazenamento; retornar ausência genérica para reserva fora desse escopo.
- [x] 3.3 Implementar disponibilidade expondo somente área/data e livre/ocupada; verificar que o resultado nunca contém proprietário ou código alheio.
- [x] 3.4 Implementar serviço único de gravação de reservas para área gratuita e área paga aprovada, tratando conflito do índice como indisponibilidade e repetindo apenas contenção transitória de forma limitada.
- [x] 3.5 Implementar listagem e gravação de visitantes do apartamento da sessão, com nome/data validados e proteção contra repetição da mesma operação.

## 4. Confirmações e execução idempotente

- [x] 4.1 Implementar registro persistente de pendências com argumentos imutáveis e correlação entre ID público, sessão, invocação, agente, chamada original e chamada ADK de confirmação.
- [x] 4.2 Implementar decisão de exigir confirmação a partir da taxa cadastrada ou autorização de visitante; verificar ausência de efeitos antes de aprovação e ausência de pendência para quadra/cancelamento próprio.
- [x] 4.3 Implementar consumo condicional da pendência e registro da decisão; devolver `409` para ID inexistente, alheio ou respondido antes de qualquer retomada.
- [x] 4.4 Adaptar a decisão HTTP para `FunctionResponse` de confirmação, retomando via Runner a execução original com os parâmetros validados na prova; recusar divergência de argumentos ou correlação.
- [x] 4.5 Gravar efeito e resultado idempotente na mesma transação, finalizar negações sem efeito e devolver o resultado persistido em reexecuções internas; verificar que a resposta HTTP reflete esse resultado.
- [x] 4.6 Implementar reconciliação de decisões aceitas sem resultado após interrupção e validar manualmente que a retomada não repete efeitos.
- [x] 4.7 Implementar projeção de todas as pendências da sessão e resposta `200` de orientação para mensagens durante pendências, sem converter texto em consentimento; verificar tratamento independente de múltiplos IDs.

## 5. Regulamento e agentes completos

- [x] 5.1 Implementar índice local do regulamento por assunto/capítulo/artigo, seleção por termos/sinônimos e retorno com referência, sem inserir o documento integral no contexto.
- [x] 5.2 Implementar tool de consulta seletiva com esclarecimento para ambiguidade, ausência de informação quando aplicável e recusa de carregar o documento inteiro; conferir recuperação do artigo 22 para piscina aos domingos.
- [x] 5.3 Conectar tools de reservas e visitantes aos serviços das etapas 3 e 4, sem argumentos livres de apartamento, taxa ou aprovação.
- [x] 5.4 Concluir o principal e os três especialistas com a topologia validada; confirmar troca de assunto na mesma sessão e ausência de regulamento nas instruções do principal.
- [x] 5.5 Integrar consumo dos eventos do Runner, composição da resposta e serialização completa do histórico, preservando chamadas/resultados de tools e sem compactação destrutiva.

## 6. Contrato HTTP e comandos

- [x] 6.1 Implementar `POST /sessoes` com `201`, validação de apartamento e registro persistente da sessão/vínculo.
- [x] 6.2 Implementar rotas de mensagens e confirmações com envelopes exatos, `404` para sessão ausente, `409` para confirmação inválida, booleano estrito e serialização por sessão sem bloquear outras sessões.
- [x] 6.3 Implementar `GET /sessoes/{session_id}/eventos` com todos os eventos em ordem e conteúdo completo.
- [x] 6.4 Implementar consultas diretas de reservas/visitantes por apartamento com formatos do enunciado, datas ISO e independência do modelo.
- [x] 6.5 Implementar `uv run aurora serve` em `http://localhost:8000`, carregamento de ambiente com padrões documentados, criação de diretórios e encerramento dos recursos persistentes.

## 7. Validação manual de aceite

- [x] 7.1 Criar `docs/validacao-manual.md` com comandos e resultados esperados dos 15 passos do avaliador; executar instalação, restauração, subida e criação de S1 em ambiente limpo (passos 1–2).
- [x] 7.2 Executar tentativas de consulta/cancelamento do 302 em S1, cancelamento próprio e reserva gratuita; conferir dados e eventos, incluindo ausência de `RSV-4821`/Marina Duarte e ausência de confirmações indevidas (passos 3–6).
- [x] 7.3 Executar negação, nova aprovação, reenvio sequencial, ID inexistente e sessão inexistente; conferir `200`, `409`, `404` e unicidade do efeito (passos 7–9).
- [x] 7.4 Executar tentativa em data ocupada e autorização de Joana Ribeiro com consentimento escrito no chat; conferir privacidade e ausência de efeito até a rota de confirmação (passos 10–11).
- [x] 7.5 Consultar piscina aos domingos; conferir resposta às 20h, chamadas de tools no histórico e ausência de trechos de capítulos irrelevantes em todos os eventos (passo 12).
- [x] 7.6 Anotar eventos, parar e subir sem restaurar; conferir quantidade preservada, continuidade de S1, dados esperados e códigos distintos das sementes (passo 13).
- [x] 7.7 Criar S3/S4 do 101/201, gerar as duas pendências para salão em `2030-05-11` e aprovar simultaneamente; conferir dois HTTP `200`, uma única reserva total e resultado normal para a perdedora (passo 14).
- [x] 7.8 Validar casos complementares: ID de outra sessão do mesmo apartamento, negação de visitante, aprovação e negação após reinício com pendência, tentativa de alterar argumentos aprovados e concorrência em área gratuita.
- [x] 7.9 Revisar versão exata ADK, lock, ausência de segredos versionados, hashes dos dados, agentes, escopo de tools, índice transacional e referências documentais, registrando evidências e corrigindo divergências (passo 15).

## 8. Documentação e preparação da entrega

- [x] 8.1 Substituir o README pelas seções Arquitetura, Garantias e Como rodar, preservando `docs/enunciado.md`; explicar agentes, acionamento, escolhas e a configuração de confirmação persistida comprovada.
- [x] 8.2 Documentar cada garantia com links para arquivos e funções reais; incluir variáveis, modelo validado, pré-requisitos, `uv sync`, subida, restauração e seu efeito sobre sessões.
- [x] 8.3 Reexecutar os comandos do README em ambiente limpo se ajustes finais os afetarem, conferir que os artefatos necessários estão prontos para versionamento e registrar o estado da validação manual.
- [x] 8.4 Preparar o entregável para publicação via PR na branch `main`, sem incluir bancos, `.env` ou segredos.
