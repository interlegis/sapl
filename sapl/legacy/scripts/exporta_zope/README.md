# Como exportar o documentos do zope usando

- Crie um diretório base de sua escolha contendo os subdiretórios `datafs` e `repos`. 
  Para usar como <base> o diretório `~/migracao_sapl`, rode os seguintes comandos:

        mkdir -p ~/migracao_sapl/datafs
        mkdir -p ~/migracao_sapl/repos

- Interrompa o serviço do sapl 2.5:

        /var/interlegis/SAPL-2.5/instances/sapl25/bin/zopectl stop

- **Copie** os arquivos `Data.fs` e `DocumentosSapl.fs` de sua instalação de sapl 2.5 para a pasta `<base>/datafs`, 
  renomenado os arquivos para que terminem com `_cm_<sigla-da-sua-casa>.fs`.
  Se não sabe a sigla de sua casa pode usar `zzz`.
  Se seus arquivos estão em `/var/interlegis/SAPL-2.5/instances/sapl25/var`:
  
        cd /var/interlegis/SAPL-2.5/instances/sapl25/var
        cp Data.fs ~/migracao_sapl/datafs/Data_cm_zzz.fs
        cp DocumentosSapl.fs ~/migracao_sapl/datafs/DocumentosSapl_cm_zzz.fs

- A estrutura obtida deve ser a seguinte:

        migracao_sapl/
        ├── datafs
        │   ├── Data_cm_zzz.fs
        │   └── DocumentosSapl_cm_zzz.fs
        └── repos

- Reinicie o serviço do sapl 2.5 (após concluída a cópia e antes de continuar o processo):

        /var/interlegis/SAPL-2.5/instances/sapl25/bin/zopectl start

- Instale o Docker (https://docs.docker.com/install)

- Se desejar usar os comandos do docker sem um usuário root siga os passos de
    https://docs.docker.com/install/linux/linux-postinstall/#manage-docker-as-a-non-root-user

- Clone o repo do sapl e construa a imagem docker do diretório `sapl/legacy/scripts/exporta_zope`:

        cd ~
        git clone git@github.com:interlegis/sapl.git
        cd ~/sapl/sapl/legacy/scripts/exporta_zope
        docker build -t exporta_zope .

- Rode o comando de exportação da imagem `exporta_zope` construída:

        docker run -it -v ~/migracao_sapl:/root/migracao_sapl exporta_zope ./exporta_zope.py zzz

- Se a exportação for concluída com sucesso vc deve ter uma nova pasta com os dados em `~/migracao_sapl/repos/sapl_cm_zzz`

- Trate com segurança os dados exportados, pois eles não tem mais nenhum controle de acesso como no zope.
  Especialmente o arquivo `usuarios.yaml` conterá todos os nomes de usuários e hashs de suas senhas em texto aberto.
  Os textos integrais de todas as proposições também devem ter sido exportados em aberto.
  Ao completarmos a migração reimportando estes arquivos para o sapl 3.1 os controles de acesso serão restabelecidos.
