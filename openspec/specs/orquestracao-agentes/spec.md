# Orquestração de agentes

## Purpose

Definir a divisão de responsabilidades entre o agente principal, especialistas ADK, tools, Runner e o armazenamento persistente.

## Requirements

### Requirement: Principal distribui trabalho a especialistas ADK
O sistema MUST utilizar um agente principal Google ADK e especialistas de reservas, visitantes e regulamento, todos com Gemini. O principal MUST distribuir as intenções aos especialistas, e o README MUST explicar suas responsabilidades e acionamento.

#### Scenario: Mudança de assunto na mesma sessão
- **WHEN** um morador trata de reservas, depois visitantes e depois regulamento
- **THEN** os especialistas correspondentes são acionados na mesma sessão e o histórico permite inspecionar sua atuação

### Requirement: Dados reais acessados por tools
Leituras e alterações de reservas e visitantes na conversa MUST ocorrer por tools que consultam o armazenamento, sem tratar memória do modelo como fonte de dados. O runtime MUST integrar App e Runner à API assíncrona e ao serviço persistente de sessões.

#### Scenario: Consulta após reinício
- **WHEN** o morador pergunta suas reservas após reiniciar a API
- **THEN** a resposta é baseada em consulta registrada em evento de tool e corresponde às reservas ativas no armazenamento

### Requirement: Compatibilidade de retomada comprovada
A configuração final de agentes, Runner, App e serviço de sessão MUST demonstrar retomada de confirmação no especialista solicitante com armazenamento persistente, inclusive depois de reinício. A versão exata ADK 2.x >= 2.2.0 MUST constar em `pyproject.toml` e `uv.lock`.

#### Scenario: Especialista continua após confirmação
- **WHEN** a API reinicia com uma confirmação pendente gerada pelo especialista de reservas e depois recebe aprovação válida
- **THEN** o Runner entrega a decisão à execução correspondente, a operação produz resultado verificável e a configuração usada fica documentada
