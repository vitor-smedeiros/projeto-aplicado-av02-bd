# Organização dos Dados e Modelo Conceitual Simplificado

A modelagem do Banco de Dados Relacional para o sistema de emissão de certificados de calibração da Schulz S.A. foi desenvolvida com base no diagnóstico operacional realizado na Entrega 01. O principal problema identificado anteriormente era o uso de múltiplas planilhas desconectadas (como as abas "Importação", "Registro" e "Complemento"), o que exigia a transcrição manual repetitiva de informações e gerava um alto risco de inconsistência. 

Para resolver esses problemas de arquitetura e garantir a integridade dos dados, estruturamos o banco de dados relacional dividindo as informações em três entidades principais, conforme as diretrizes do projeto:

1. Técnico/Solicitante: 
Esta entidade centraliza o cadastro de todos os recursos humanos envolvidos no fluxo de calibração. Ela agrupa tanto o técnico executante (que capta os dados na máquina de medição por coordenadas - MMC) quanto o metrologista (signatário autorizado) e o cliente interno solicitante (como o setor de Usinagem I). O objetivo de isolar estas informações é evitar que o nome do colaborador, o seu cargo ou o seu departamento precisem de ser digitados repetidas vezes a cada nova medição realizada.

2. Equipamento: 
Esta entidade é responsável por armazenar de forma única o cadastro físico e metrológico dos itens utilizados na operação da Schulz S.A.. Ela substitui a necessidade de preenchimento manual recorrente dos dados do instrumento calibrado (como código, denominação, fabricante e TAG) e dos padrões de referência. Ao unificar estes dados cadastrais numa tabela independente, evitamos as lacunas, informações nulas e anomalias que ocorriam frequentemente na antiga aba "Complemento".

3. Medição: 
Atuando como a tabela transacional central do sistema, esta entidade regista o histórico detalhado de cada aferição. Ela substitui a antiga aba "Registro" e recebe os dados brutos de exportação da MMC, armazenando o parâmetro avaliado, os valores nominais esperados, as tolerâncias permitidas e o valor efetivamente obtido. Esta tabela conecta-se às entidades de Equipamento e Técnico através de chaves estrangeiras (Foreign Keys).

A Importância de Evitar Dados Duplicados (Normalização):
A normalização do banco de dados para evitar a duplicação de informações é um passo fundamental para garantir a segurança, a rastreabilidade e a consistência exigidas em auditorias de qualidade, como a norma ISO/IEC 17025. 

No modelo anterior, baseado em Excel, a repetição manual de campos causava divergências graves, como datas corrompidas e fórmulas quebradas (erros #NAME?), aumentando consideravelmente o risco de emissão de certificados com dados irreais e comprometendo a operação. 

Ao separar o sistema nestas três entidades relacionais e ligá-las de forma estruturada, garantimos que qualquer alteração no cadastro de um equipamento ou de um técnico seja feita num único lugar e propagada automaticamente para todos os registos vinculados. Isto não apenas elimina o retrabalho e o risco de falha humana na digitação, como também cria um histórico confiável e imutável para as calibrações da Schulz S.A., substituindo definitivamente a leitura estática das planilhas.