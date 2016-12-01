==============================
Instruções para fazer o Deploy
==============================

Para efeitos deste doc, foram consideradas as tecnologias NGINX + GUNICORN para servir a aplicação Django SAPL.

O NGINX é o servidor WEB, e o GUNICORN é o servidor da aplicação para o servidor WEB.

   
Instalar o NGINX::

  sudo apt-get install nginx
  
  
Instalar o Gunicorn::

  sudo pip install gunicorn  


Preparando o NGINX
------------------
sudo nano /etc/nginx/sites-available/sapl31.conf::

   upstream ENDERECO_SITE {  
      server unix:/var/interlegis/sapl/run/gunicorn.sock fail_timeout=0;
   }

   server {

       listen   80;
       server_name ENDERECO_SITE;

       client_max_body_size 4G;

       access_log /var/log/nginx-access.log;
       error_log /var/log/nginx-error.log;

       location /static/ {
           alias   /var/interlegis/sapl/collected_static/;
       }

       location /media/ {
           alias   /var/interlegis/sapl/media/;
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
           root /var/interlegis/sapl/sapl/static/;
       }
   }


Criar link simbólico para ativar o site::

   sudo ln -s /etc/nginx/sites-available/sapl31.conf /etc/nginx/sites-enabled/sapl3

Reiniciar o nginx

   sudo service nginx restart


Preparando o Gunicorn
---------------------
Na raiz do Projeto sapl, existe o arquivo chamado gunicorn_start.sh

Para definir o parametro NUM_WORKERS  utilize a seguinte fórmula: 2 * CPUs  1.
Para uma máquina de CPU única o valor seria 3


Para rodar o gunicorn::
   workon sapl
   
   /var/interlegis/sapl/.gunicorn_start.sh
   
   
   
#Referências.

http://michal.karzynski.pl/blog/2013/06/09/django-nginx-gunicorn-virtualenv-supervisor/

Para multiplas aplicações Django.

http://michal.karzynski.pl/blog/2013/10/29/serving-multiple-django-applications-with-nginx-gunicorn-supervisor/
   
