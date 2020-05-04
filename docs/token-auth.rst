1. Realizar o migrate

./manage.py migrate

2. Criar um API Token para usuário e anotar a API Key gerada.

python3 manage.py drf_create_token admin

3. Testar endpoint
curl http://localhost:8000/api/version -H 'Authorization: Token <API Key>'

4. Exemplo de POST
curl -d '{"nome_completo”:”Gozer The Gozerian“, "nome_parlamentar": “Gozer”, "sexo":"M"}' -X POST http://localhost:8000/api/parlamentares/parlamentar/ -H 'Authorization: Token <API Key>' -H 'Content-Type: application/json'

Note: If you use TokenAuthentication in production you must ensure that your API is only available over https.

References: https://www.django-rest-framework.org/api-guide/authentication/#tokenauthentication
