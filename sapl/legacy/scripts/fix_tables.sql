-- Apaga as restrições somente para essa sessão
SELECT REPLACE(@@sql_mode,'STRICT_TRANS_TABLES,','ALLOW_INVALID_DATES');
-- Exclui procedures caso já existam
DROP PROCEDURE IF EXISTS verifica_campos_proposicao;
DROP PROCEDURE IF EXISTS verifica_campos_tipo_materia_legislativa;
DROP PROCEDURE IF EXISTS verifica_campos_sessao_plenaria_presenca;
DROP PROCEDURE IF EXISTS cria_lexml_registro_provedor_e_publicador;
DROP PROCEDURE IF EXISTS cria_tipo_situacao_militar;
DROP PROCEDURE IF EXISTS muda_vinculo_norma_juridica_ind_excluido;
-- Procedure para criar campo num_proposicao em proposicao
CREATE PROCEDURE verifica_campos_proposicao() BEGIN IF NOT EXISTS (SELECT * FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='proposicao' AND column_name='num_proposicao') THEN UPDATE proposicao SET dat_envio = '1800-01-01' WHERE CAST(dat_envio AS CHAR(20)) = '0000-00-00 00:00:00'; ALTER TABLE proposicao ADD COLUMN num_proposicao INT(11) NULL after txt_justif_devolucao; END IF; END;
-- Procedure para criar campo iind_num_automatica em tipo_materia_legislativa
CREATE PROCEDURE verifica_campos_tipo_materia_legislativa() BEGIN IF NOT EXISTS (SELECT * FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='tipo_materia_legislativa' AND column_name='ind_num_automatica') THEN ALTER TABLE tipo_materia_legislativa ADD COLUMN ind_num_automatica BOOLEAN NULL DEFAULT FALSE after des_tipo_materia; END IF; IF NOT EXISTS (SELECT * FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='tipo_materia_legislativa' AND column_name='quorum_minimo_votacao') THEN ALTER TABLE tipo_materia_legislativa ADD COLUMN quorum_minimo_votacao INT(11) NULL after ind_num_automatica; END IF; END;
-- Procedure para criar campos cod_presenca_sessao (sendo a nova PK da tabela) e dat_sessao em sessao_plenaria_presenca
CREATE PROCEDURE verifica_campos_sessao_plenaria_presenca() BEGIN IF NOT EXISTS (SELECT * FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='sessao_plenaria_presenca' AND column_name='cod_presenca_sessao') THEN ALTER TABLE sessao_plenaria_presenca DROP PRIMARY KEY, ADD cod_presenca_sessao INT AUTO_INCREMENT PRIMARY KEY FIRST; END IF; IF NOT EXISTS (SELECT * FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='sessao_plenaria_presenca' AND column_name='dat_sessao') THEN ALTER TABLE sessao_plenaria_presenca ADD COLUMN dat_sessao DATE NULL after cod_parlamentar; END IF; END;
-- Procedure para criar tabela lexml_registro_provedor e lexml_registro_publicador
CREATE PROCEDURE cria_lexml_registro_provedor_e_publicador() BEGIN IF NOT EXISTS (SELECT * FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='lexml_registro_publicador') THEN CREATE TABLE lexml_registro_publicador (cod_publicador INT AUTO_INCREMENT NOT NULL, id_publicador INT, nom_publicador VARCHAR(255), adm_email VARCHAR(50), sigla VARCHAR(255), nom_responsavel VARCHAR(255), tipo VARCHAR(50), id_responsavel INT, PRIMARY KEY (cod_publicador)); END IF; IF NOT EXISTS (SELECT * FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='lexml_registro_provedor') THEN CREATE TABLE lexml_registro_provedor (cod_provedor INT AUTO_INCREMENT NOT NULL, id_provedor INT, nom_provedor VARCHAR(255), sgl_provedor VARCHAR(15), adm_email VARCHAR(50), nom_responsavel VARCHAR(255), tipo VARCHAR(50), id_responsavel INT, xml_provedor LONGTEXT, PRIMARY KEY (cod_provedor)); END IF; END;
-- Procedure para criar tabela tipo_situacao_militar
CREATE PROCEDURE cria_tipo_situacao_militar() BEGIN IF NOT EXISTS (SELECT * FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='tipo_situacao_militar') THEN CREATE TABLE tipo_situacao_militar (tip_situacao_militar INT AUTO_INCREMENT NOT NULL, des_tipo_situacao VARCHAR(50), ind_excluido INT, PRIMARY KEY (tip_situacao_militar)); END IF; END;
-- Procedure para mudar valor do campo ind_excluido da tabela vinculo_norma_juridica de 0 para string vazia ''
CREATE PROCEDURE muda_vinculo_norma_juridica_ind_excluido() BEGIN UPDATE vinculo_norma_juridica SET ind_excluido = '' WHERE trim(ind_excluido) = '0'; END;
-- Executa as procedures criadas acima
CALL verifica_campos_proposicao;
CALL verifica_campos_tipo_materia_legislativa;
CALL verifica_campos_sessao_plenaria_presenca;
CALL cria_lexml_registro_provedor_e_publicador;
CALL cria_tipo_situacao_militar;
CALL muda_vinculo_norma_juridica_ind_excluido;
