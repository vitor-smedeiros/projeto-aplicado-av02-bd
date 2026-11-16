
import importlib
import os


classes = importlib.import_module("04_classes")
Tecnico = classes.Tecnico
Equipamento = classes.Equipamento
Medicao = classes.Medicao
BancoDados = classes.BancoDados


def imprimir_relatorio(linhas):
    print("\n" + "=" * 100)
    print("RELATÓRIO DE CALIBRAÇÃO - SCHULZ S.A.")
    print("=" * 100)
    print(f"{'ID':<4}{'TAG':<10}{'EQUIPAMENTO':<27}{'TÉCNICO':<18}"
          f"{'DATA':<12}{'REF':>8}{'OBT':>9}{'TOL':>7}  STATUS")
    print("-" * 100)
    for l in linhas:
        # l = (id, tag, descricao, nome, data, ref, obtido, tol, status)
        print(f"{l[0]:<4}{l[1]:<10}{l[2]:<27}{l[3]:<18}"
              f"{l[4]:<12}{l[5]:>8.3f}{l[6]:>9.3f}{l[7]:>7.3f}  {l[8]}")
    print("-" * 100)

    aprovadas = sum(1 for l in linhas if l[8] == "APROVADO")
    reprovadas = len(linhas) - aprovadas
    print(f"Total: {len(linhas)} | Aprovadas: {aprovadas} | Reprovadas: {reprovadas}")


def main():
    if os.path.exists("schulz.db"):
        os.remove("schulz.db")

    banco = BancoDados("schulz.db")
    banco.conectar()
    banco.criar_tabelas()

    try:
        print(">> Inserindo técnicos...")
        t1 = Tecnico("T001", "Carlos Silva", "Metrologia")
        t2 = Tecnico("T002", "Ana Souza", "Laboratório")
        banco.inserir_tecnico(t1)
        banco.inserir_tecnico(t2)


        banco.inserir_tecnico(Tecnico("T001", "Duplicado", "Metrologia"))


        print(">> Inserindo equipamentos...")
        e1 = Equipamento("pq-001", "Paquímetro Digital 150mm", "Mitutoyo")
        e2 = Equipamento("mi-002", "Micrômetro Externo 25mm", "Starrett")
        e3 = Equipamento("mn-003", "Manômetro 0-10 bar", "Wika")
        banco.inserir_equipamento(e1)
        banco.inserir_equipamento(e2)
        banco.inserir_equipamento(e3)


        print(">> Inserindo medições...")
        medicoes = [
            Medicao(e1.id_equipamento, t1.id_tecnico, 100.00, 100.02, 0.03, "2025-05-10"),
            Medicao(e2.id_equipamento, t1.id_tecnico, 25.000, 25.010, 0.005, "2025-05-10"),
            Medicao(e3.id_equipamento, t2.id_tecnico, 5.00, 5.08, 0.10, "2025-05-11"),
            Medicao(e3.id_equipamento, t2.id_tecnico, 10.00, 10.25, 0.10, "2025-05-12"),
        ]
        for m in medicoes:
            banco.inserir_medicao(m)


        try:
            Medicao(e1.id_equipamento, t1.id_tecnico, 100, 100, -1)
        except ValueError as erro:
            print(f"Erro tratado (esperado): {erro}")


        imprimir_relatorio(banco.relatorio_calibracao())


        print("\n>> Atualizando setor do técnico 2 e corrigindo a medição 2...")
        banco.atualizar_setor_tecnico(t2.id_tecnico, "Qualidade")
        banco.atualizar_medicao(2, 25.004)   # agora dentro da tolerância

        imprimir_relatorio(banco.relatorio_calibracao())

        print("\n>> Técnicos cadastrados:")
        for t in banco.listar_tecnicos():
            print(t)

    finally:
        banco.desconectar()


if __name__ == "__main__":
    main()
