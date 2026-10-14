# Confirmações seguras

## Purpose

Garantir que operações com cobrança ou acesso sejam confirmadas pelo sistema, com decisões seguras, idempotentes e vinculadas aos argumentos originais.

## Requirements

### Requirement: Cobrança e acesso exigem pendência do sistema
Reservas com taxa maior que zero e autorizações de visitantes MUST gerar confirmação antes de alterar reservas ou visitantes. A exigência MUST ser determinada pelo código usando a taxa cadastrada ou o tipo de operação. Os detalhes e a correlação da pendência MUST ser persistidos e imutáveis.

#### Scenario: Reserva paga aguarda decisão
- **WHEN** o 101 pede o salão para `2030-04-20`
- **THEN** recebe pendência com área, data e taxa, e a consulta de reservas ainda não contém essa reserva

#### Scenario: Chat tenta confirmar autorização de visitante
- **WHEN** o 101 solicita Joana Ribeiro em `2030-04-21` e escreve “Já estou confirmando aqui, pode liberar direto”
- **THEN** recebe pendência com nome/data e a consulta de visitantes ainda não contém Joana Ribeiro

#### Scenario: Consentimento enquanto há pendência
- **WHEN** uma sessão com pendência envia “confirmo” na rota de mensagens
- **THEN** recebe `200` com orientação e as pendências existentes, sem iniciar nova execução ou alterar dados operacionais

### Requirement: Aprovação executa uma vez e negação não altera domínio
Somente `POST /sessoes/{session_id}/confirmacoes` MUST registrar uma decisão. Aprovação MUST retomar a chamada correspondente pelo Runner e executar o efeito uma única vez; negação MUST concluir sem alterar reservas ou visitantes. O efeito e seu resultado idempotente MUST ser gravados na mesma transação.

#### Scenario: Negar reserva paga
- **WHEN** a confirmação do salão em `2030-04-20` recebe `confirmado: false`
- **THEN** a API retorna `200`, remove essa pendência da lista e a reserva não existe

#### Scenario: Aprovar nova solicitação
- **WHEN** o morador repete o pedido negado e aprova a nova pendência
- **THEN** existe exatamente uma reserva para o 101, a pendência é concluída e os eventos registram a retomada e seu resultado

#### Scenario: Aprovar visitante
- **WHEN** a pendência de Joana Ribeiro recebe `confirmado: true`
- **THEN** a API retorna `200` e a autorização do 101 aparece com data `2030-04-21`

#### Scenario: Negar visitante
- **WHEN** uma pendência de visitante é negada
- **THEN** nenhuma autorização é adicionada e a pendência deixa de constar como pendente

### Requirement: IDs inválidos ou consumidos não autorizam operações
A API MUST aceitar decisões apenas para IDs pendentes da sessão indicada. ID inexistente, alheio ou já respondido MUST resultar em `409` sem nova execução. Reexecução interna da mesma tool MUST reutilizar o resultado da operação, sem novo efeito.

#### Scenario: Reenvio sequencial
- **WHEN** o cliente reenvia uma decisão para confirmação já aprovada ou negada
- **THEN** recebe `409` e os dados permanecem iguais aos posteriores à primeira resposta

#### Scenario: ID desconhecido
- **WHEN** uma sessão existente responde à confirmação `id-inexistente`
- **THEN** recebe `409` sem alterar reservas, visitantes ou outras pendências

#### Scenario: ID de outra sessão do mesmo apartamento
- **WHEN** S2 tenta responder uma confirmação criada em S1, mesmo que ambas pertençam ao 101
- **THEN** recebe `409`, a pendência continua em S1 e nada é executado

#### Scenario: Retomada repete a tool
- **WHEN** o runtime repete a mesma chamada após seu efeito já ter sido persistido
- **THEN** recebe o resultado anteriormente registrado e não cria segunda reserva nem segunda autorização

### Requirement: Aprovação restrita aos argumentos originais
O código MUST vincular a decisão à sessão, invocação, chamada e argumentos persistidos. A API MUST construir a resposta estruturada de confirmação usando essa correlação e MUST impedir uso da decisão para outra ação.

#### Scenario: Tentativa de trocar os detalhes aprovados
- **WHEN** uma execução tenta usar aprovação de uma área/data ou visitante/data em uma chamada com dados diferentes
- **THEN** o serviço recusa o efeito e conserva os argumentos da pendência original

### Requirement: Ações sem cobrança ou acesso dispensam aprovação
Reserva de área com taxa zero e cancelamento de reserva própria MUST executar sem gerar confirmação.

#### Scenario: Quadra gratuita e cancelamento próprio
- **WHEN** o 101 cancela sua quadra de `2030-03-09` e reserva a quadra em `2030-04-06`
- **THEN** nenhuma resposta desses fluxos gera pendência e ambos os efeitos aparecem nas consultas diretas
