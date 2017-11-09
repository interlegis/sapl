import mysql.connector # dep: mysql-connector-python-rf

def migra_autor(db, passwd):
  connection = mysql.connector.connect(user='root', database=db, passwd=passwd)
  cursor = connection.cursor(buffered=True)
  query = ("select cod_parlamentar, COUNT(*) \
      from {}.autor where col_username is not null \
      group by col_username, cod_parlamentar \
      having 1 < COUNT(*) \
      order by cod_parlamentar asc;").format(db)

  cursor.execute(query)

  all_authors = []
  for response in cursor:
    if response[0] is not None:
      all_authors.append(response)


  for author in all_authors:
    query2 = ("select * from {}.autor \
    where cod_parlamentar = " + str(author[0]) + " \
    group by cod_autor;").format(db)
    cursor.execute(query2)
    user = []
    for response in cursor:
      user.append(response)

    ativ = []
    inativ = []
    for tupl in user:
      if tupl[8] == 1:
        inativ.append(tupl)
      elif tupl[8] == 0:
        ativ.append(tupl)


    tables = ['autoria', 'documento_administrativo', 'proposicao', 'protocolo']
    for table in tables:
      query3 = ("UPDATE {}.{} SET cod_autor = {} WHERE cod_autor in ").format(db, table, ativ[0][0])
      inativIds = [u[0] for u in inativ]
      inativIds = (str(inativIds)).replace(']', ')').replace('[', '(')
      query3 += inativIds

      cursor.execute(query3)
      