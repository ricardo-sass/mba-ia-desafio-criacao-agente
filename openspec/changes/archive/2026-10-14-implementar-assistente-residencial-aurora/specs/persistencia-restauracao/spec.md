## ADDED Requirements

### Requirement: Reinício preserva dados e conversas
O sistema MUST persistir sessões, vínculo com apartamento, eventos completos, reservas, cancelamentos, visitantes, decisões e confirmações. Subir a API MUST NOT restaurar automaticamente as sementes sobre dados existentes.

#### Scenario: Continuidade da sessão S1
- **WHEN** o avaliador anota a quantidade de eventos, para a API e sobe novamente sem restaurar
- **THEN** a mesma sessão retorna os mesmos eventos e quantidade; uma nova mensagem recebe `200` e aumenta a quantidade de eventos

#### Scenario: Efeitos mantidos
- **WHEN** a API reinicia depois do fluxo de reserva/cancelamento/visita
- **THEN** o 101 mantém quadra em `2030-04-06`, salão em `2030-04-20` e Joana Ribeiro em `2030-04-21`, não tem `RSV-1377` ativa e o 302 mantém `RSV-4821`

### Requirement: Pendências e decisões continuam após reinício
Pendências MUST continuar respondíveis após reinício, com os mesmos IDs, argumentos e sessão. Decisões aceitas sem conclusão MUST ser reconciliadas sem repetir efeitos já persistidos.

#### Scenario: Aprovação após reinício
- **WHEN** a API reinicia com uma reserva paga ou autorização de visitante pendente e depois recebe aprovação do ID original
- **THEN** o Runner retoma o especialista correspondente, executa uma vez e o reenvio recebe `409`

#### Scenario: Negação após reinício
- **WHEN** a API reinicia com uma pendência e depois recebe negação
- **THEN** a pendência é concluída sem criar reserva ou autorização

#### Scenario: Interrupção após decisão aceita
- **WHEN** existe decisão persistida sem resultado final ao iniciar o runtime
- **THEN** a reconciliação retoma a operação original e usa seu registro idempotente para evitar duplicação

### Requirement: Restauração explícita preserva arquivos iniciais
O comando `uv run aurora reset` MUST repor reservas e visitantes das sementes com a API parada, limpar sessões/eventos/pendências e conservar o registro de códigos emitidos. Todos os cinco arquivos de `dados/` MUST permanecer byte a byte inalterados.

#### Scenario: Restaurar depois de alterações
- **WHEN** o operador executa o comando de restauração após criar reservas e visitas
- **THEN** as rotas de verificação voltam às sementes, antigas sessões recebem `404` e os hashes dos arquivos de `dados/` permanecem iguais

#### Scenario: Restauração repetida
- **WHEN** o comando é executado duas vezes seguidas
- **THEN** o estado visível de reservas e visitantes é igual ao estado inicial em ambas as execuções

### Requirement: Instalação e documentação reproduzíveis
O projeto MUST usar Python >= 3.12 e uv com `pyproject.toml` e `uv.lock` versionados, ADK 2.x >= 2.2.0 fixado exatamente e Gemini configurável por ambiente. `.env` e chaves MUST NOT ser versionados. `.env.example` MUST listar variáveis sem valores. O README final MUST conter Arquitetura, Garantias e Como rodar, com referências a código existente e comandos completos, preservando o enunciado em documentação.

#### Scenario: Clone limpo
- **WHEN** o avaliador copia `.env.example`, configura sua chave, executa `uv sync`, restaura e sobe pelos comandos documentados
- **THEN** a API responde em `http://localhost:8000` com as sementes e sem exigir serviço externo de banco

#### Scenario: Inspeção da entrega
- **WHEN** o avaliador inspeciona o repositório final
- **THEN** encontra versão exata do ADK, lock, documentação das cinco garantias com arquivos/funções existentes, dados preservados e nenhum segredo versionado
