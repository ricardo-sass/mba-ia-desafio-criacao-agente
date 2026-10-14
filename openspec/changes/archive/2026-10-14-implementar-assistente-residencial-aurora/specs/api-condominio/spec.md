## ADDED Requirements

### Requirement: Criação de sessão pelo contrato público
O sistema MUST disponibilizar `POST /sessoes` com JSON `{apartamento}` e retornar `201` com `{session_id}` para apartamento cadastrado. Apartamento desconhecido MUST receber `404`.

#### Scenario: Sessão do apartamento 101
- **WHEN** o cliente envia `{"apartamento":"101"}`
- **THEN** recebe `201` e um identificador utilizável nas rotas de sessão

#### Scenario: Apartamento desconhecido
- **WHEN** o cliente tenta criar sessão de um apartamento ausente das sementes
- **THEN** recebe `404` sem criar sessão

### Requirement: Envelope de mensagens e confirmações
O sistema MUST aceitar `{texto}` em `POST /sessoes/{session_id}/mensagens` e `{id, confirmado}` em `POST /sessoes/{session_id}/confirmacoes`. Respostas bem-sucedidas MUST usar `200` e `{resposta, confirmacoes_pendentes}`, com string em `resposta` e lista completa das pendências da sessão em `confirmacoes_pendentes`. Cada pendência MUST conter `id`, `acao` e `detalhes`. ID não pendente MUST receber `409`.

#### Scenario: Execução pausada
- **WHEN** uma operação para aguardando confirmação
- **THEN** a resposta contém todas as pendências persistidas, com detalhes de área/data ou nome/data, e admite `resposta` vazia

#### Scenario: Ausência de pendências
- **WHEN** o turno termina sem confirmação pendente
- **THEN** o envelope contém `confirmacoes_pendentes: []`

#### Scenario: Booleano inválido
- **WHEN** `confirmado` recebe uma string ou outro valor que não seja booleano JSON
- **THEN** a API responde `422` sem decidir nem executar a operação

### Requirement: Sessão inexistente tem precedência
Todas as rotas com `{session_id}` MUST retornar `404` para sessão inexistente antes de executar agentes ou consultar uma confirmação.

#### Scenario: Rotas de uma sessão desconhecida
- **WHEN** o cliente chama mensagens, confirmações ou eventos com uma sessão inexistente
- **THEN** cada rota retorna `404`, inclusive quando o ID da confirmação também é inválido

### Requirement: Histórico completo em ordem
`GET /sessoes/{session_id}/eventos` MUST devolver `200` com a lista completa dos eventos persistidos em ordem, incluindo conteúdo integral, chamadas e respostas de tools e eventos de confirmação.

#### Scenario: Inspeção após operações
- **WHEN** o avaliador consulta eventos após reservar, cancelar e consultar o regulamento
- **THEN** encontra os eventos dessas interações e respectivas tools, sem substituição por resumos

### Requirement: Consultas diretas de verificação
`GET /apartamentos/{apartamento}/reservas` MUST devolver apenas reservas ativas como `[{codigo, area, data}]` e `GET /apartamentos/{apartamento}/visitantes` MUST devolver `[{nome, data}]`, com `200`, datas `AAAA-MM-DD` e acesso direto ao armazenamento sem modelo. Apartamento desconhecido MUST receber `404`.

#### Scenario: Dados iniciais
- **WHEN** os dados foram restaurados e o avaliador consulta reservas do 101 e visitantes do 302
- **THEN** encontra `RSV-1377` na quadra em `2030-03-09` e Marina Duarte em `2030-03-16`, respectivamente

#### Scenario: Consulta independente do Gemini
- **WHEN** não há acesso ao modelo e o avaliador consulta os dados de um apartamento existente
- **THEN** as rotas de verificação continuam retornando os dados persistidos
