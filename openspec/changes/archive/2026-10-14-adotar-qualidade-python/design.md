## Context

O pacote `aurora` é executado com Python 3.12 ou superior e é gerenciado por `uv`, mas o `pyproject.toml` atualmente não define ferramentas de qualidade. O código cruza API assíncrona, persistência, schemas, tools e integração com o ADK; por isso, estilo e tipos precisam ser verificados de maneira consistente e localmente reproduzível.

## Goals / Non-Goals

**Goals:**

- Centralizar no `pyproject.toml` a configuração do Ruff e do mypy.
- Usar Ruff para lint e formatação PEP 8, cobrindo o pacote `src/aurora`.
- Usar mypy para detectar incompatibilidades de tipos no mesmo pacote.
- Fazer o código atual passar pelas verificações, preservando seu comportamento.
- Documentar comandos executáveis com `uv`.

**Non-Goals:**

- Alterar rotas, payloads, regras de negócio, dados iniciais ou fluxo do Runner.
- Criar testes automatizados, pipeline de CI, evals, deploy ou autenticação real.
- Exigir tipagem estrita de dependências externas que não forneçam stubs; eventuais limites devem ser explícitos e mínimos.

## Decisions

### Configuração no `pyproject.toml`

As configurações de Ruff e mypy ficarão no arquivo já usado pelo empacotamento, evitando arquivos de configuração concorrentes. Ruff será habilitado para lint e format, com regras selecionadas para erros comuns, imports, modernização compatível com Python 3.12 e estilo; o formato será aplicado apenas ao código Python do projeto. Mypy será executado em `src/aurora`, com `python_version = "3.12"` e relatório de erros acionáveis.

Alternativas consideradas: arquivos separados (`ruff.toml` e `mypy.ini`) aumentariam pontos de configuração; usar somente um formatter não detectaria problemas de imports e lógica estática.

### Dependências de desenvolvimento gerenciadas por `uv`

Ruff e mypy serão adicionados como dependências de desenvolvimento e registrados no `uv.lock`. Os comandos documentados serão `uv run ruff format --check src`, `uv run ruff check src` e `uv run mypy src/aurora`, deixando a instalação e a resolução reproduzíveis.

Alternativa considerada: depender de instalações globais, o que faria a validação variar entre máquinas e não refletiria o ambiente do projeto.

### Correções graduais e explícitas

Os achados serão corrigidos no código sempre que possível. Ignorados pontuais deverão conter justificativa e ficar limitados à linha ou regra inevitável, especialmente em fronteiras de bibliotecas externas. Não será adotado `ignore_errors = true` nem exclusão ampla do pacote.

### Preservação do comportamento

Depois das correções estáticas, serão executados os comandos de qualidade e as validações manuais já descritas no README. As cinco garantias do enunciado não são afetadas diretamente: confirmação, isolamento, persistência, regulamento e concorrência continuam impostas pelo código de domínio, armazenamento e API, e não pelo modelo ou pelas ferramentas de lint.

## Risks / Trade-offs

- **[Risco]** Tipagem de bibliotecas do ADK, FastAPI ou SQLAlchemy pode produzir falsos positivos ou erros sem stubs. → **Mitigação:** usar configurações compatíveis com o código atual, tipar as fronteiras locais e restringir qualquer `# type: ignore` com código de erro e justificativa.
- **[Risco]** A formatação pode gerar um diff grande. → **Mitigação:** limitar o escopo a `src/aurora`, revisar o diff e não alterar dados ou documentação fora do necessário.
- **[Risco]** Regras novas podem dificultar contribuições futuras. → **Mitigação:** documentar comandos simples, manter configuração versionada e evitar regras não suportadas pelo Python mínimo do projeto.
- **[Risco]** Ajustes de anotações podem revelar um bug real. → **Mitigação:** tratar cada erro como candidato a correção funcional, validar o fluxo afetado e registrar exceções somente quando o comportamento pretendido estiver correto.

## Migration Plan

1. Adicionar as ferramentas e a configuração no `pyproject.toml`; atualizar `uv.lock`.
2. Executar Ruff e mypy, corrigir os achados no pacote e revisar o diff.
3. Documentar os comandos no README.
4. Validar a instalação limpa com `uv sync`, as verificações e o fluxo manual existente.

Rollback: remover as configurações, dependências e alterações de código desta mudança e regenerar o lockfile; como não há migração de dados nem alteração de contrato, não há rollback operacional especial.

## Open Questions

- A versão exata das ferramentas será resolvida pelo `uv` durante a implementação, respeitando a compatibilidade com Python 3.12 e o lockfile versionado.
- O nível final de rigor do mypy deve ser ajustado após a primeira execução; a decisão obrigatória é manter erros reais visíveis e evitar uma exclusão global.
