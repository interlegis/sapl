================================
Instruções para instalar o Solr
================================

Solr é a ferramenta utilizada pelo SAPL 3.1 para indexar documentos para que possa ser feita
a Pesquisa Textual. Se a execução for mediante containers Docker então use o arquivo docker-compose.yml disponível em
*https://github.com/interlegis/sapl/blob/3.1.x/solr/docker-compose.yml* (verifique os mapeamentos de volume, e realize o
backup de seu BD antes de qualquer tentativa de substituição do arquivo docker-compose.yml em uso corrente).

1) Faça o download da distribuição _binária_ do Apache Solr do site oficial do projeto *http://lucene.apache.org/solr* ;

As instalações Solr suportadas até o momento vão da 7.4 à 8;

2) Descompacte o arquivo em uma pasta do diretório (referenciada neste tutorial como $SOLR_HOME)

3) Inicie o Solr com o comando:

    **$SOLR_HOME/bin/solr start -c** ;

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
de 'Busca Textual' próximo ao botão de busca tradicional.

**Observações:**

a) Para parar o Solr execute o comando **$SOLR_HOME/bin/solr stop**

b) Para reindexar os dados do SAPL execute o comando `python3 manage.py rebuild_index` (isso irá apagar todos os dados
do Solr e indexar tudo novamente).



