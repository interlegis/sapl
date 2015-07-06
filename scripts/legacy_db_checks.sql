-- These queries should return no results (or zero when counting)
select count(*) from sessao_plenaria s join expediente_materia e on s.cod_sessao_plen = e.cod_sessao_plen where s.dat_inicio_sessao != e.dat_ordem ;
select s.cod_sessao_plen, s.dat_inicio_sessao, e.dat_ordem from sessao_plenaria s join ordem_dia e on s.cod_sessao_plen = e.cod_sessao_plen where s.dat_inicio_sessao != e.dat_ordem ;
select s.cod_sessao_leg, m.* from mesa_sessao_plenaria m join sessao_plenaria s on m.cod_sessao_plen = s.cod_sessao_plen where m.cod_sessao_leg != s.cod_sessao_leg;
