
export DATABASE_NAME=sapl_cm_$1

echo $DATABASE_NAME
/home/mazza/work/sapl/sapl/legacy/scripts/restaura_da_producao.sh $DATABASE_NAME
./manage.py tenta_correcao --settings=sapl.legacy_migration_settings
