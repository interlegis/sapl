-- Apaga as restrições somente para essa sessão
SELECT replace(@@sql_mode,'STRICT_TRANS_TABLES,','ALLOW_INVALID_DATES');

-- Exclui procedures caso já existam
DROP PROCEDURE IF EXISTS verifica_campos_proposicao;
DROP PROCEDURE IF EXISTS verifica_campos_tipo_materia_legislativa;
DROP PROCEDURE IF EXISTS verifica_campos_sessao_plenaria_presenca;
DROP PROCEDURE IF EXISTS cria_lexml_registro_provedor_e_publicador;
DROP PROCEDURE IF EXISTS cria_tipo_situacao_militar;
DROP PROCEDURE IF EXISTS muda_vinculo_norma_juridica_ind_excluido;
DROP PROCEDURE IF EXISTS muda_unidade_tramitacao_cod_parlamentar;

-- Procedure para criar campo num_proposicao em proposicao
CREATE PROCEDURE verifica_campos_proposicao() BEGIN IF NOT EXISTS
  (SELECT *
   FROM information_schema.columns
   WHERE table_schema=database()
     AND TABLE_NAME='proposicao'
     AND COLUMN_NAME='num_proposicao') THEN

  -- ajusta data zero para poder alterar a tabela
  UPDATE proposicao SET dat_envio = '1800-01-01' WHERE dat_envio = 0;
  alter table proposicao modify dat_envio datetime;
  UPDATE proposicao SET dat_envio = NULL where dat_envio = '1800-01-01';

  ALTER TABLE proposicao ADD COLUMN num_proposicao int(11) NULL AFTER txt_justif_devolucao;
END IF; END;

-- Procedure para criar campo iind_num_automatica em tipo_materia_legislativa
CREATE PROCEDURE verifica_campos_tipo_materia_legislativa()
BEGIN IF NOT EXISTS
  (SELECT *
   FROM information_schema.columns
   WHERE table_schema=database()
     AND TABLE_NAME='tipo_materia_legislativa'
     AND COLUMN_NAME='ind_num_automatica') THEN
ALTER TABLE tipo_materia_legislativa ADD COLUMN ind_num_automatica BOOLEAN NULL DEFAULT FALSE AFTER des_tipo_materia;
END IF;
IF NOT EXISTS
  (SELECT *
   FROM information_schema.columns
   WHERE table_schema=database()
     AND TABLE_NAME='tipo_materia_legislativa'
     AND COLUMN_NAME='quorum_minimo_votacao') THEN
ALTER TABLE tipo_materia_legislativa ADD COLUMN quorum_minimo_votacao int(11) NULL AFTER ind_num_automatica;
END IF; END;

-- Procedure para criar campos cod_presenca_sessao (sendo a nova PK da tabela) e dat_sessao em sessao_plenaria_presenca
CREATE PROCEDURE verifica_campos_sessao_plenaria_presenca() BEGIN IF NOT EXISTS
  (SELECT *
   FROM information_schema.columns
   WHERE table_schema=database()
     AND TABLE_NAME='sessao_plenaria_presenca'
     AND COLUMN_NAME='cod_presenca_sessao') THEN
ALTER TABLE sessao_plenaria_presenca
DROP PRIMARY KEY,
             ADD cod_presenca_sessao INT auto_increment PRIMARY KEY FIRST;
END IF;
IF NOT EXISTS
  (SELECT *
   FROM information_schema.columns
   WHERE table_schema=database()
     AND TABLE_NAME='sessao_plenaria_presenca'
     AND COLUMN_NAME='dat_sessao') THEN
ALTER TABLE sessao_plenaria_presenca ADD COLUMN dat_sessao DATE NULL AFTER cod_parlamentar;
END IF; END;


-- Procedure para criar tabela lexml_registro_provedor e lexml_registro_publicador
CREATE PROCEDURE cria_lexml_registro_provedor_e_publicador()
BEGIN IF NOT EXISTS
  (SELECT *
   FROM information_schema.columns
   WHERE table_schema=database()
     AND TABLE_NAME='lexml_registro_publicador') THEN
CREATE TABLE lexml_registro_publicador (
    cod_publicador INT auto_increment NOT NULL,
    id_publicador INT, nom_publicador varchar(255),
    adm_email varchar(50),
    sigla varchar(255),
    nom_responsavel varchar(255),
    tipo varchar(50),
    id_responsavel INT, PRIMARY KEY (cod_publicador));
END IF;
IF NOT EXISTS
    (SELECT *
        FROM information_schema.columns
        WHERE table_schema=database()
     AND TABLE_NAME='lexml_registro_provedor') THEN
CREATE TABLE lexml_registro_provedor (
    cod_provedor INT auto_increment NOT NULL,
    id_provedor INT, nom_provedor varchar(255),
    sgl_provedor varchar(15),
    adm_email varchar(50),
    nom_responsavel varchar(255),
    tipo varchar(50),
    id_responsavel INT, xml_provedor longtext,
    PRIMARY KEY (cod_provedor));
END IF; END;

-- Procedure para criar tabela tipo_situacao_militar
CREATE PROCEDURE cria_tipo_situacao_militar() BEGIN IF NOT EXISTS
  (SELECT *
   FROM information_schema.columns
   WHERE table_schema=database()
     AND TABLE_NAME='tipo_situacao_militar') THEN
CREATE TABLE tipo_situacao_militar (
    tip_situacao_militar INT auto_increment NOT NULL,
    des_tipo_situacao varchar(50),
    ind_excluido INT, PRIMARY KEY (tip_situacao_militar));
END IF; END;

-- Procedure para mudar valor do campo ind_excluido da tabela vinculo_norma_juridica de 0 para string vazia ''
CREATE PROCEDURE muda_vinculo_norma_juridica_ind_excluido() BEGIN
UPDATE vinculo_norma_juridica
SET ind_excluido = ''
WHERE trim(ind_excluido) = '0';
END;

-- Procedure para mudar valor do campo cod_parlamentar da tabela unidade_tramitacao de 0 para string vazia NULL
CREATE PROCEDURE muda_unidade_tramitacao_cod_parlamentar() BEGIN
UPDATE unidade_tramitacao
SET cod_parlamentar = NULL
WHERE cod_parlamentar = 0;
END;

-- Executa as procedures criadas acima
CALL verifica_campos_proposicao;
CALL verifica_campos_tipo_materia_legislativa;
CALL verifica_campos_sessao_plenaria_presenca;
CALL cria_lexml_registro_provedor_e_publicador;
CALL cria_tipo_situacao_militar;
CALL muda_vinculo_norma_juridica_ind_excluido;
CALL muda_unidade_tramitacao_cod_parlamentar;

-- Corrige cod_parlamentar igual a zero em unidade de tramitação
update unidade_tramitacao set cod_parlamentar = NULL where cod_parlamentar = 0;

-- Corrige cod_nivel_instrucao e tip_situacao_militar zero em parlamentar
update parlamentar set cod_nivel_instrucao = NULL where cod_nivel_instrucao = 0;
update parlamentar set tip_situacao_militar = NULL where tip_situacao_militar = 0;

-- Corrige tip_afastamento igual a zero em mandato
update mandato set tip_afastamento = NULL where tip_afastamento = 0;

-- Corrige tip_fim_relatoria igual a zero em relatoria
update relatoria set tip_fim_relatoria = NULL where tip_fim_relatoria = 0;
