================================
Instruções para instalar o Solr
================================

Solr é a ferramenta utilizada pelo SAPL 3.1 para indexar documentos para que possa ser feita
a Pesquisa Textual.


Dentro do diretório principal siga os seguintes passos::

   curl -LO https://archive.apache.org/dist/lucene/solr/4.10.2/solr-4.10.2.tgz
   tar xvzf solr-4.10.2.tgz
   cd solr-4.10.2
   cd example
   java -jar start.jar
   ./manage.py build_solr_schema --filename solr-4.10.2/example/solr/collection1/conf/schema.xml


Após isso, deve-se parar o servidor do Solr e restartar com ``java -jar start.jar``


``**OBS: Toda vez que o código da pesquisa textual for modificado, os comandos de build_solr_schema e start.jar devem ser rodados, nessa mesma ordem.**``