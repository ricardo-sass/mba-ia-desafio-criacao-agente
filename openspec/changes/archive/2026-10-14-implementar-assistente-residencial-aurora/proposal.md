## Why

O Residencial Aurora precisa de um assistente que execute operações reais sem permitir que mensagens do morador contornem as regras do condomínio. O repositório contém somente o enunciado e os dados iniciais; esta mudança propõe a implementação completa da API e dos agentes, com as cinco garantias impostas pelo código.

## What Changes

- Criar uma API Python em `http://localhost:8000`, com o contrato de sessões, mensagens, confirmações, eventos e consultas de verificação definido no README.
- Implementar um agente principal Google ADK e especialistas em reservas, visitantes e regulamento, com acesso a dados por tools.
- Exigir confirmação pela API para reservas com taxa e autorizações de visitantes; impedir execução por consentimento escrito no chat e por reenvio de confirmação.
- Vincular cada sessão a um apartamento imutável, restringindo consultas e alterações antes que resultados sejam entregues ao modelo ou registrados nos eventos.
- Persistir sessões, eventos e operações; manter códigos de reservas únicos mesmo após cancelamento e impedir reservas simultâneas da mesma área/data na gravação.
- Consultar somente os trechos pertinentes do regulamento, preservando os arquivos originais de `dados/`.
- Disponibilizar comandos de restauração e subida, configuração sem segredos versionados e documentação final das garantias e da arquitetura.
- Validar manualmente os 15 passos do avaliador, além da retomada de confirmação pendente após reinício.

Obrigatórios: Python >= 3.12, uv com lock versionado, Google ADK 2.x >= 2.2.0 fixado em versão exata, Gemini com chave do Google AI Studio, pelo menos dois especialistas, todas as rotas e as cinco garantias. Escolhas desta proposta: FastAPI, SQLite local e três especialistas. A versão exata do ADK, o modelo Gemini e os parâmetros de retomada serão fechados na etapa inicial de compatibilidade, com documentação e execução reais.

Fora de escopo: interface visual, autenticação real, pagamento/estorno, regras de antecedência, datas passadas, horários/capacidade, testes automatizados, evals e deploy. Preparar a entrega em fork público na branch `main` faz parte do resultado final do projeto; esta mudança não executa publicação durante a elaboração da proposta.

## Capabilities

### New Capabilities

- `api-condominio`: contrato HTTP completo e consultas de verificação sem uso do modelo.
- `orquestracao-agentes`: agente principal, três especialistas e execução assíncrona via App e Runner.
- `confirmacoes-seguras`: pendências persistidas e confirmação exclusiva pela API, com retomada e execução única.
- `isolamento-apartamento`: identidade imutável da sessão e acesso aos dados limitado ao próprio apartamento.
- `reservas-visitantes`: operações sobre dados reais, cancelamento próprio, códigos únicos e exclusividade de área/data.
- `persistencia-restauracao`: continuidade após reinício, dados iniciais imutáveis e restauração explícita.
- `consulta-regulamento`: recuperação seletiva de conteúdo relevante, sem carregar o documento inteiro na conversa.

### Modified Capabilities

Nenhuma. Não existem especificações anteriores nem aplicação implementada.

## Impact

Todas as cinco garantias do README são cobertas: confirmação (`confirmacoes-seguras`), isolamento (`isolamento-apartamento`), persistência (`persistencia-restauracao`), contexto seletivo (`consulta-regulamento`) e concorrência (`reservas-visitantes`).

Rotas novas: `POST /sessoes`, `POST /sessoes/{session_id}/mensagens`, `POST /sessoes/{session_id}/confirmacoes`, `GET /sessoes/{session_id}/eventos`, `GET /apartamentos/{apartamento}/reservas` e `GET /apartamentos/{apartamento}/visitantes`.

Serão criados o pacote da aplicação, `pyproject.toml`, `uv.lock`, `.env.example`, armazenamento local ignorado pelo Git e instruções operacionais. As dependências previstas incluem Google ADK, FastAPI, Uvicorn e suporte assíncrono a SQLite. A única integração externa necessária em execução será a API Gemini; nenhum serviço de banco em container será exigido. O README atual será preservado como enunciado em documentação antes de sua substituição pelo README de entrega. Nenhum arquivo de `dados/` será alterado.
