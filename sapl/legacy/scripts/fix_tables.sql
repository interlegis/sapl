-- Apaga as restrições somente para essa sessão
SET SESSION sql_mode = '';
-- Exclui procedures caso já existam
DROP PROCEDURE IF EXISTS verifica_campos_proposicao;
DROP PROCEDURE IF EXISTS verifica_campos_sessao_plenaria_presenca;
DROP PROCEDURE IF EXISTS cria_lexml_registro_provedor_e_publicador;
-- Procedure para criar campo num_proposicao em proposicao
CREATE PROCEDURE verifica_campos_proposicao() BEGIN IF NOT EXISTS (SELECT * FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='proposicao' AND column_name='num_proposicao') THEN ALTER TABLE proposicao ADD COLUMN num_proposicao INT(11) NULL after txt_justif_devolucao; END IF; END;
-- Procedure para criar campos cod_presenca_sessao (sendo a nova PK da tabela) e dat_sessao em sessao_plenaria_presenca
CREATE PROCEDURE verifica_campos_sessao_plenaria_presenca() BEGIN IF NOT EXISTS (SELECT * FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='sessao_plenaria_presenca' AND column_name='cod_presenca_sessao') THEN ALTER TABLE sessao_plenaria_presenca DROP PRIMARY KEY, ADD cod_presenca_sessao INT AUTO_INCREMENT PRIMARY KEY FIRST; END IF; IF NOT EXISTS (SELECT * FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='sessao_plenaria_presenca' AND column_name='dat_sessao') THEN ALTER TABLE sessao_plenaria_presenca ADD COLUMN dat_sessao DATE NULL after cod_parlamentar; END IF; END;
-- Procedure para criar tabela lexml_registro_provedor e lexml_registro_publicador
CREATE PROCEDURE cria_lexml_registro_provedor_e_publicador() BEGIN CREATE TABLE IF NOT EXISTS lexml_registro_publicador (cod_publicador INT AUTO_INCREMENT NOT NULL, id_publicador INT, nom_publicador VARCHAR(255), adm_email VARCHAR(50), sigla VARCHAR(255), nom_responsavel VARCHAR(255), tipo VARCHAR(50), id_responsavel INT, PRIMARY KEY (cod_publicador)); CREATE TABLE IF NOT EXISTS lexml_registro_provedor (cod_provedor INT AUTO_INCREMENT NOT NULL, id_provedor INT, nom_provedor VARCHAR(255), sgl_provedor VARCHAR(15), adm_email VARCHAR(50), nom_responsavel VARCHAR(255), tipo VARCHAR(50), id_responsavel INT, xml_provedor LONGTEXT, PRIMARY KEY (cod_provedor)); END;
-- Executa as procedures criadas acima
CALL verifica_campos_proposicao;
CALL verifica_campos_sessao_plenaria_presenca;
CALL cria_lexml_registro_provedor_e_publicador;
