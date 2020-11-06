# Ambiente de Desenvolvimento

### Tópicos

* [Rodar Docker Compose](#Rodar-Docker-Compose)
* [Configurar Banco de Dados PostgreSQL instalado na máquina](#Configurar-Banco-de-Dados-PostgreSQL-instalado-na-máquina)
* [Restaurar uma Base de Dados](#Restaurar-Base-de-Dados)

##### A configuração do banco de dados e restauração da base de dados só devem ser feitas na primeira vez.


## Rodar Docker Compose
Para rodar o docker compose sem o conteiner postgresql, vá ao terminal e execute o comando:
```shell
docker-compose -f docker/docker-compose-dev.yml up
```
Se quiser com o conteiner postgresql, execute o comando:
```shell
docker-compose -f docker/docker-compose-dev-db.yml up
```

## Configurar Banco de Dados PostgreSQL instalado na máquina
A configuração do banco de dados só é necessário com o postgresql na máquina local. Para configurá-lo, vá ao terminal e execute os comandos a seguir para criar o usuário "sapl", senha "sapl" e a base de dados "sapl":
```shell
sudo -u postgres psql -c "CREATE ROLE sapl LOGIN ENCRYPTED PASSWORD 'sapl' NOSUPERUSER INHERIT CREATEDB NOCREATEROLE NOREPLICATION;"

sudo -u postgres psql -c "ALTER ROLE sapl VALID UNTIL 'infinity';"

sudo -u postgres psql -c "CREATE DATABASE sapl WITH OWNER = sapl ENCODING = 'UTF8' TABLESPACE = pg_default LC_COLLATE = 'pt_BR.UTF-8' LC_CTYPE = 'pt_BR.UTF-8' CONNECTION LIMIT = -1 TEMPLATE template0;"
```
Depois do banco de dados ter sido configurado, [restaure alguma base de dados](#Restaurar-Base-de-Dados).

## Restaurar Base de Dados
No termianal, rode o comando no diretório raiz do projeto passando como parâmetro o caminho do backup:
```shell
./scripts/restore_db.sh -f <caminho-do-dump>
```
Se o postgres estiver rodando no container, adicione a _flag_ "-p 5433":
```shell
./scripts/restore_db.sh -f <caminho-do-dump> -f 5433
```
