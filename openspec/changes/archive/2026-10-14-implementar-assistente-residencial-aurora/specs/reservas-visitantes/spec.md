## ADDED Requirements

### Requirement: Operações usam dados persistidos e validados
Tools MUST listar áreas, consultar disponibilidade, listar reservas próprias, reservar, cancelar reservas próprias, listar visitantes próprios e solicitar autorização de visitantes usando armazenamento real. O sistema MUST validar área e data, registrar nome/data de visitantes e obter taxas do cadastro. Datas passadas, horários, capacidade e antecedência MUST NOT acrescentar restrições à reserva neste escopo.

#### Scenario: Reserva gratuita
- **WHEN** o 101 reserva quadra disponível em `2030-04-06`
- **THEN** a reserva aparece com código gerado pelo sistema e não há confirmação

#### Scenario: Área com taxa
- **WHEN** um morador pede salão ou churrasqueira em data disponível
- **THEN** a exigência de confirmação e a taxa exibida correspondem ao cadastro, independentemente da taxa alegada na mensagem

### Requirement: Cancelamento conserva histórico de códigos
Cancelar reserva própria MUST retirar sua condição ativa sem exigir confirmação e MUST conservar seu código como já utilizado. Uma data liberada MUST poder ser reservada novamente.

#### Scenario: Reutilizar data sem reutilizar código
- **WHEN** a reserva `RSV-1377` é cancelada e a quadra na mesma data é reservada novamente
- **THEN** a nova reserva tem código diferente e existe no máximo uma reserva ativa nessa área/data

### Requirement: Códigos de reserva nunca se repetem
O sistema MUST gerar códigos únicos para novas reservas e impor sua unicidade em armazenamento, incluindo códigos das sementes e de reservas canceladas. Reinícios e restaurações MUST preservar o registro de códigos novos já emitidos.

#### Scenario: Novas reservas após cancelamento e reinício
- **WHEN** o fluxo cria quadra em `2030-04-06` e salão em `2030-04-20`, após cancelar `RSV-1377`, e a API reinicia
- **THEN** os códigos persistem, são distintos entre si e diferentes de `RSV-1377`, `RSV-4821` e `RSV-2950`

### Requirement: Exclusividade de área e data no instante da gravação
O armazenamento MUST impedir mais de uma reserva ativa para cada par área/data por restrição transacional. Pendências MUST NOT ocupar a agenda. Conflito de reserva MUST produzir resposta normal sem expor o proprietário da reserva vencedora.

#### Scenario: Duas aprovações simultâneas
- **WHEN** sessões do 101 e 201 solicitam salão em `2030-05-11`, ambas recebem pendência e as duas aprovações são enviadas simultaneamente
- **THEN** ambas retornam `200`, as consultas dos dois apartamentos somam exatamente uma reserva ativa nessa área/data e a outra operação é recusada por indisponibilidade

#### Scenario: Disputa em área gratuita
- **WHEN** duas sessões tentam reservar simultaneamente a mesma quadra/data disponível
- **THEN** apenas uma reserva é gravada, nenhuma confirmação é gerada e a outra tentativa recebe recusa normal

#### Scenario: Consulta prévia ficou desatualizada
- **WHEN** a área estava livre na consulta, mas outra transação a reservou antes da gravação
- **THEN** a restrição do banco impede a segunda reserva e o serviço retorna indisponibilidade sem erro de servidor
