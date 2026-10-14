## 1. Configuração das ferramentas

- [x] 1.1 Adicionar Ruff e mypy como dependências de desenvolvimento no `pyproject.toml`, mantendo Python >= 3.12 e a resolução gerenciada por `uv`.
- [x] 1.2 Configurar no `pyproject.toml` o lint e o format do Ruff para `src/aurora`, com regras PEP 8 aplicáveis e sem exclusão global de achados.
- [x] 1.3 Configurar o mypy para analisar `src/aurora`, declarar a versão Python compatível e manter erros reais visíveis, documentando exceções pontuais quando necessárias.
- [x] 1.4 Executar `uv lock` ou equivalente e revisar o `uv.lock` para garantir que as ferramentas estejam reproduzíveis em instalação limpa.

## 2. Adequação do código

- [x] 2.1 Executar `uv run ruff check src` e corrigir imports, erros de lint e demais achados sem alterar contratos ou regras de negócio.
- [x] 2.2 Executar `uv run ruff format src` e revisar o diff para limitar mudanças de formatação ao código Python necessário.
- [x] 2.3 Executar `uv run mypy src/aurora`, adicionar anotações e ajustar incompatibilidades de tipos nas camadas de API, agentes, tools, persistência e schemas.
- [x] 2.4 Revisar cada eventual `# type: ignore` ou regra desabilitada para garantir escopo mínimo, código de erro e justificativa relacionada a dependência externa.

## 3. Documentação e validação

- [x] 3.1 Documentar no README a instalação com `uv` e os comandos de format check, lint e tipagem na ordem recomendada.
- [x] 3.2 Confirmar que a documentação continua descrevendo a arquitetura, as cinco garantias, o contrato da API e os comandos de execução e restauração sem alterações indevidas.
- [x] 3.3 Validar em clone ou ambiente limpo com `uv sync`, `uv run ruff check src`, `uv run ruff format --check src` e `uv run mypy src/aurora`.
- [x] 3.4 Reexecutar a validação manual pertinente do README, incluindo subida/restauração, isolamento, confirmação, consulta do regulamento, reinício com continuidade da sessão e disputa concorrente, confirmando que dados iniciais e contrato permanecem intactos.
