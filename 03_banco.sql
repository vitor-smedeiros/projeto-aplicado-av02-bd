-- Script DDL de Criação das Tabelas

-- 1. Criação da tabela Tecnico_Solicitante
CREATE TABLE Tecnico_Solicitante (
    id_tecnico INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    cargo_funcao TEXT NOT NULL,
    departamento TEXT
);

-- 2. Criação da tabela Equipamento
CREATE TABLE Equipamento (
    id_equipamento INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo_tag TEXT NOT NULL UNIQUE,
    denominacao TEXT NOT NULL,
    fabricante TEXT,
    tipo_item TEXT NOT NULL
);

-- 3. Criação da tabela Medicao
CREATE TABLE Medicao (
    id_medicao INTEGER PRIMARY KEY AUTOINCREMENT,
    id_equipamento_fk INTEGER NOT NULL,
    id_tecnico_fk INTEGER NOT NULL,
    parametro_avaliado TEXT NOT NULL,
    valor_nominal REAL NOT NULL,
    tolerancia_mais REAL NOT NULL,
    tolerancia_menos REAL NOT NULL,
    valor_obtido REAL NOT NULL,
    status_aprovacao TEXT NOT NULL,
    
    -- Definição das Chaves Estrangeiras conectando as medições aos equipamentos e técnicos
    FOREIGN KEY (id_equipamento_fk) REFERENCES Equipamento(id_equipamento) 
        ON DELETE RESTRICT 
        ON UPDATE CASCADE,
    FOREIGN KEY (id_tecnico_fk) REFERENCES Tecnico_Solicitante(id_tecnico) 
        ON DELETE RESTRICT 
        ON UPDATE CASCADE
);