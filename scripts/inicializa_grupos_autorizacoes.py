from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


def cria_grupos_permissoes():

    if not Group.objects.filter("Teste"):
        pass

    # Cria todos os grupos necessários para a aplicação

    op_geral = Group.objects.get_or_create(name="Operador Geral")
    op_prot = Group.objects.get_or_create(name="Operador de Protocolo")
    op_sessao = Group.objects.get_or_create(name="Operador de Sessão")
    op_comissao = Group.objects.get_or_create(name="Operador de Comissão")
    op_adm = Group.objects.get_or_create(name="Operador de Administração")
    op_norma = Group.objects.get_or_create(name="Operador de Norma Jurídica")
    op_materia = Group.objects.get_or_create(name="Operador de Matéria Legislativa")
    op_autor = Group.objects.get_or_create(name="Autor")

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
