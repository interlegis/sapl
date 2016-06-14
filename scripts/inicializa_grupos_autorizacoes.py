from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


def cria_grupos_permissoes():

    if not Group.objects.filter("Teste"):
        pass

    # Cria todos os grupos necessários para a aplicação

    if not Group.objects.filter(name="Operador Geral").exists():
        op_geral = Group.objects.create(name="Operador Geral")
    else:
        op_geral = Group.objects.get(name="Operador Geral")

    if not Group.objects.filter(name="Operador de Protocolo").exists():
        op_prot = Group.objects.create(name="Operador de Protocolo")
    else:
        op_prot = Group.objects.get(name="Operador de Protocolo")

    if not Group.objects.filter(name="Operador de Sessão").exists():
        op_sessao = Group.objects.create(name="Operador de Sessão")
    else:
        op_sessao = Group.objects.get(name="Operador de Sessão")

    if not Group.objects.filter(name="Operador de Comissão").exists():
        op_comissao = Group.objects.create(name="Operador de Comissão")
    else:
        op_comissao = Group.objects.get(name="Operador de Comissão")

    if not Group.objects.filter(name="Operador de Administração").exists():
        op_adm = Group.objects.create(name="Operador de Administração")
    else:
        op_adm = Group.objects.get(name="Operador de Administração")

    if not Group.objects.filter(name="Operador de Norma Jurídica").exists():
        op_norma = Group.objects.create(name="Operador de Norma Jurídica")
    else:
        op_norma = Group.objects.get(name="Operador de Norma Jurídica")

    if not Group.objects.filter(name="Operador de Matéria Legislativa").exists():
        op_materia = Group.objects.create(
            name="Operador de Matéria Legislativa")
    else:
        op_materia = Group.objects.get(name="Operador de Matéria Legislativa")

    if not Group.objects.filter(name="Autor").exists():
        op_autor = Group.objects.create(name="Autor")
    else:
        op_autor = Group.objects.get(name="Autor")

    # Base

    permissao_add_cl = Permission.objects.get(
        name="Can add Casa Legislativa")
    permissao_edit_cl = Permission.objects.get(
        name="Can change Casa Legislativa")
    permissao_remove_cl = Permission.objects.get(
        name="Can delete Casa Legislativa")

    permissoes_base = [permissao_add_cl,
                       permissao_edit_cl,
                       permissao_remove_cl]

    # Comissao

    cts = ContentType.objects.filter(app_label='comissoes')
    perms_comissoes = list(Permission.objects.filter(content_type__in=cts))

    # Materia

    cts = ContentType.objects.filter(app_label='materia')
    perms_materia = list(Permission.objects.filter(content_type__in=cts))

    # Norma

    cts = ContentType.objects.filter(app_label='norma')
    perms_norma = list(Permission.objects.filter(content_type__in=cts))

    # Painel

    cts = ContentType.objects.filter(app_label='painel')
    perms_painel = list(Permission.objects.filter(content_type__in=cts))

    # Parlamentares

    cts = ContentType.objects.filter(app_label='parlamentares')
    perms_parlamentares = list(Permission.objects.filter(content_type__in=cts))

    # ProtocoloADM e DOCADM

    cts = ContentType.objects.filter(app_label='protocoloadm')

    perms_docadm = list(Permission.objects.filter(content_type__in=cts))

    cts_exc1 = cts.filter(model__icontains='tramitacao')
    cts_exc2 = cts.filter(model__icontains='documentoadministrativo')

    cts = cts.exclude(id__in=[o.id for o in cts_exc1])
    cts = cts.exclude(id__in=[o.id for o in cts_exc2])

    perms_protocoloadm = list(Permission.objects.filter(content_type__in=cts))

    # Sessao

    cts = ContentType.objects.filter(app_label='sessao')
    perms_sessao = list(Permission.objects.filter(content_type__in=cts))

    # Autor

    perms_autor = Permission.objects.get(name="Can add Proposição")

    # Configura Permissoes Operador de Protocolo
    for p in perms_protocoloadm:
        op_prot.permissions.add(p)

    # Configura Permissoes Operador de Sessao
    for p in perms_sessao:
        op_sessao.permissions.add(p)

    # Configura Permissoes Operador de Comissao
    for p in perms_comissoes:
        op_comissao.permissions.add(p)

    # Configura Permissoes Operador de Administracao
    for p in perms_docadm:
        op_adm.permissions.add(p)

    # Configura Permissoes Operador de Norma
    for p in perms_norma:
        op_norma.permissions.add(p)

    # Configura Permissoes Operador de Materia
    for p in perms_materia:
        op_materia.permissions.add(p)

    # Configura Permissoes Autor
    op_autor.permissions.add(perms_autor)

    # Configura Permissoes Operador Geral
    perms_op_geral = perms_protocoloadm + perms_sessao + perms_comissoes
    perms_op_geral = perms_op_geral + perms_docadm + perms_norma
    perms_op_geral = perms_op_geral + perms_materia
    perms_op_geral = perms_op_geral + perms_parlamentares + perms_painel
    perms_op_geral = perms_op_geral + permissoes_base

    for p in perms_op_geral:
        op_geral.permissions.add(p)
    op_geral.permissions.add(perms_autor)

if __name__ == '__main__':
    cria_grupos_permissoes()
