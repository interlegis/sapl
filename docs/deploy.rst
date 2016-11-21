==============================
Instruções para fazer o Deploy
==============================

Para efeitos deste doc, foram consideradas as tecnologias NGINX + GUNICORN para servir a aplicação Django SAPL.

O NGINX é o servidor WEB, e o GUNICORN é o servidor da aplicação para o servidor WEB.

   
Instalar o NGINX::

  sudo pip install nginx
  
  
Instalar o Gunicorn::

  sudo pip install gunicorn  


Preparando o NGINX
------------------
vi /etc/nginx/sites-available/sapl31::

   upstream ENDERECO_SITE {  
      server unix:~/sapl/run/gunicorn.sock fail_timeout=0;
   }

   server {

       listen   80;
       server_name ENDERECO_SITE;

       client_max_body_size 4G;

       access_log /var/log/nginx-access.log;
       error_log /var/log/nginx-error.log;

       location /static/ {
           alias   ~/sapl/collected_static/;
       }

       location /media/ {
           alias   ~/sapl/media/;
       }

       location / {
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header Host $http_host;
           proxy_redirect off;
           if (!-f $request_filename) {
               proxy_pass http://ENDERECO_SITE;
               break;
           }
       }

       # Error pages
       error_page 500 502 503 504 /500.html;
       location = /500.html {
           root ~/sapl/sapl/static/;
       }
   }


Criar link simbólico para ativar o site::

   sudo ln -s /etc/nginx/sites-available/sapl3.conf /etc/nginx/sites-enabled/sapl3



Preparando o Gunicorn
---------------------
Na raiz do Projeto sapl, existe o arquivo chamado gunicorn_start.sh
onde ~/ devem ser alterados pelos caminhos correspondentes.

Para definir o parametro NUM_WORKERS  utilize a seguinte fórmula: 2 * CPUs  1.
Para uma máquina de CPU única o valor seria 3

Para dar Permissão de execução para o script::

   chmod ux bin/gunicorn_start

Para rodar o gunicorn::
   
   ./~/.gunicorn_start.sh
   
   
   
#Referências.

http://michal.karzynski.pl/blog/2013/06/09/django-nginx-gunicorn-virtualenv-supervisor/

Para multiplas aplicações Django.

http://michal.karzynski.pl/blog/2013/10/29/serving-multiple-django-applications-with-nginx-gunicorn-supervisor/
   
