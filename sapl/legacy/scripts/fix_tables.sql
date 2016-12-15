DROP PROCEDURE IF EXISTS verifica_campos;
CREATE PROCEDURE verifica_campos() BEGIN IF NOT EXISTS (SELECT * FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='proposicao' AND column_name='num_proposicao') THEN ALTER TABLE proposicao add column num_proposicao int(11) NULL after txt_justif_devolucao; END IF; END;
CALL verifica_campos;
