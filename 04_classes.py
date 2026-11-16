
import sqlite3
from datetime import date



class Tecnico:
    def __init__(self, matricula, nome, setor, id_tecnico=None):
        self.id_tecnico = id_tecnico
        self.matricula = matricula
        self.nome = nome
        self.setor = setor


    @property
    def nome(self):
        return self._nome

    @nome.setter
    def nome(self, valor):
        if not valor or not valor.strip():
            raise ValueError("O nome do técnico não pode ser vazio.")
        self._nome = valor.strip()

    def __str__(self):
        return f"Técnico {self.matricula} - {self.nome} ({self.setor})"


class Equipamento:
    def __init__(self, codigo_tag, descricao, fabricante, id_equipamento=None):
        self.id_equipamento = id_equipamento
        self.codigo_tag = codigo_tag
        self.descricao = descricao
        self.fabricante = fabricante

    @property
    def codigo_tag(self):
        return self._codigo_tag

    @codigo_tag.setter
    def codigo_tag(self, valor):
        if not valor or not valor.strip():
            raise ValueError("O código TAG do equipamento não pode ser vazio.")
        self._codigo_tag = valor.strip().upper()

    def __str__(self):
        return f"Equipamento {self.codigo_tag} - {self.descricao} ({self.fabricante})"


class Medicao:
    def __init__(self, id_equipamento, id_tecnico, valor_referencia,
                 valor_obtido, tolerancia, data_medicao=None, id_medicao=None):
        if tolerancia < 0:
            raise ValueError("não pode ser negativa.")
        self.id_medicao = id_medicao
        self.id_equipamento = id_equipamento
        self.id_tecnico = id_tecnico
        self.valor_referencia = valor_referencia
        self.valor_obtido = valor_obtido
        self.tolerancia = tolerancia
        self.data_medicao = data_medicao or str(date.today())
        self.status = self.validar_status()

    def calcular_erro(self):
        return abs(self.valor_obtido - self.valor_referencia)

    def validar_status(self):
        if self.calcular_erro() <= self.tolerancia:
            return "APROVADO"
        return "REPROVADO"


class BancoDados:
    def __init__(self, nome_arquivo="schulz.db"):
        self.nome_arquivo = nome_arquivo
        self.conexao = None

    def conectar(self):
        try:
            self.conexao = sqlite3.connect(self.nome_arquivo)
            self.conexao.execute("PRAGMA foreign_keys = ON")  # ativa as chaves estrangeiras
        except sqlite3.Error as erro:
            print(f"Erro ao conectar no banco: {erro}")
            raise

    def desconectar(self):
        if self.conexao:
            self.conexao.close()
            self.conexao = None

    def criar_tabelas(self):
        sql = """
        CREATE TABLE IF NOT EXISTS tecnicos (
            id_tecnico INTEGER PRIMARY KEY AUTOINCREMENT,
            matricula  TEXT NOT NULL UNIQUE,
            nome       TEXT NOT NULL,
            setor      TEXT
        );
        CREATE TABLE IF NOT EXISTS equipamentos (
            id_equipamento INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_tag     TEXT NOT NULL UNIQUE,
            descricao      TEXT NOT NULL,
            fabricante     TEXT
        );
        CREATE TABLE IF NOT EXISTS medicoes (
            id_medicao       INTEGER PRIMARY KEY AUTOINCREMENT,
            id_equipamento   INTEGER NOT NULL,
            id_tecnico       INTEGER NOT NULL,
            data_medicao     TEXT NOT NULL,
            valor_referencia REAL NOT NULL,
            valor_obtido     REAL NOT NULL,
            tolerancia       REAL NOT NULL,
            status           TEXT NOT NULL CHECK (status IN ('APROVADO', 'REPROVADO')),
            FOREIGN KEY (id_equipamento) REFERENCES equipamentos (id_equipamento),
            FOREIGN KEY (id_tecnico) REFERENCES tecnicos (id_tecnico)
        );
        """
        try:
            self.conexao.executescript(sql)
            self.conexao.commit()
        except sqlite3.Error as erro:
            print(f"Erro ao criar tabelas: {erro}")
            raise

    # ---------------- INSERT ----------------
    def inserir_tecnico(self, tecnico):
        try:
            cursor = self.conexao.execute(
                "INSERT INTO tecnicos (matricula, nome, setor) VALUES (?, ?, ?)",
                (tecnico.matricula, tecnico.nome, tecnico.setor),
            )
            self.conexao.commit()
            tecnico.id_tecnico = cursor.lastrowid
            return tecnico.id_tecnico
        except sqlite3.IntegrityError:
            self.conexao.rollback()
            print(f"Técnico com matrícula {tecnico.matricula} já existe.")
            return None
        except sqlite3.Error as erro:
            self.conexao.rollback()
            print(f"Erro ao inserir técnico: {erro}")
            return None

    def inserir_equipamento(self, equipamento):
        try:
            cursor = self.conexao.execute(
                "INSERT INTO equipamentos (codigo_tag, descricao, fabricante) VALUES (?, ?, ?)",
                (equipamento.codigo_tag, equipamento.descricao, equipamento.fabricante),
            )
            self.conexao.commit()
            equipamento.id_equipamento = cursor.lastrowid
            return equipamento.id_equipamento
        except sqlite3.IntegrityError:
            self.conexao.rollback()
            print(f"Equipamento com TAG {equipamento.codigo_tag} já existe.")
            return None
        except sqlite3.Error as erro:
            self.conexao.rollback()
            print(f"Erro ao inserir equipamento: {erro}")
            return None

    def inserir_medicao(self, medicao):
        try:
            cursor = self.conexao.execute(
                """INSERT INTO medicoes
                   (id_equipamento, id_tecnico, data_medicao, valor_referencia,
                    valor_obtido, tolerancia, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (medicao.id_equipamento, medicao.id_tecnico, medicao.data_medicao,
                 medicao.valor_referencia, medicao.valor_obtido,
                 medicao.tolerancia, medicao.status),
            )
            self.conexao.commit()
            medicao.id_medicao = cursor.lastrowid
            return medicao.id_medicao
        except sqlite3.Error as erro:
            self.conexao.rollback()
            print(f"Erro ao inserir medição: {erro}")
            return None

    def listar_tecnicos(self):
        cursor = self.conexao.execute("SELECT id_tecnico, matricula, nome, setor FROM tecnicos")
        return cursor.fetchall()

    def listar_equipamentos(self):
        cursor = self.conexao.execute(
            "SELECT id_equipamento, codigo_tag, descricao, fabricante FROM equipamentos"
        )
        return cursor.fetchall()

    def relatorio_calibracao(self):
        sql = """
        SELECT m.id_medicao, e.codigo_tag, e.descricao, t.nome,
               m.data_medicao, m.valor_referencia, m.valor_obtido,
               m.tolerancia, m.status
        FROM medicoes m
        JOIN equipamentos e ON m.id_equipamento = e.id_equipamento
        JOIN tecnicos t     ON m.id_tecnico = t.id_tecnico
        ORDER BY m.data_medicao, m.id_medicao
        """
        cursor = self.conexao.execute(sql)
        return cursor.fetchall()

    def atualizar_setor_tecnico(self, id_tecnico, novo_setor):
        try:
            cursor = self.conexao.execute(
                "UPDATE tecnicos SET setor = ? WHERE id_tecnico = ?",
                (novo_setor, id_tecnico),
            )
            self.conexao.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as erro:
            self.conexao.rollback()
            print(f"Erro ao atualizar técnico: {erro}")
            return False

    def atualizar_medicao(self, id_medicao, novo_valor_obtido):
        """Atualiza o valor obtido e recalcula o status."""
        try:
            cursor = self.conexao.execute(
                "SELECT id_equipamento, id_tecnico, data_medicao, valor_referencia, tolerancia "
                "FROM medicoes WHERE id_medicao = ?",
                (id_medicao,),
            )
            linha = cursor.fetchone()
            if linha is None:
                print("Medição não encontrada.")
                return False

            nova = Medicao(linha[0], linha[1], linha[3], novo_valor_obtido, linha[4], linha[2])
            self.conexao.execute(
                "UPDATE medicoes SET valor_obtido = ?, status = ? WHERE id_medicao = ?",
                (nova.valor_obtido, nova.status, id_medicao),
            )
            self.conexao.commit()
            return True
        except sqlite3.Error as erro:
            self.conexao.rollback()
            print(f"Erro ao atualizar medição: {erro}")
            return False
