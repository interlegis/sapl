
#!/bin/sh
# wait until MySQL is really available
maxcounter=${MAX_DB_CONN_ATTEMPTS:-10}
echo "Trying to connect to PostgreSQL, max attempts="$maxcounter
 
counter=1
while ! mysql --host="$DATABASE_URL" --protocol TCP -u"$POSTGRES_USER" -p"$POSTGRES_PASSWORD" -e "show databases;" > /dev/null 2>&1; do
    sleep 1
    counter=`expr $counter + 1`
    if [ $counter -gt $maxcounter ]; then
        >&2 echo "We have been waiting for PostgreSQL too long already; failing."
        exit 1
    fi;
done
echo "-=------------------------------------------------------"
echo "-=------------------------------------------------------"
echo "Connected to PostgreSQL!"
echo "-=------------------------------------------------------"
echo "-=------------------------------------------------------"
