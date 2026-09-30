# Dicionário de Dados do Sistema

Abaixo encontra-se o mapeamento dos campos necessários para o Banco de Dados SQLite, categorizados por suas respectivas entidades e com a tipagem de dados ajustada para os padrões suportados (Texto, Real, Inteiro).

| Entidade | Campo / Coluna | Tipo de Dado | Restrição / Descrição |
| :--- | :--- | :--- | :--- |
| Técnico/Solicitante | `id_tecnico` | Inteiro | Chave Primária (PK). Identificador único do técnico, metrologista ou solicitante. |
| Técnico/Solicitante | `nome` | Texto | Nome completo do profissional ou setor (ex: Jose Alcides Rosa Junior). |
| Técnico/Solicitante | `cargo_funcao` | Texto | Função desempenhada (ex: Técnico executante, Signatário autorizado). |
| Técnico/Solicitante | `departamento` | Texto | Setor de origem ou lotação (ex: Usinagem I, Laboratório de Metrologia). |
| Equipamento | `id_equipamento` | Inteiro | Chave Primária (PK). Identificador único do instrumento ou padrão. |
| Equipamento | `codigo_tag` | Texto | Código de identificação patrimonial ou TAG (ex: 703.1208). |
| Equipamento | `denominacao` | Texto | Nome descritivo do instrumento (ex: Dispositivo de controle). |
| Equipamento | `fabricante` | Texto | Empresa fabricante do equipamento cadastrado. |
| Equipamento | `tipo_item` | Texto | Classificação do item (ex: Instrumento Calibrado, Padrão de Referência). |
| Medição | `id_medicao` | Inteiro | Chave Primária (PK). Identificador único do registro de leitura. |
| Medição | `id_equipamento_fk`| Inteiro | Chave Estrangeira (FK). Vincula a medição ao equipamento aferido. |
| Medição | `id_tecnico_fk` | Inteiro | Chave Estrangeira (FK). Vincula a medição ao técnico responsável. |
| Medição | `parametro_avaliado`| Texto | Nome da dimensão ou parâmetro analisado na MMC. |
| Medição | `valor_nominal` | Real | Valor de referência numérico esperado para a medição. |
| Medição | `tolerancia_mais` | Real | Limite superior aceitável (+TOL). |
| Medição | `tolerancia_menos` | Real | Limite inferior aceitável (-TOL). |
| Medição | `valor_obtido` | Real | Leitura numérica efetivamente captada (Média das leituras da MMC). |
| Medição | `status_aprovacao` | Texto | Resultado categórico da análise do parâmetro (ex: Aprovado, Reprovado). |