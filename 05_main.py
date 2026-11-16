"""
05_main.py - Demonstração do fluxo completo do MVP (Schulz S.A.)

Todos os dados abaixo são EXEMPLOS escritos neste arquivo: não vêm de
nenhuma planilha nem da MMC. Servem para provar que o sistema cria o banco,
grava, consulta (JOIN), atualiza e trata erros.

Os nomes dos campos são os do 02_dicionario.md / 03_banco.sql.
"""

import importlib
import os

# O arquivo começa com número ("04_classes.py"), então "import 04_classes"
# não é permitido pelo Python; por isso usamos importlib.
classes = importlib.import_module("04_classes")
TecnicoSolicitante = classes.TecnicoSolicitante
Equipamento = classes.Equipamento
Medicao = classes.Medicao
BancoDados = classes.BancoDados
ErroBanco = classes.ErroBanco
RegistroDuplicadoError = classes.RegistroDuplicadoError
STATUS_APROVADO = classes.STATUS_APROVADO

# Banco exclusivo da demonstração. Ele é apagado a cada execução para o
# resultado ser sempre o mesmo. Um banco de uso real NÃO deve ser apagado.
ARQUIVO_DEMO = "schulz_demo.db"
LARGURA = 130


def cortar(texto, tamanho):
    """Corta textos longos para não desalinhar a tabela."""
    texto = str(texto)
    return texto if len(texto) <= tamanho else texto[: tamanho - 1] + "…"


def imprimir_relatorio(linhas):
    print("\n" + "=" * LARGURA)
    print("RELATÓRIO DE CALIBRAÇÃO - SCHULZ S.A.")
    print("=" * LARGURA)
    print(f"{'ID':<4}{'TAG':<10}{'EQUIPAMENTO':<25}{'TÉCNICO':<26}{'PARÂMETRO':<22}"
          f"{'NOMINAL':>9}{'+TOL':>8}{'-TOL':>8}{'OBTIDO':>9}  STATUS")
    print("-" * LARGURA)
    for l in linhas:
        print(f"{l['id_medicao']:<4}"
              f"{cortar(l['codigo_tag'], 9):<10}"
              f"{cortar(l['denominacao'], 24):<25}"
              f"{cortar(l['tecnico'], 25):<26}"
              f"{cortar(l['parametro_avaliado'], 21):<22}"
              f"{l['valor_nominal']:>9.3f}"
              f"{l['tolerancia_mais']:>8.3f}"
              f"{l['tolerancia_menos']:>8.3f}"
              f"{l['valor_obtido']:>9.3f}  "
              f"{l['status_aprovacao']}")
    print("-" * LARGURA)

    aprovadas = sum(1 for l in linhas if l["status_aprovacao"] == STATUS_APROVADO)
    reprovadas = len(linhas) - aprovadas
    print(f"Total: {len(linhas)} | Aprovadas: {aprovadas} | Reprovadas: {reprovadas}")


def main():
    if os.path.exists(ARQUIVO_DEMO):
        os.remove(ARQUIVO_DEMO)

    banco = BancoDados(ARQUIVO_DEMO)
    banco.conectar()

    try:
        # criar_tabelas() executa o 03_banco.sql
        banco.criar_tabelas()

        # ---- 1. Técnicos / solicitantes -------------------------------------
        print(">> Inserindo técnicos/solicitantes...")
        t1 = TecnicoSolicitante("Jose Alcides Rosa Junior", "Técnico executante",
                                "Laboratório de Metrologia")
        t2 = TecnicoSolicitante("Ana Souza", "Signatário autorizado",
                                "Laboratório de Metrologia")
        t3 = TecnicoSolicitante("Usinagem I", "Cliente interno solicitante",
                                "Usinagem I")
        for t in (t1, t2, t3):
            banco.inserir_tecnico(t)

        # ---- 2. Equipamentos -------------------------------------------------
        print(">> Inserindo equipamentos...")
        # fabricante é opcional (aceita NULL no banco)
        e1 = Equipamento("703.1208", "Dispositivo de controle", "Instrumento Calibrado")
        e2 = Equipamento("pad-001", "Bloco padrão 25 mm", "Padrão de Referência",
                         fabricante="Mitutoyo")
        banco.inserir_equipamento(e1)
        banco.inserir_equipamento(e2)

        # Erro tratado nº 1: codigo_tag é UNIQUE (e a TAG é normalizada em
        # maiúsculas, então "pad-001" e "PAD-001" são o mesmo item).
        try:
            banco.inserir_equipamento(
                Equipamento("PAD-001", "Outro bloco", "Padrão de Referência")
            )
        except RegistroDuplicadoError as erro:
            print(f"Erro tratado (esperado): {erro}")

        # ---- 3. Medições -----------------------------------------------------
        print(">> Inserindo medições...")
        # Cada medição calcula o próprio status: -TOL <= (obtido - nominal) <= +TOL
        m1 = Medicao(e1.id_equipamento, t1.id_tecnico, "Diâmetro do furo A",
                     25.000, 0.010, -0.010, 25.004)    # desvio +0.004 -> Aprovado
        m2 = Medicao(e1.id_equipamento, t1.id_tecnico, "Diâmetro do furo B",
                     25.000, 0.010, -0.010, 25.015)    # desvio +0.015 -> Reprovado
        m3 = Medicao(e1.id_equipamento, t1.id_tecnico, "Altura do rebaixo",
                     10.000, 0.020, 0.000, 10.012)     # tolerância assimétrica
        m4 = Medicao(e2.id_equipamento, t2.id_tecnico, "Comprimento",
                     100.000, 0.030, -0.030, 100.030)  # exatamente no limite
        for m in (m1, m2, m3, m4):
            banco.inserir_medicao(m)

        # Erro tratado nº 2: tolerância inferior não pode ser positiva.
        try:
            Medicao(e1.id_equipamento, t1.id_tecnico, "Teste", 10.0, 0.01, 0.01, 10.0)
        except ValueError as erro:
            print(f"Erro tratado (esperado): {erro}")

        # Erro tratado nº 3: medição sem equipamento/técnico salvo (id None).
        try:
            Medicao(None, None, "Teste", 10.0, 0.01, -0.01, 10.0)
        except ValueError as erro:
            print(f"Erro tratado (esperado): {erro}")

        # Erro tratado nº 4: o banco recusa FK que não existe (PRAGMA foreign_keys = ON).
        try:
            banco.inserir_medicao(Medicao(999, 999, "Teste", 10.0, 0.01, -0.01, 10.0))
        except ErroBanco as erro:
            print(f"Erro tratado (esperado): {erro}")

        imprimir_relatorio(banco.relatorio_calibracao())

        # ---- 4. Atualizações -------------------------------------------------
        print("\n>> Atualizando o departamento da signatária e corrigindo a "
              "medição do furo B...")
        banco.atualizar_departamento_tecnico(t2.id_tecnico, "Qualidade")
        banco.atualizar_medicao(m2.id_medicao, 25.008)   # agora dentro da tolerância

        imprimir_relatorio(banco.relatorio_calibracao())

        # ---- 5. Consultas simples -------------------------------------------
        print("\n>> Técnicos/solicitantes cadastrados:")
        for t in banco.listar_tecnicos():
            print(f"  {t}")

        print("\n>> Equipamentos cadastrados:")
        for e in banco.listar_equipamentos():
            print(f"  {e}")

    except (ErroBanco, ValueError) as erro:
        print(f"\nA demonstração foi interrompida: {erro}")
    finally:
        banco.desconectar()


if __name__ == "__main__":
    main()
