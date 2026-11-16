# Documentação Técnica do MVP — Parte 1

Projeto Aplicado I — Automação de Certificados de Calibração (Schulz S.A.)
Linguagem utilizada: Python 3, com persistência em SQLite (`sqlite3`).

## 1. Padrões de Orientação a Objetos Utilizados

**Encapsulamento com validação.** As classes `Tecnico` e `Equipamento` expõem seus atributos sensíveis (`nome`, `codigo_tag`) como `@property`, com um setter que valida o valor antes de armazená-lo. Um nome vazio ou um código TAG em branco é rejeitado no momento da atribuição, e não apenas quando o dado chega ao banco. Isso impede que um objeto inválido chegue a existir em memória.

**Separação de responsabilidades.** O módulo divide claramente dois papéis: classes de domínio (`Tecnico`, `Equipamento`, `Medicao`), que representam as regras de negócio metrológicas, e uma classe de persistência (`BancoDados`), responsável exclusivamente por abrir conexão, criar tabelas e executar comandos SQL. Nenhuma classe de domínio conhece o SQLite; a tradução entre objeto e tabela é feita inteiramente dentro de `BancoDados`.

**Validação no construtor (fail-fast).** `Medicao` calcula seu próprio `status` (`APROVADO`/`REPROVADO`) dentro do `__init__`, chamando `validar_status()`. Uma tolerância negativa é rejeitada antes mesmo de o objeto ser criado, levantando `ValueError` imediatamente.

**Associação por chave, não por composição de objeto.** `Medicao` não guarda uma referência direta aos objetos `Tecnico` e `Equipamento`, apenas seus identificadores (`id_equipamento`, `id_tecnico`). Essa escolha espelha o modelo relacional do Tema 02 (chaves estrangeiras) e evita acoplamento forte entre as classes de domínio em memória.

## 2. Diagrama Textual das Classes (UML Simplificado)

```
+----------------------------+
|          Tecnico           |
+----------------------------+
| - id_tecnico: int          |
| - matricula: str           |
| - nome: str  [validado]    |
| - setor: str                |
+----------------------------+
| + __str__(): str            |
+----------------------------+
              ^
              | 1
              |
              | N
+----------------------------+        N        1    +----------------------------+
|          Medicao            |-------------------->|        Equipamento          |
+----------------------------+                      +----------------------------+
| - id_medicao: int           |                      | - id_equipamento: int       |
| - id_equipamento: int (FK)  |                      | - codigo_tag: str [validado]|
| - id_tecnico: int (FK)      |                      | - descricao: str            |
| - valor_referencia: float   |                      | - fabricante: str           |
| - valor_obtido: float       |                      +----------------------------+
| - tolerancia: float         |                      | + __str__(): str            |
| - data_medicao: str         |                      +----------------------------+
| - status: str                |
+----------------------------+
| + calcular_erro(): float    |
| + validar_status(): str     |
+----------------------------+

+--------------------------------------------------+
|                    BancoDados                     |
+--------------------------------------------------+
| - nome_arquivo: str                               |
| - conexao: Connection                             |
+--------------------------------------------------+
| + conectar() / desconectar()                      |
| + criar_tabelas()                                 |
| + inserir_tecnico(Tecnico)                         |
| + inserir_equipamento(Equipamento)                 |
| + inserir_medicao(Medicao)                         |
| + atualizar_setor_tecnico(id, novo_setor)          |
| + atualizar_medicao(id, novo_valor_obtido)         |
| + listar_tecnicos() / listar_equipamentos()        |
| + relatorio_calibracao()                            |
+--------------------------------------------------+
   ..> depende de Tecnico, Equipamento e Medicao
       (persiste e reconstrói esses objetos via SQL)
```

Cardinalidade: um `Tecnico` executa N `Medicao`; um `Equipamento` é alvo de N `Medicao`. `BancoDados` não herda nem é herdado por nenhuma classe de domínio — a relação é de dependência (uso), não de hierarquia.

## 3. Tratamento de Erros

O sistema trata erros em duas camadas distintas:

**Camada de domínio (regra de negócio).** `ValueError` é levantado diretamente nos construtores/setters quando um dado viola uma regra antes mesmo de tocar o banco: nome ou código TAG vazio, tolerância negativa. Em `05_main.py`, esse erro é capturado com `try/except ValueError` ao tentar criar uma `Medicao` com tolerância `-1`, confirmando que a validação ocorre em memória, sem necessidade de uma transação no banco para ser descartada.

**Camada de persistência (integridade do banco).** Cada método de inserção em `BancoDados` captura dois tipos de exceção separadamente:
- `sqlite3.IntegrityError`: disparado pelas restrições `UNIQUE` em `matricula` e `codigo_tag`. Ao tentar inserir um técnico com uma matrícula já existente (caso demonstrado em `05_main.py` com `T001` duplicado), a transação é desfeita com `rollback()` e uma mensagem específica é exibida, sem derrubar a aplicação.
- `sqlite3.Error` (classe genérica): cobre qualquer outra falha de banco (conexão perdida, SQL malformado), também seguida de `rollback()`.

Em ambos os casos o padrão é o mesmo: nunca deixar uma transação parcial comprometida — ou o `commit()` é confirmado, ou o `rollback()` desfaz tudo. A integridade referencial entre tabelas é reforçada em nível de banco por `PRAGMA foreign_keys = ON`, ativado logo na conexão, o que garante que as chaves estrangeiras definidas no DDL do Tema 02 sejam de fato checadas pelo SQLite (que, por padrão, as ignora).

## 4. Validação do Fluxo Funcional do MVP

O script `05_main.py` demonstra o ciclo completo de uso do sistema:

1. **Inicialização:** remove um banco `schulz.db` pré-existente e recria a estrutura com `criar_tabelas()`, garantindo um estado limpo a cada execução.
2. **Inserção de técnicos:** dois técnicos são cadastrados com sucesso; uma terceira tentativa, com matrícula repetida (`T001`), é rejeitada pela restrição `UNIQUE`, validando o tratamento de `IntegrityError`.
3. **Inserção de equipamentos:** três instrumentos de medição são cadastrados (paquímetro, micrômetro, manômetro).
4. **Inserção de medições:** quatro medições são registradas, cada uma calculando seu próprio status de aprovação a partir da tolerância informada.
5. **Rejeição de dado inválido:** uma tentativa de medição com tolerância `-1` é capturada como `ValueError`, sem afetar o restante da execução.
6. **Relatório consolidado:** `relatorio_calibracao()` executa um `JOIN` entre as três tabelas e o relatório é impresso no terminal com contagem de aprovadas/reprovadas.
7. **Atualização de dados:** o setor de um técnico é alterado e o valor obtido de uma medição é corrigido, o que recalcula automaticamente seu status (de `REPROVADO` para `APROVADO`, ao entrar dentro da tolerância).
8. **Relatório final:** o mesmo relatório é reimpresso, refletindo as atualizações — confirmando que a camada de persistência e a lógica de domínio permanecem sincronizadas após uma operação de `UPDATE`.

Esse fluxo cobre as quatro operações exigidas (criação de tabelas, inserção, consulta com `JOIN` e atualização), além de dois cenários de erro tratado, validando o funcionamento do MVP de ponta a ponta.
