================================
Instruções para instalar o Solr
================================

**O servidor do Solr NÃO DEVE SER EXPOSTO NA INTERNET. Assim como o servidor de bancos de dados Postgres ele deve estar acessível pelo SAPL na rede interna (atrás de NATs/firewalls/proxies/etc).**

Solr é uma plataforma open source de indexação e busca textual utilizada pelo SAPL 3.1 para indexar documentos (normas jurídicas, matérias legislativas e documentos acessórios). 

Observação: Se a execução do SAPL for mediante containers Docker então use o arquivo *docker-compose.yml* disponível em
*https://github.com/interlegis/sapl/blob/3.1.x/dist/docker-compose.yml* (verifique os mapeamentos de volume estão corretos, a verso do SAPL referenciada no arquivo docker-compose.yml, e realize o backup de seu BD **antes** de qualquer tentativa de substituição do arquivo *docker-compose.yml* em uso corrente);

1) Faça o download da distribuição *binária* do Apache Solr do site oficial do projeto **http://lucene.apache.org/solr**


   As instalações Solr suportadas até o momento vão da 7.4 à 8;


2) Descompacte o arquivo em uma pasta do diretório (referenciada neste tutorial como $SOLR_HOME)


3) Inicie o Solr com o comando:

    **$SOLR_HOME/bin/solr start -c** 
    

4) Por meio do browser, acesse a URL **http://localhost:8983** (ou informe o endereço da máquina onde o Solr foi instalado)

5) Pare o servidor do SAPL;

6) Edite o arquivo .env adicionando as seguintes linhas:

    USE_SOLR = True


    SOLR_COLLECTION = sapl


    SOLR_URL = http://localhost:8983


 (o valor do campo SOLR_URL deve corresponder à URL acessada no item 3)

7) Entre no diretório raiz do SAPL e digite o comando: **python3 solr_api.py -c sapl -u http://localhost:8983`**

    (a URL informada acima deve ser a mesma dos itens 3 e 6)

8) Enquanto o Solr realiza a indexação da base de dados do SAPL, inicie em uma outra tela o SAPL;

9) Após realizados os passos com sucesso, nas telas de busca de Matéria Legislativa e Normas deverá aparecer um botão
de 'Pesquisa Textual' na tela de busca tradicional.

**Observações:**

* Para parar o Solr execute o comando **$SOLR_HOME/bin/solr stop**


* Comandos de manutenção da base textual do Solr:

1. **python3 manage.py rebuild_index** : Apaga os dados da coleção `sapl` no Solr e reindexa tudo do início;

2. **python3 manage.py clear_index** : Apaga todos os dados da coleção `sapl` do Solr. **Este comando não irá apagar os dados do BD Postgres, somente os dados do Solr serão apagados.**

3. **python3 manage.py update_index** : atualiza os dados do Solr:

3.1. **python3 manage.py update_index --remove** : remove objetos do Solr que não mais existem no BD Postgres (no caso do Postgres e Solr derem dessincronizados).

3.2. **python3 manage.py update_index --age <N>** : reindexa os documentos inseridos/alterados nas últimas <N> horas;

3.3. **python3 manage.py update_index -s YYYY-MM-DDTHH:MM:SS -e YYYY-MM-DDTHH:MM:SS** : reindexa os documentos que foram inseridos/atualizados entre a data inicial (-s) e a data final (-e). Ambos os argumentos de início e fim são opcionais.


### FAQ 

1. Uma dúvida quanto a indexação do Solr, pelo que entendi de tempos e tempos tenho que rodar o comando para poder indexar novos arquivos certo?

   Errado. Cada novo documento inserido, atualizado, ou removido do SAPL dispara uma nova indexação somente daquele documento no Solr automaticamente.

2. O comando **python3 solr_api.py -c sapl -u http://localhost:8983** indexa os novos arquivos?

   Não. Este comando é para construir a coleção do Solr a primeira vez e, por acaso, faz a indexação inicial. Não deve ser usado se a coleção já foi criada.

3. Ou teria que reindexar do zero com *rebuild_index*?

   Pode acontecer do Postgres e o Solr se dessincronizarem (ex: o Solr ficou fora do ar por um dia e foram inseridos registros no SAPL). Ou por algum motivo se deseja refazer o índice do Solr. Neste caso pode-se refazer a indexação no Solr com o comando : **python3 manage.py rebuild_index** (direto na linha de comando, a partir da pasta raiz do SAPL). Mas existem maneiras de atualizar somente os documentos inseridos/alterados a partir de uma determinada data ao invés de atualizar tudo do zero de novo.

4. Pergunto isso pois estou querendo criar um script para crontab para indexar esses novos arquivos

Desnecessário.
