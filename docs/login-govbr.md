# Login gov.br no SAPL

Este documento registra a integração do SAPL com o Login Único gov.br por
OpenID Connect. Ele serve como referência para revisar, publicar no GitHub da
equipe e depois espelhar a alteração no repositório de produção
`Camara-Indaiatuba/SAPL.git`.

## Escopo da alteração

- adiciona o cliente OIDC gov.br em `sapl/base/govbr.py`;
- expõe as rotas `/login/govbr/`, `/auth/govbr/callback/` e a rota legada
  `/login/govbr/callback/`;
- exibe o botão "Entrar com GOV.BR" na tela de login apenas quando a integração
  está habilitada;
- valida `state`, `nonce`, assinatura RS256 via JWK, `audience` e `issuer`;
- resolve o usuário local pelo CPF retornado pelo gov.br, procurando por
  `username` por padrão e opcionalmente por e-mail verificado;
- permite criação automática de usuário quando `GOVBR_AUTO_CREATE_USERS=True`;
- redireciona o logout para o encerramento da sessão gov.br quando a sessão foi
  autenticada por esse provedor;
- adiciona `requests` e `PyJWT[crypto]` como dependências de runtime;
- adiciona testes para renderização do botão, início do fluxo OIDC e resolução
  do usuário por CPF.

## Variáveis de ambiente

As variáveis abaixo ficam em `sapl/settings.py` e podem ser configuradas no
`.env`, Docker Compose ou ambiente de produção.

```env
GOVBR_LOGIN_ENABLED=True
GOVBR_SSO_BASE_URL=https://sso.staging.acesso.gov.br
GOVBR_CLIENT_ID=<client-id-fornecido-pelo-govbr>
GOVBR_CLIENT_SECRET=<client-secret-fornecido-pelo-govbr>
GOVBR_SCOPE=openid email profile govbr_confiabilidades govbr_confiabilidades_idtoken
GOVBR_REDIRECT_URI=https://sapl.indaiatuba.tec.br/auth/govbr/callback/
GOVBR_POST_LOGOUT_REDIRECT_URI=https://sapl.indaiatuba.tec.br
GOVBR_USER_LOOKUP_FIELDS=username
GOVBR_AUTO_CREATE_USERS=False
```

Variáveis avançadas, úteis se o gov.br entregar URLs específicas junto com a
credencial:

```env
GOVBR_ISSUER=
GOVBR_AUTHORIZE_URL=
GOVBR_TOKEN_URL=
GOVBR_JWK_URL=
GOVBR_LOGOUT_URL=
GOVBR_REQUEST_TIMEOUT=10
GOVBR_JWT_LEEWAY=30
GOVBR_STATE_MAX_AGE=600
```

Para homologação, o valor padrão de `GOVBR_SSO_BASE_URL` aponta para
`https://sso.staging.acesso.gov.br`. Em produção, confirmar a URL final no
cadastro da credencial gov.br antes de ativar a integração.

## Cadastro da aplicação no gov.br

Solicitar credenciais de teste/homologação e produção no Serviço de Integração
aos Produtos do Ecossistema da Identidade Digital GOV.BR.

Cadastrar pelo menos estas URLs na credencial:

```text
Redirect URI: https://sapl.indaiatuba.tec.br/auth/govbr/callback/
URL de logout: https://sapl.indaiatuba.tec.br
```

O roteiro técnico gov.br exige HTTPS para o fluxo de autenticação e recomenda
domínio oficial de governo para credenciais de produção.

## Vínculo com usuários locais

Por padrão, o SAPL procura uma conta local cujo `username` seja o CPF retornado
pelo gov.br, aceitando CPF apenas com dígitos ou no formato `000.000.000-00`.

Para procurar também por e-mail verificado:

```env
GOVBR_USER_LOOKUP_FIELDS=username,email
```

Use `GOVBR_AUTO_CREATE_USERS=True` somente se a criação automática já estiver
aprovada pela regra operacional da Câmara. Usuários criados automaticamente ficam
sem senha local utilizável e usam o CPF como `username`.

## Checklist para produção

1. Abrir uma branch dedicada a partir de `3.1.x`.
2. Incluir somente os arquivos do escopo gov.br no commit.
3. Configurar as variáveis no ambiente de produção, sem versionar segredo.
4. Garantir que os usuários locais que usarão gov.br tenham `username` igual ao
   CPF, ou ajustar `GOVBR_USER_LOOKUP_FIELDS`.
5. Executar migrações existentes do SAPL, se houver pendência do ambiente.
6. Executar `python manage.py check`.
7. Executar `pytest sapl/base/tests/test_login.py -q`.
8. Validar manualmente a tela `/login/`, o redirecionamento para gov.br e o
   retorno em `/auth/govbr/callback/`.
9. Publicar a branch no GitHub da equipe.
10. Abrir PR para `Camara-Indaiatuba/SAPL.git`, base `3.1.x`, descrevendo
    configuração, impacto e validações.

## Referências

- Roteiro técnico gov.br: https://acesso.gov.br/roteiro-tecnico/iniciarintegracao.html
- Solicitação de credencial gov.br: https://acesso.gov.br/roteiro-tecnico/solicitacaocredencialprocesso.html
- pytest-django 4.5.2: https://pypi.org/project/pytest-django/4.5.2/
