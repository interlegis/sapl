#!/usr/bin/env bash
# shellcheck disable=SC2086

ajuda_uso() {
  echo -e "\033[33mUso\033[0m: $0 [-h] -f <caminho-do-dump> [-p <porta-do-banco-de-dados>]"
  echo "  -h (Ajuda)"
  echo -e "\tAjuda de uso."
  echo "  -f (Arquivo)"
  echo -e "\tCaminho do arquivo do dump."
  echo -e "\tEx.: ~/Downloads/teste.backup"
  echo "  -p (Porta)"
  echo -e "\tPorta do banco de dados, valor opcional. De 1 até 65535"
  echo -e "\tValor padrão é 5432."
}

valida_parametros() {
  if [[ -z $CAMINHO_DUMP ]]; then
    ajuda_uso
    exit 1
  elif [[ ! -e $CAMINHO_DUMP ]]; then
    echo -e "\033[31mERRO\033[0m  Dump não encontrado com o caminho fornecido!"
    exit 1
  fi

  if [[ -z $PORTA ]]; then
    PORTA="5432"
  elif ! [[ $PORTA =~ ^[0-9]+$ ]] || { [[ $PORTA -lt 1 ]] || [[ $PORTA -gt 65535 ]]; }; then
    ajuda_uso
    exit 1
  fi
}

confirma_operacao() {
  echo -e "\033[33mALERTA\033[0m\t\tEsta operação apagará todo o conteúdo da base de dados atual e restaurará o dump!"
  while ! [[ $ESCOLHA =~ ^[sSyYnN]+$ ]]; do
    read -rp "                Deseja continuar? " ESCOLHA
  done

  [[ $ESCOLHA =~ ^[nN]+$ ]] && exit 0
}

cria_diretorio_restauracoes() {
  echo -e "\n\033[33mEXECUÇÃO\033[0m\tCriando diretório $BASE_DIR/restauracoes/\033[1mrestauracao_${HORARIO}\033[0m ..."
  if mkdir -p $BASE_DIR/restauracoes/restauracao_${HORARIO} &>/dev/null; then
    echo -e "\033[32mSUCESSO\033[0m\t\tDiretório \033[1mrestauracao_${HORARIO}\033[0m criado.\n"
  else
    echo -e "\033[31mERRO\033[0m\t\tNão foi possível criar o diretório \033[1mrestauracao_${HORARIO}\033[0m."
    exit 1
  fi
}

restaura_base_de_dados() {
  echo -e "\033[33mEXECUÇÃO\033[0m  [1/2] Restaurando a base de dados..."

  HAS_SCHEMA_PUBLIC=$(psql $PGURL -tAc "SELECT 1 FROM information_schema.schemata WHERE schema_name='public'")
  if [[ -n $HAS_SCHEMA_PUBLIC ]]; then
    if ! psql $PGURL -c "DROP SCHEMA public CASCADE;"\
          &> $BASE_DIR/restauracoes/restauracao_${HORARIO}/restauracao_$DUMP.log; then
      echo -e "\033[31mERRO\033[0m\t\tHouve um erro no banco de dados."
      exit 1
    fi
  fi

  HAS_ROLE_POSTGRES=$(psql $PGURL -tAc "SELECT 1 FROM pg_roles WHERE rolname='postgres'")
  if [[ -z $HAS_ROLE_POSTGRES ]]; then
    psql $PGURL -c "CREATE ROLE postgres;"\
     >> $BASE_DIR/restauracoes/restauracao_${HORARIO}/restauracao_$DUMP.log 2>&1
  fi

  if ! pg_restore -d $PGURL -e $CAMINHO_DUMP\
      >> $BASE_DIR/restauracoes/restauracao_${HORARIO}/restauracao_$DUMP.log 2>&1; then
    echo -e "\033[31mERRO\033[0m\t\tHouve um erro ao tentar restaurar a base de dados."
    exit 1
  fi
  echo -e "\033[32mSUCESSO\033[0m\t\tRestauração concluida.\n"
}

gera_relatorio_base_de_dados() {
  echo -e "\033[33mEXECUÇÃO\033[0m  [2/2] Criando relatório da base de dados restaurada com \033[1m$DUMP\033[0m..."
  psql $PGURL -P pager=off -c "
    SELECT relname as tabelas,
           n_live_tup as qntd_de_registros
    FROM pg_stat_user_tables
    ORDER BY relname ASC,
             n_live_tup DESC;
  " &> $BASE_DIR/restauracoes/restauracao_${HORARIO}/relatorio_$DUMP.log
  echo -e "\033[32mSUCESSO\033[0m\t\tRelatório concluida.\n"
}

alerta_migracao() {
    echo -e "\033[33mALERTA\033[0m\t\tExecute a migração da base de dados com o comando \033[1mpython3 manage.py migrate\033[0m."
}


HORARIO=$(date +'%Y-%m-%d_%H-%M-%S')

while getopts "h f: p:" opcao; do
  case $opcao in
    h)ajuda_uso
      exit;;
    f)CAMINHO_DUMP="$OPTARG";;
    p)PORTA="$OPTARG";;
    *)ajuda_uso
      exit 1;;
  esac
done

valida_parametros
confirma_operacao

BASE_DIR=${PWD%/scripts}
DUMP=${CAMINHO_DUMP##*/}

PGUSER=${PGUSER:-"sapl"}
PGPASSWORD=${PGPASSWORD:-"sapl"}
PGHOST=${PGHOST:-"localhost"}
PGPORT="$PORTA"
PGDATABASE=${PGDATABASE:-"sapl"}
PGURL="postgresql://$PGUSER:$PGPASSWORD@$PGHOST:$PGPORT/$PGDATABASE"

cria_diretorio_restauracoes
restaura_base_de_dados
gera_relatorio_base_de_dados
alerta_migracao