# Documentação Técnica do MVP — Parte 1

Projeto Aplicado I — Automação de Certificados de Calibração (Schulz S.A.)
Linguagem utilizada: Python 3, com persistência em SQLite (`sqlite3`).

## 1. Rastreabilidade com o Modelo de Dados (01, 02 e 03)

O MVP implementa o modelo definido em `01_estrutura.md`, `02_dicionario.md` e `03_banco.sql`, sem alterá-lo. O arquivo `03_banco.sql` é a **fonte única** dos nomes de tabelas e colunas: o método `BancoDados.criar_tabelas()` lê e executa esse próprio arquivo, em vez de repetir o `CREATE TABLE` dentro do código Python. Assim, documentação e código não podem divergir.

| Entidade (01) | Tabela (03) | Classe (04) | Campos (02) |
| :--- | :--- | :--- | :--- |
| Técnico/Solicitante | `Tecnico_Solicitante` | `TecnicoSolicitante` | `id_tecnico`, `nome`, `cargo_funcao`, `departamento` |
| Equipamento | `Equipamento` | `Equipamento` | `id_equipamento`, `codigo_tag`, `denominacao`, `fabricante`, `tipo_item` |
| Medição | `Medicao` | `Medicao` | `id_medicao`, `id_equipamento_fk`, `id_tecnico_fk`, `parametro_avaliado`, `valor_nominal`, `tolerancia_mais`, `tolerancia_menos`, `valor_obtido`, `status_aprovacao` |

Cada atributo das classes tem o mesmo nome da coluna correspondente do dicionário de dados. Os campos `NOT NULL` do `03_banco.sql` (por exemplo `cargo_funcao`, `tipo_item`, `parametro_avaliado`) são validados nas classes antes de chegarem ao banco; os campos opcionais (`departamento`, `fabricante`) aceitam `None`.

**Convenção das tolerâncias.** O dicionário define `tolerancia_mais` como limite superior (+TOL) e `tolerancia_menos` como limite inferior (-TOL). O MVP adota a convenção usual de relatórios de MMC: ambas são desvios em relação ao valor nominal, sendo `tolerancia_mais >= 0` e `tolerancia_menos <= 0`. Exemplo: nominal `25.000`, +TOL `0.010`, -TOL `-0.010` → faixa aceitável de `24.990` a `25.010`. Tolerâncias assimétricas são suportadas (ex.: +TOL `0.020` e -TOL `0.000`).

**Status de aprovação.** Segue os valores de exemplo do dicionário: `Aprovado` ou `Reprovado`.

## 2. Padrões de Orientação a Objetos Utilizados

**Encapsulamento com validação.** Todos os atributos das classes de domínio são `@property` com setter que valida o valor antes de armazená-lo: textos obrigatórios não podem ser vazios, valores numéricos precisam ser números finitos, `+TOL` não pode ser negativa e `-TOL` não pode ser positiva. As validações valem também depois da criação do objeto (alterar `tecnico.nome = ""` levanta erro), e não apenas no construtor. Um objeto inválido não chega a existir em memória.

**Separação de responsabilidades.** O módulo divide dois papéis: classes de domínio (`TecnicoSolicitante`, `Equipamento`, `Medicao`), que representam as regras de negócio metrológicas, e uma classe de persistência (`BancoDados`), responsável por abrir a conexão, criar as tabelas e executar o SQL. Nenhuma classe de domínio conhece o SQLite. A regra de aprovação existe em um só lugar, na classe `Medicao`: quando uma medição é atualizada, `BancoDados` apenas carrega o objeto, a classe recalcula o status e o resultado é gravado.

**Validação no construtor (fail-fast).** Os setters são chamados já no `__init__`. Uma tolerância com sinal incorreto, um campo obrigatório vazio ou uma chave estrangeira ausente levantam `ValueError` imediatamente, antes de qualquer acesso ao banco.

**Status calculado, nunca armazenado em separado no objeto.** `Medicao.status_aprovacao` é uma propriedade calculada a partir dos valores atuais (`valor_nominal`, `valor_obtido`, `tolerancia_mais`, `tolerancia_menos`). Por isso o status não fica desatualizado se `valor_obtido` mudar. O valor é gravado na coluna `status_aprovacao` apenas no momento do `INSERT` ou do `UPDATE`.

**Associação por chave, não por composição de objeto.** `Medicao` não guarda referência direta aos objetos `TecnicoSolicitante` e `Equipamento`, apenas seus identificadores (`id_equipamento_fk`, `id_tecnico_fk`). Isso espelha o modelo relacional do `03_banco.sql` e evita acoplamento forte entre as classes em memória.

**Tratamento numérico.** A comparação com a tolerância usa o desvio arredondado a 9 casas decimais. Sem isso, o erro de ponto flutuante do Python (por exemplo, `100.03 - 100 = 0.030000000000001137`) reprovaria uma medição que está exatamente no limite da tolerância.

## 3. Diagrama Textual das Classes (UML Simplificado)

```
+--------------------------------+
|       TecnicoSolicitante       |
+--------------------------------+
| - id_tecnico: int              |
| - nome: str  [validado]        |
| - cargo_funcao: str [validado] |
| - departamento: str (opcional) |
+--------------------------------+
| + __str__(): str               |
+--------------------------------+
              ^
              | 1
              |
              | N
+--------------------------------+        N        1    +----------------------------------+
|            Medicao             |-------------------->|           Equipamento            |
+--------------------------------+                     +----------------------------------+
| - id_medicao: int              |                     | - id_equipamento: int            |
| - id_equipamento_fk: int (FK)  |                     | - codigo_tag: str [validado]     |
| - id_tecnico_fk: int (FK)      |                     | - denominacao: str [validado]    |
| - parametro_avaliado: str      |                     | - tipo_item: str [validado]      |
| - valor_nominal: float         |                     | - fabricante: str (opcional)     |
| - tolerancia_mais: float (+TOL)|                     +----------------------------------+
| - tolerancia_menos: float(-TOL)|                     | + __str__(): str                 |
| - valor_obtido: float          |                     +----------------------------------+
| /status_aprovacao: str         |
+--------------------------------+
| + calcular_desvio(): float     |
| + validar_status(): str        |
+--------------------------------+
   (/ = atributo calculado)

+------------------------------------------------------------+
|                        BancoDados                           |
+------------------------------------------------------------+
| - nome_arquivo: str                                         |
| - conexao: Connection                                       |
+------------------------------------------------------------+
| + conectar() / desconectar()                                |
| + criar_tabelas()          (executa o 03_banco.sql)         |
| + inserir_tecnico(TecnicoSolicitante)                       |
| + inserir_equipamento(Equipamento)                          |
| + inserir_medicao(Medicao)                                  |
| + listar_tecnicos() / listar_equipamentos()                 |
| + buscar_medicao(id): Medicao                               |
| + relatorio_calibracao()   (JOIN das 3 tabelas)             |
| + atualizar_departamento_tecnico(id, novo_departamento)     |
| + atualizar_medicao(id, novo_valor_obtido)                  |
| + deletar_tecnico(id) / deletar_equipamento(id)             |
| + deletar_medicao(id)                                       |
+------------------------------------------------------------+
   ..> depende de TecnicoSolicitante, Equipamento e Medicao
       (persiste e reconstrói esses objetos via SQL)

ErroBanco  <|--  RegistroDuplicadoError     (exceções da camada de persistência)
```

Cardinalidade: um `TecnicoSolicitante` executa N `Medicao`; um `Equipamento` é alvo de N `Medicao`. `BancoDados` não herda nem é herdado por nenhuma classe de domínio — a relação é de dependência (uso), não de hierarquia.

## 4. Tratamento de Erros

O sistema trata erros em duas camadas distintas.

**Camada de domínio (regra de negócio).** `ValueError` com mensagem específica é levantado nos setters e construtores quando um dado viola uma regra, antes de tocar o banco. Exemplos: `O campo 'nome' não pode ser vazio.`, `A tolerância inferior (-TOL) não pode ser positiva (ex.: use -0.010 e não 0.010).`, ou `O campo 'id_equipamento_fk' é obrigatório...` quando se tenta criar uma medição sem equipamento ou técnico salvo.

**Camada de persistência (integridade do banco).** Os métodos de `BancoDados` capturam as exceções do `sqlite3`, desfazem a transação com `rollback()` e levantam exceções próprias, para que o chamador **não possa ignorar a falha** sem querer:
- `RegistroDuplicadoError`: disparada pela restrição `UNIQUE` de `codigo_tag`. Como a TAG é normalizada em maiúsculas, `pad-001` e `PAD-001` são tratadas como o mesmo equipamento.
- `ErroBanco` (classe base): cobre violações de chave estrangeira (medição apontando para equipamento ou técnico inexistente, ou exclusão de um equipamento/técnico que ainda possui medições) e qualquer outra falha do SQLite.

O padrão é o mesmo em todos os casos: ou o `commit()` é confirmado, ou o `rollback()` desfaz tudo, e nunca fica uma transação parcial. A integridade referencial definida em `03_banco.sql` (`FOREIGN KEY ... ON DELETE RESTRICT ON UPDATE CASCADE`) é de fato verificada porque `PRAGMA foreign_keys = ON` é ativado logo na conexão (o SQLite ignora chaves estrangeiras por padrão). Na prática, o banco impede apagar um equipamento ou técnico que já possui medições: `deletar_equipamento` e `deletar_tecnico` capturam essa recusa, desfazem a transação e levantam `ErroBanco` com uma mensagem que explica o vínculo. Excluir um `id` que não existe não é erro: o método apenas retorna `False`.

## 5. Validação do Fluxo Funcional do MVP

O MVP implementa o CRUD completo na classe `BancoDados`:

| Operação | Métodos |
| :--- | :--- |
| Create | `inserir_tecnico`, `inserir_equipamento`, `inserir_medicao` |
| Read | `listar_tecnicos`, `listar_equipamentos`, `buscar_medicao`, `relatorio_calibracao` (JOIN das 3 tabelas) |
| Update | `atualizar_departamento_tecnico`, `atualizar_medicao` (recalcula o status) |
| Delete | `deletar_tecnico`, `deletar_equipamento`, `deletar_medicao` |

O script `05_main.py` demonstra o ciclo completo de uso. Todos os dados são exemplos escritos no próprio script.

1. **Inicialização:** remove o arquivo `schulz_demo.db` (exclusivo da demonstração) e chama `criar_tabelas()`, que executa o `03_banco.sql`. A cada execução o estado inicial é limpo.
2. **Cadastro de técnicos/solicitantes:** três registros, que cobrem os papéis descritos no `01_estrutura.md`: técnico executante, signatário autorizado e cliente interno solicitante (setor Usinagem I).
3. **Cadastro de equipamentos:** um instrumento calibrado (`703.1208`) e um padrão de referência (`PAD-001`). O fabricante do primeiro é deixado em branco para mostrar que o campo é opcional.
4. **Erro tratado — TAG duplicada:** nova tentativa de cadastrar `PAD-001` é recusada com `RegistroDuplicadoError`.
5. **Registro de medições:** quatro medições, cada uma com seu `parametro_avaliado`, tolerâncias +TOL/-TOL e status calculado. Entre elas há um caso reprovado (desvio de +0,015 contra +TOL de 0,010), um com tolerância assimétrica e um exatamente no limite da tolerância (aprovado).
6. **Erros tratados — dados inválidos:** tolerância inferior positiva, medição sem equipamento/técnico (`id` nulo) e medição com chaves inexistentes (recusada pelo banco).
7. **Relatório consolidado:** `relatorio_calibracao()` executa um `JOIN` entre as três tabelas, e o relatório é impresso com a contagem de aprovadas e reprovadas.
8. **Atualização de dados:** o departamento de uma signatária é alterado e o valor obtido da medição reprovada é corrigido, o que recalcula automaticamente seu status para `Aprovado`.
9. **Exclusão de dados (Delete):** primeiro, a tentativa de excluir o instrumento `703.1208`, que ainda tem medições, é recusada pelo banco (`ON DELETE RESTRICT`) e tratada como `ErroBanco`. Depois são excluídos, nesta ordem, a medição do padrão, o próprio padrão `PAD-001` (que ficou sem medições) e o solicitante `Usinagem I` (sem medições). Excluir um `id` inexistente retorna `False`.
10. **Relatório final e listagens:** o relatório é reimpresso refletindo as atualizações e exclusões (3 medições restantes, todas aprovadas), e técnicos e equipamentos são listados.

Esse fluxo cobre as quatro operações do CRUD (Create, Read com `JOIN`, Update e Delete), além da criação das tabelas e de cinco cenários de erro tratado.

**Verificação de coerência.** Foi feita uma checagem automática (fora do `05_main.py`) comparando: (a) as colunas e tipos das três tabelas criadas pelo código com o `02_dicionario.md`; (b) o DDL das tabelas criadas pelo código com o do `03_banco.sql` executado diretamente; (c) os atributos das classes com os campos do dicionário. Os três resultados foram idênticos.

## 6. Limitações Conhecidas e Próximos Passos

**Dados de entrada fixos.** O `05_main.py` é uma demonstração com dados de exemplo. Os próximos passos previstos são: importar os arquivos de exportação da MMC (lotes de medições), oferecer uma interface para cadastro e consulta, gerar o certificado a partir da consulta e, por último, empacotar a aplicação em um executável.
