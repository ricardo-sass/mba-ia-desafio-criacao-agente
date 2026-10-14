## Why

O projeto Python ainda não declara nem automatiza um padrão único para estilo, erros comuns e tipagem estática. Isso torna a revisão manual inconsistente e aumenta o risco de regressões nas camadas de API, agentes, tools, persistência e schemas; agora é um bom momento para tornar a qualidade verificável antes de novas alterações.

## What Changes

- Adicionar Ruff como ferramenta única para lint e formatação compatíveis com PEP 8, com configuração versionada no `pyproject.toml`.
- Adicionar mypy para verificar tipagem estática do código Python do pacote `aurora`.
- Definir comandos reproduzíveis via `uv` para formatar, validar lint e executar a checagem de tipos.
- Corrigir os achados existentes necessários para que as verificações passem sem ignorar regras de forma ampla.
- Documentar no README os comandos de qualidade e a expectativa de executá-los antes da entrega.
- Não alterar o contrato funcional da API, as cinco garantias do enunciado, os dados iniciais ou o escopo de validação manual.

## Capabilities

### New Capabilities

- `qualidade-codigo-python`: padrão verificável de estilo PEP 8, lint, formatação e tipagem estática para o pacote Python.

### Modified Capabilities

Nenhuma capacidade funcional existente terá requisitos alterados; a mudança é de engenharia e validação estática.

## Impact

- `pyproject.toml`: novas dependências de desenvolvimento e configurações do Ruff e do mypy.
- `uv.lock`: atualização para registrar as ferramentas adicionadas.
- `src/aurora/**/*.py`: ajustes de estilo, imports, tratamento de erros e anotações necessários para satisfazer as verificações.
- `README.md`: documentação dos comandos de qualidade e do fluxo recomendado antes da entrega.
- O pipeline de execução da API e as rotas existentes permanecem funcionalmente inalterados.
- As garantias de confirmação, isolamento, persistência, regulamento e concorrência não são modificadas; a validação deve confirmar que os ajustes estáticos não as degradaram.
