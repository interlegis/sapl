set -e  # Exit immediately if a command exits with a non-zero status

echo $HOME
echo "Database $1"
sudo -u postgres psql -c "drop DATABASE if exists $1"
sudo -u postgres psql -c "CREATE DATABASE $1 WITH OWNER = sapl ENCODING = 'UTF8' TABLESPACE = pg_default LC_COLLATE = 'pt_BR.UTF-8' LC_CTYPE = 'pt_BR.UTF-8' CONNECTION LIMIT = -1 TEMPLATE template0;"

sudo -u postgres pg_restore -d $1 -U postgres "$HOME/migracao_sapl/dumps_producao/$1.prod"

