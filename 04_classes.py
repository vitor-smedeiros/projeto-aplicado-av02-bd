"""
04_classes.py - Camada de domínio e de persistência do MVP (Schulz S.A.)

Este módulo segue EXATAMENTE o modelo definido em:
    01_estrutura.md  -> as 3 entidades (Técnico/Solicitante, Equipamento, Medição)
    02_dicionario.md -> nomes e tipos de cada campo
    03_banco.sql     -> DDL das tabelas (é o próprio arquivo executado aqui)

Regra do projeto: os nomes de tabelas e colunas existem em UM lugar só, o
03_banco.sql. As classes usam os mesmos nomes do dicionário de dados.
"""

import math
import os
import sqlite3

# Caminho do 03_banco.sql, sempre relativo a este arquivo (e não à pasta
# de onde o programa foi executado).
CAMINHO_SQL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "03_banco.sql")

STATUS_APROVADO = "Aprovado"
STATUS_REPROVADO = "Reprovado"

# Casas decimais usadas ao comparar valores com a tolerância. Evita que o erro
# de ponto flutuante (ex.: 100.03 - 100 = 0.030000000000001137) reprove uma
# medição que está exatamente no limite.
CASAS_DECIMAIS = 9


# ---------------------------------------------------------------------------
# Exceções da camada de persistência
# ---------------------------------------------------------------------------
class ErroBanco(Exception):
    """Falha ao acessar ou gravar no banco de dados."""


class RegistroDuplicadoError(ErroBanco):
    """Violação de unicidade (ex.: codigo_tag já cadastrado)."""


# ---------------------------------------------------------------------------
# Funções de validação reutilizadas pelas classes de domínio
# ---------------------------------------------------------------------------
def _texto_obrigatorio(valor, campo):
    """Campos NOT NULL do tipo TEXT: não aceita None, número ou texto em branco."""
    if not isinstance(valor, str) or not valor.strip():
        raise ValueError(f"O campo '{campo}' não pode ser vazio.")
    return valor.strip()


def _texto_opcional(valor, campo):
    """Campos TEXT que aceitam NULL no banco: texto em branco vira None."""
    if valor is None:
        return None
    if not isinstance(valor, str):
        raise ValueError(f"O campo '{campo}' deve ser um texto.")
    return valor.strip() or None


def _numero(valor, campo):
    """Campos REAL: aceita int/float finitos (rejeita texto, bool, NaN e infinito)."""
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise ValueError(f"O campo '{campo}' deve ser numérico.")
    if not math.isfinite(valor):
        raise ValueError(f"O campo '{campo}' deve ser um número finito.")
    return float(valor)


def _id_obrigatorio(valor, campo):
    """Chaves estrangeiras NOT NULL: o registro referenciado precisa já estar salvo."""
    if isinstance(valor, bool) or not isinstance(valor, int):
        raise ValueError(
            f"O campo '{campo}' é obrigatório. Cadastre o registro no banco "
            f"antes de criar a medição."
        )
    return valor


# ---------------------------------------------------------------------------
# Classes de domínio (não conhecem o SQLite)
# ---------------------------------------------------------------------------
class TecnicoSolicitante:
    """Entidade Técnico/Solicitante (tabela Tecnico_Solicitante)."""

    def __init__(self, nome, cargo_funcao, departamento=None, id_tecnico=None):
        self.id_tecnico = id_tecnico
        self.nome = nome
        self.cargo_funcao = cargo_funcao
        self.departamento = departamento

    @property
    def nome(self):
        return self._nome

    @nome.setter
    def nome(self, valor):
        self._nome = _texto_obrigatorio(valor, "nome")

    @property
    def cargo_funcao(self):
        return self._cargo_funcao

    @cargo_funcao.setter
    def cargo_funcao(self, valor):
        self._cargo_funcao = _texto_obrigatorio(valor, "cargo_funcao")

    @property
    def departamento(self):
        return self._departamento

    @departamento.setter
    def departamento(self, valor):
        self._departamento = _texto_opcional(valor, "departamento")

    def __str__(self):
        depto = self.departamento or "sem departamento"
        return f"{self.nome} - {self.cargo_funcao} ({depto})"


class Equipamento:
    """Entidade Equipamento (tabela Equipamento): instrumento ou padrão de referência."""

    def __init__(self, codigo_tag, denominacao, tipo_item, fabricante=None,
                 id_equipamento=None):
        self.id_equipamento = id_equipamento
        self.codigo_tag = codigo_tag
        self.denominacao = denominacao
        self.tipo_item = tipo_item
        self.fabricante = fabricante

    @property
    def codigo_tag(self):
        return self._codigo_tag

    @codigo_tag.setter
    def codigo_tag(self, valor):
        # TAG é normalizada em maiúsculas: "pad-001" e "PAD-001" são o mesmo item.
        self._codigo_tag = _texto_obrigatorio(valor, "codigo_tag").upper()

    @property
    def denominacao(self):
        return self._denominacao

    @denominacao.setter
    def denominacao(self, valor):
        self._denominacao = _texto_obrigatorio(valor, "denominacao")

    @property
    def tipo_item(self):
        return self._tipo_item

    @tipo_item.setter
    def tipo_item(self, valor):
        self._tipo_item = _texto_obrigatorio(valor, "tipo_item")

    @property
    def fabricante(self):
        return self._fabricante

    @fabricante.setter
    def fabricante(self, valor):
        self._fabricante = _texto_opcional(valor, "fabricante")

    def __str__(self):
        fab = self.fabricante or "fabricante não informado"
        return f"{self.codigo_tag} - {self.denominacao} [{self.tipo_item}] ({fab})"


class Medicao:
    """
    Entidade Medição (tabela Medicao): uma aferição de um parâmetro.

    Convenção das tolerâncias (iguais às colunas exportadas pela MMC):
        tolerancia_mais  (+TOL) >= 0  -> desvio máximo acima do nominal
        tolerancia_menos (-TOL) <= 0  -> desvio máximo abaixo do nominal
    Exemplo: nominal 25.000, +TOL 0.010, -TOL -0.010  ->  faixa 24.990 a 25.010.

    O status_aprovacao não é guardado em separado: é sempre calculado a partir
    dos valores atuais, então nunca fica desatualizado.
    """

    def __init__(self, id_equipamento_fk, id_tecnico_fk, parametro_avaliado,
                 valor_nominal, tolerancia_mais, tolerancia_menos, valor_obtido,
                 id_medicao=None):
        self.id_medicao = id_medicao
        self.id_equipamento_fk = id_equipamento_fk
        self.id_tecnico_fk = id_tecnico_fk
        self.parametro_avaliado = parametro_avaliado
        self.valor_nominal = valor_nominal
        self.tolerancia_mais = tolerancia_mais
        self.tolerancia_menos = tolerancia_menos
        self.valor_obtido = valor_obtido

    # --- chaves estrangeiras -------------------------------------------------
    @property
    def id_equipamento_fk(self):
        return self._id_equipamento_fk

    @id_equipamento_fk.setter
    def id_equipamento_fk(self, valor):
        self._id_equipamento_fk = _id_obrigatorio(valor, "id_equipamento_fk")

    @property
    def id_tecnico_fk(self):
        return self._id_tecnico_fk

    @id_tecnico_fk.setter
    def id_tecnico_fk(self, valor):
        self._id_tecnico_fk = _id_obrigatorio(valor, "id_tecnico_fk")

    # --- dados da medição ----------------------------------------------------
    @property
    def parametro_avaliado(self):
        return self._parametro_avaliado

    @parametro_avaliado.setter
    def parametro_avaliado(self, valor):
        self._parametro_avaliado = _texto_obrigatorio(valor, "parametro_avaliado")

    @property
    def valor_nominal(self):
        return self._valor_nominal

    @valor_nominal.setter
    def valor_nominal(self, valor):
        self._valor_nominal = _numero(valor, "valor_nominal")

    @property
    def tolerancia_mais(self):
        return self._tolerancia_mais

    @tolerancia_mais.setter
    def tolerancia_mais(self, valor):
        valor = _numero(valor, "tolerancia_mais")
        if valor < 0:
            raise ValueError(
                "A tolerância superior (+TOL) não pode ser negativa "
                "(ex.: use 0.010 e não -0.010)."
            )
        self._tolerancia_mais = valor

    @property
    def tolerancia_menos(self):
        return self._tolerancia_menos

    @tolerancia_menos.setter
    def tolerancia_menos(self, valor):
        valor = _numero(valor, "tolerancia_menos")
        if valor > 0:
            raise ValueError(
                "A tolerância inferior (-TOL) não pode ser positiva "
                "(ex.: use -0.010 e não 0.010)."
            )
        self._tolerancia_menos = valor

    @property
    def valor_obtido(self):
        return self._valor_obtido

    @valor_obtido.setter
    def valor_obtido(self, valor):
        self._valor_obtido = _numero(valor, "valor_obtido")

    # --- regras de negócio ---------------------------------------------------
    def calcular_desvio(self):
        """Desvio com sinal: valor_obtido - valor_nominal."""
        return round(self.valor_obtido - self.valor_nominal, CASAS_DECIMAIS)

    def validar_status(self):
        """Aprovado se -TOL <= desvio <= +TOL; caso contrário, Reprovado."""
        desvio = self.calcular_desvio()
        limite_inf = round(self.tolerancia_menos, CASAS_DECIMAIS)
        limite_sup = round(self.tolerancia_mais, CASAS_DECIMAIS)
        if limite_inf <= desvio <= limite_sup:
            return STATUS_APROVADO
        return STATUS_REPROVADO

    @property
    def status_aprovacao(self):
        return self.validar_status()


# ---------------------------------------------------------------------------
# Camada de persistência
# ---------------------------------------------------------------------------
class BancoDados:
    """Único ponto do sistema que conhece o SQLite e o SQL."""

    def __init__(self, nome_arquivo="schulz.db"):
        self.nome_arquivo = nome_arquivo
        self.conexao = None

    def conectar(self):
        try:
            self.conexao = sqlite3.connect(self.nome_arquivo)
            self.conexao.row_factory = sqlite3.Row
            # O SQLite ignora FOREIGN KEY por padrão; sem isto as chaves
            # estrangeiras do 03_banco.sql não seriam verificadas.
            self.conexao.execute("PRAGMA foreign_keys = ON")
        except sqlite3.Error as erro:
            raise ErroBanco(f"Erro ao conectar no banco: {erro}") from erro

    def desconectar(self):
        if self.conexao:
            self.conexao.close()
            self.conexao = None

    def criar_tabelas(self):
        """
        Executa o 03_banco.sql se o banco ainda não tiver as tabelas.
        Como o .sql usa CREATE TABLE simples, a checagem abaixo evita erro
        ao abrir um banco que já existe (e preserva os dados dele).
        """
        existe = self.conexao.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'Medicao'"
        ).fetchone()
        if existe:
            return
        try:
            with open(CAMINHO_SQL, encoding="utf-8") as arquivo:
                self.conexao.executescript(arquivo.read())
            self.conexao.commit()
        except (OSError, sqlite3.Error) as erro:
            raise ErroBanco(
                f"Erro ao criar tabelas a partir do 03_banco.sql: {erro}"
            ) from erro

    # ---------------- INSERT ----------------
    def inserir_tecnico(self, tecnico):
        try:
            cursor = self.conexao.execute(
                "INSERT INTO Tecnico_Solicitante (nome, cargo_funcao, departamento) "
                "VALUES (?, ?, ?)",
                (tecnico.nome, tecnico.cargo_funcao, tecnico.departamento),
            )
            self.conexao.commit()
        except sqlite3.Error as erro:
            self.conexao.rollback()
            raise ErroBanco(f"Erro ao inserir técnico/solicitante: {erro}") from erro
        tecnico.id_tecnico = cursor.lastrowid
        return tecnico.id_tecnico

    def inserir_equipamento(self, equipamento):
        try:
            cursor = self.conexao.execute(
                "INSERT INTO Equipamento (codigo_tag, denominacao, fabricante, tipo_item) "
                "VALUES (?, ?, ?, ?)",
                (equipamento.codigo_tag, equipamento.denominacao,
                 equipamento.fabricante, equipamento.tipo_item),
            )
            self.conexao.commit()
        except sqlite3.IntegrityError as erro:
            self.conexao.rollback()
            raise RegistroDuplicadoError(
                f"Já existe um equipamento com a TAG {equipamento.codigo_tag}."
            ) from erro
        except sqlite3.Error as erro:
            self.conexao.rollback()
            raise ErroBanco(f"Erro ao inserir equipamento: {erro}") from erro
        equipamento.id_equipamento = cursor.lastrowid
        return equipamento.id_equipamento

    def inserir_medicao(self, medicao):
        try:
            cursor = self.conexao.execute(
                """INSERT INTO Medicao
                   (id_equipamento_fk, id_tecnico_fk, parametro_avaliado,
                    valor_nominal, tolerancia_mais, tolerancia_menos,
                    valor_obtido, status_aprovacao)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (medicao.id_equipamento_fk, medicao.id_tecnico_fk,
                 medicao.parametro_avaliado, medicao.valor_nominal,
                 medicao.tolerancia_mais, medicao.tolerancia_menos,
                 medicao.valor_obtido, medicao.status_aprovacao),
            )
            self.conexao.commit()
        except sqlite3.IntegrityError as erro:
            self.conexao.rollback()
            raise ErroBanco(
                "Medição rejeitada: o equipamento ou o técnico informado não "
                "existe no banco."
            ) from erro
        except sqlite3.Error as erro:
            self.conexao.rollback()
            raise ErroBanco(f"Erro ao inserir medição: {erro}") from erro
        medicao.id_medicao = cursor.lastrowid
        return medicao.id_medicao

    # ---------------- SELECT ----------------
    def listar_tecnicos(self):
        linhas = self.conexao.execute(
            "SELECT id_tecnico, nome, cargo_funcao, departamento "
            "FROM Tecnico_Solicitante ORDER BY id_tecnico"
        ).fetchall()
        return [
            TecnicoSolicitante(l["nome"], l["cargo_funcao"], l["departamento"],
                               id_tecnico=l["id_tecnico"])
            for l in linhas
        ]

    def listar_equipamentos(self):
        linhas = self.conexao.execute(
            "SELECT id_equipamento, codigo_tag, denominacao, fabricante, tipo_item "
            "FROM Equipamento ORDER BY id_equipamento"
        ).fetchall()
        return [
            Equipamento(l["codigo_tag"], l["denominacao"], l["tipo_item"],
                        l["fabricante"], id_equipamento=l["id_equipamento"])
            for l in linhas
        ]

    def buscar_medicao(self, id_medicao):
        """Retorna a Medicao com esse id, ou None se não existir."""
        l = self.conexao.execute(
            "SELECT * FROM Medicao WHERE id_medicao = ?", (id_medicao,)
        ).fetchone()
        if l is None:
            return None
        return Medicao(
            l["id_equipamento_fk"], l["id_tecnico_fk"], l["parametro_avaliado"],
            l["valor_nominal"], l["tolerancia_mais"], l["tolerancia_menos"],
            l["valor_obtido"], id_medicao=l["id_medicao"],
        )

    def relatorio_calibracao(self):
        """JOIN das 3 tabelas. Cada linha é acessada pelo nome da coluna."""
        sql = """
        SELECT m.id_medicao, e.codigo_tag, e.denominacao,
               t.nome AS tecnico, m.parametro_avaliado,
               m.valor_nominal, m.tolerancia_mais, m.tolerancia_menos,
               m.valor_obtido, m.status_aprovacao
        FROM Medicao m
        JOIN Equipamento e         ON m.id_equipamento_fk = e.id_equipamento
        JOIN Tecnico_Solicitante t ON m.id_tecnico_fk     = t.id_tecnico
        ORDER BY m.id_medicao
        """
        return self.conexao.execute(sql).fetchall()

    # ---------------- UPDATE ----------------
    def atualizar_departamento_tecnico(self, id_tecnico, novo_departamento):
        novo_departamento = _texto_opcional(novo_departamento, "departamento")
        try:
            cursor = self.conexao.execute(
                "UPDATE Tecnico_Solicitante SET departamento = ? WHERE id_tecnico = ?",
                (novo_departamento, id_tecnico),
            )
            self.conexao.commit()
        except sqlite3.Error as erro:
            self.conexao.rollback()
            raise ErroBanco(f"Erro ao atualizar técnico/solicitante: {erro}") from erro
        return cursor.rowcount > 0

    def atualizar_medicao(self, id_medicao, novo_valor_obtido):
        """
        Atualiza valor_obtido e recalcula status_aprovacao.
        A regra de aprovação continua só na classe Medicao: o banco apenas
        carrega o objeto, a classe recalcula, e o resultado é gravado.
        Retorna False se o id não existir.
        """
        medicao = self.buscar_medicao(id_medicao)
        if medicao is None:
            return False
        medicao.valor_obtido = novo_valor_obtido  # valida o novo valor
        try:
            self.conexao.execute(
                "UPDATE Medicao SET valor_obtido = ?, status_aprovacao = ? "
                "WHERE id_medicao = ?",
                (medicao.valor_obtido, medicao.status_aprovacao, id_medicao),
            )
            self.conexao.commit()
        except sqlite3.Error as erro:
            self.conexao.rollback()
            raise ErroBanco(f"Erro ao atualizar medição: {erro}") from erro
        return True
