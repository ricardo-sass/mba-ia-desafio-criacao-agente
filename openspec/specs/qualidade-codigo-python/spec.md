## ADDED Requirements

### Requirement: O projeto SHALL declarar ferramentas de qualidade reproduzíveis

O projeto SHALL declarar Ruff e mypy como dependências de desenvolvimento gerenciadas por `uv`, com versões resolvidas no `uv.lock` e configuração versionada no `pyproject.toml`.

#### Scenario: Instalação limpa disponibiliza as ferramentas
- **WHEN** uma pessoa executa `uv sync` a partir de um clone limpo
- **THEN** os comandos `uv run ruff --version` e `uv run mypy --version` executam sem depender de instalação global

### Requirement: Ruff SHALL verificar e formatar o código do pacote

Ruff SHALL oferecer uma verificação de lint e uma verificação de formatação para os arquivos Python em `src/aurora`, usando regras compatíveis com PEP 8 e sem ignorar globalmente os achados.

#### Scenario: Lint sem violações
- **WHEN** a implementação concluída executa `uv run ruff check src`
- **THEN** o comando termina com código zero

#### Scenario: Formatação sem diferenças
- **WHEN** a implementação concluída executa `uv run ruff format --check src`
- **THEN** o comando termina com código zero e não indica arquivos que precisem de formatação

### Requirement: mypy SHALL verificar tipos do pacote sem ocultar erros

mypy SHALL analisar `src/aurora` com uma configuração compatível com Python 3.12 e SHALL retornar código diferente de zero para incompatibilidades de tipos não resolvidas; exclusões e silenciamentos, quando inevitáveis em fronteiras externas, SHALL ser específicos e justificáveis.

#### Scenario: Checagem estática aprovada
- **WHEN** a implementação concluída executa `uv run mypy src/aurora`
- **THEN** o comando termina com código zero sem habilitar uma exclusão global de erros

### Requirement: A documentação SHALL orientar a validação de qualidade

O README SHALL documentar a instalação com `uv` e os comandos de Ruff e mypy que devem ser executados antes da entrega, deixando claro que essa validação complementa a validação manual funcional existente.

#### Scenario: Colaborador encontra os comandos
- **WHEN** uma pessoa consulta a seção de desenvolvimento ou execução do README
- **THEN** encontra comandos executáveis para lint, formatação e tipagem, além da ordem recomendada de uso

### Requirement: A adoção das ferramentas SHALL preservar o comportamento funcional

As alterações necessárias para satisfazer as verificações SHALL preservar o contrato da API, os arquivos iniciais e as garantias de confirmação, isolamento, persistência, regulamento e concorrência.

#### Scenario: Fluxo funcional continua validável
- **WHEN** a validação manual existente é executada após as correções de qualidade
- **THEN** as rotas e os fluxos de negócio continuam atendendo ao README, sem modificar os dados iniciais versionados
