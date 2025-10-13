
# Websockets 

Rodar o container antes de iniciar o SAPL:
    
```commandline
    sudo docker run --rm -p 6379:6379 redis:7-alpine redis-server --save "" --appendonly no
```

Executar o SAPL

Instalar dependências do Websockets e Redis:
   
```commandline
    pip install -r requirements/dev-requirements.txt
```

Abrir um terminal e rodar `yarn` para servir as páginas VueJS:
    
```commandline
    yarn serve
```
    
Executar o SAPL (duas formas):

DAPHNE:

Em outro terminal, no diretório raiz, execute como Daphne abaixo:
```commandline
    daphne -b 127.0.0.1 -p 8000 sapl.asgi:application
```

Daphne é excelente para debugar a parte de WebSockets, pois contém melhores mensagens de erro e log.
O runserver geralmente só vai dar crash ou falhar ao enviar as mensagens via WebSocket.

**MAS atenção: Daphne não faz reload automático após mudanças na página!**

Para isso é que parar e reiniciar o Daphne ou usar `.manage.py runserver`


RUNSERVER:
Em outro terminal, no diretório raiz, execute como Daphne abaixo para debugar os websockets (melhores mensagens de log)
```commandline
    ./manage.py runserver
``` 

Logar no SAPL e acessar a página `http://localhost:8000/painel/v2`


Ferramentas:

`wscat`: permite fazer chamadas a websockets via CLI, mas para acessar o WS endpoint do painel precisa estar autenticado.
 
**Redis Insight:** GUI que é tipo um pgAdmin para o Redis;
