import json
from django.contrib.auth import get_user_model
from datetime import datetime
from django.core.serializers.json import DjangoJSONEncoder


# Função para tratar a serialização de objetos datetime
class CustomJSONEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


# Receber o nome do usuário como parâmetro
nome_usuario = input("Digite o nome do usuário: ")

# Encontrar o usuário
User = get_user_model()
try:
    usuario = User.objects.get(username=nome_usuario)
except User.DoesNotExist:
    print(f"Usuário '{nome_usuario}' não encontrado.")
    exit()

# Encontrar o autor relacionado
try:
    autor = OperadorAutor.objects.get(user=usuario).autor
except OperadorAutor.DoesNotExist:
    print(f"Nenhum autor encontrado para o usuário '{nome_usuario}'.")
    exit()

# Buscar proposições não recebidas criadas por esse autor
proposicoes = Proposicao.objects.filter(autor=autor, data_recebimento__isnull=True)

# Exibir a quantidade de registros
print(f"Total de proposições encontradas: {proposicoes.count()}")

# Opção para imprimir todas as proposições filtradas
if input("Deseja imprimir todas as proposições? (s/n): ").lower() == 's':
    for proposicao in proposicoes:
        print(proposicao)

# Escolha para proceder com a deleção
if input("Deseja proceder com a deleção das proposições? (s/n): ").lower() == 's':
    # Backup dos dados com a customização para datetime
    dados_backup = list(proposicoes.values())
    with open('backup_proposicoes.json', 'w') as file:
        json.dump(dados_backup, file, cls=CustomJSONEncoder)

    # Deletar as proposições
    num_proposicoes = proposicoes.count()
    proposicoes.delete()

    print(f"{num_proposicoes} proposições foram deletadas. Backup realizado em 'backup_proposicoes.json'.")
else:
    print("Deleção cancelada.")
