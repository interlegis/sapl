import base64
import hashlib
import json
import logging
import secrets
import time
from urllib.parse import urlencode

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.crypto import constant_time_compare


logger = logging.getLogger(__name__)

GOVBR_SESSION_KEY = 'govbr_oidc'
GOVBR_AUTH_SESSION_KEY = 'govbr_authenticated'


class GovBrAuthError(Exception):
    pass


def govbr_login_enabled():
    return bool(getattr(settings, 'GOVBR_LOGIN_ENABLED', False))


def build_absolute_uri(request, configured_uri, view_name):
    if configured_uri:
        return configured_uri

    from django.urls import reverse

    return request.build_absolute_uri(reverse(view_name))


def is_truthy(value):
    if isinstance(value, bool):
        return value
    return str(value).lower() in ('1', 'true', 't', 'yes', 'y', 'sim')


def clean_cpf(value):
    cpf = ''.join(ch for ch in str(value or '') if ch.isdigit())
    if len(cpf) == 11:
        return cpf
    return ''


def cpf_variants(cpf):
    if not cpf:
        return []
    return [
        cpf,
        '{}.{}.{}-{}'.format(cpf[:3], cpf[3:6], cpf[6:9], cpf[9:]),
    ]


def get_lookup_fields():
    fields = getattr(settings, 'GOVBR_USER_LOOKUP_FIELDS', ('username',))
    if isinstance(fields, str):
        fields = fields.replace(';', ',').split(',')
    return tuple(field.strip() for field in fields if field.strip())


def _base64url(value):
    return base64.urlsafe_b64encode(value).rstrip(b'=').decode('ascii')


def new_code_verifier():
    return _base64url(secrets.token_bytes(64))


def code_challenge_from_verifier(code_verifier):
    digest = hashlib.sha256(code_verifier.encode('ascii')).digest()
    return _base64url(digest)


class GovBrClient:

    def __init__(self, http_session=None):
        self.http = http_session or requests.Session()

    @property
    def base_url(self):
        return getattr(settings, 'GOVBR_SSO_BASE_URL', '').rstrip('/')

    @property
    def issuer(self):
        configured_issuer = getattr(settings, 'GOVBR_ISSUER', '')
        return configured_issuer or '{}/'.format(self.base_url)

    @property
    def authorize_url(self):
        return (
            getattr(settings, 'GOVBR_AUTHORIZE_URL', '') or
            '{}/authorize'.format(self.base_url)
        )

    @property
    def token_url(self):
        return (
            getattr(settings, 'GOVBR_TOKEN_URL', '') or
            '{}/token'.format(self.base_url)
        )

    @property
    def jwk_url(self):
        return (
            getattr(settings, 'GOVBR_JWK_URL', '') or
            '{}/jwk'.format(self.base_url)
        )

    @property
    def logout_url(self):
        return (
            getattr(settings, 'GOVBR_LOGOUT_URL', '') or
            '{}/logout'.format(self.base_url)
        )

    @property
    def timeout(self):
        return getattr(settings, 'GOVBR_REQUEST_TIMEOUT', 10)

    def authorization_url(self, redirect_uri, state, nonce, code_verifier):
        params = {
            'response_type': 'code',
            'client_id': settings.GOVBR_CLIENT_ID,
            'scope': settings.GOVBR_SCOPE,
            'redirect_uri': redirect_uri,
            'nonce': nonce,
            'state': state,
            'code_challenge': code_challenge_from_verifier(code_verifier),
            'code_challenge_method': 'S256',
        }
        return '{}?{}'.format(self.authorize_url, urlencode(params))

    def exchange_code(self, code, redirect_uri, code_verifier):
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': redirect_uri,
            'code_verifier': code_verifier,
        }
        try:
            response = self.http.post(
                self.token_url,
                auth=(settings.GOVBR_CLIENT_ID, settings.GOVBR_CLIENT_SECRET),
                data=data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.exception('Erro ao trocar code do gov.br por tokens.')
            raise GovBrAuthError(
                'Não foi possível concluir a autenticação no gov.br.') from exc

        try:
            return response.json()
        except ValueError as exc:
            raise GovBrAuthError('Resposta inválida recebida do gov.br.') from exc

    def validate_tokens(self, token_response, nonce):
        access_token = token_response.get('access_token')
        id_token = token_response.get('id_token')

        if not access_token or not id_token:
            raise GovBrAuthError(
                'Resposta do gov.br não retornou os tokens esperados.')

        access_claims = self.decode_token(access_token)
        id_claims = self.decode_token(id_token)

        if not constant_time_compare(str(id_claims.get('nonce') or ''), nonce):
            raise GovBrAuthError('Nonce inválido no retorno do gov.br.')

        return id_claims, access_claims

    def decode_token(self, token):
        try:
            import jwt
            from jwt.algorithms import RSAAlgorithm
        except ImportError as exc:
            raise GovBrAuthError(
                'Biblioteca PyJWT não instalada para validar tokens gov.br.') from exc

        try:
            header = jwt.get_unverified_header(token)
        except jwt.InvalidTokenError as exc:
            raise GovBrAuthError('Token gov.br inválido.') from exc

        if header.get('alg') != 'RS256':
            raise GovBrAuthError('Algoritmo de assinatura gov.br não suportado.')

        key = self._find_jwk(header.get('kid'))
        public_key = RSAAlgorithm.from_jwk(json.dumps(key))

        try:
            return jwt.decode(
                token,
                public_key,
                algorithms=['RS256'],
                audience=settings.GOVBR_CLIENT_ID,
                issuer=self.issuer,
                leeway=getattr(settings, 'GOVBR_JWT_LEEWAY', 30),
                options={'require': ['exp', 'iat', 'iss', 'aud', 'sub']},
            )
        except jwt.InvalidTokenError as exc:
            raise GovBrAuthError('Falha na validação do token gov.br.') from exc

    def _find_jwk(self, kid):
        try:
            response = self.http.get(self.jwk_url, timeout=self.timeout)
            response.raise_for_status()
            jwks = response.json()
        except (requests.RequestException, ValueError) as exc:
            logger.exception('Erro ao obter JWK do gov.br.')
            raise GovBrAuthError('Não foi possível validar a assinatura do gov.br.') from exc

        for key in jwks.get('keys', []):
            if key.get('kid') == kid:
                return key

        raise GovBrAuthError(
            'Chave pública gov.br não encontrada para o token recebido.')

    def logout_redirect_url(self, post_logout_redirect_uri):
        return '{}?{}'.format(
            self.logout_url,
            urlencode({'post_logout_redirect_uri': post_logout_redirect_uri}),
        )


def start_authorization(request, redirect_uri, next_url=''):
    state = secrets.token_urlsafe(32)
    nonce = secrets.token_urlsafe(32)
    code_verifier = new_code_verifier()

    request.session[GOVBR_SESSION_KEY] = {
        'state': state,
        'nonce': nonce,
        'code_verifier': code_verifier,
        'next': next_url,
        'created_at': int(time.time()),
    }

    return GovBrClient().authorization_url(
        redirect_uri=redirect_uri,
        state=state,
        nonce=nonce,
        code_verifier=code_verifier,
    )


def pop_authorization_state(request):
    oidc_state = request.session.pop(GOVBR_SESSION_KEY, None)
    if not oidc_state:
        raise GovBrAuthError('Sessão de autenticação gov.br não encontrada.')

    max_age = getattr(settings, 'GOVBR_STATE_MAX_AGE', 600)
    created_at = int(oidc_state.get('created_at') or 0)
    if created_at + max_age < int(time.time()):
        raise GovBrAuthError('Sessão de autenticação gov.br expirada.')

    return oidc_state


def resolve_user(id_claims, access_claims):
    cpf = clean_cpf(
        id_claims.get('preferred_username') or
        id_claims.get('sub') or
        access_claims.get('preferred_username') or
        access_claims.get('sub')
    )
    if not cpf:
        raise GovBrAuthError('O retorno do gov.br não trouxe um CPF válido.')

    user = find_existing_user(cpf, id_claims)
    if user is None and getattr(settings, 'GOVBR_AUTO_CREATE_USERS', False):
        user = create_user_from_claims(cpf, id_claims)

    if user is None:
        raise GovBrAuthError(
            'Não foi encontrada conta local vinculada ao CPF autenticado no gov.br.'
        )

    if not user.is_active:
        raise GovBrAuthError('A conta local vinculada ao gov.br está inativa.')

    return user, cpf


def find_existing_user(cpf, id_claims):
    User = get_user_model()
    email = id_claims.get('email')
    email_verified = is_truthy(id_claims.get('email_verified'))

    for field in get_lookup_fields():
        if field == 'username':
            user = first_or_error(
                User.objects.filter(username__in=cpf_variants(cpf)),
                'CPF informado pelo gov.br',
            )
            if user:
                return user
        elif field == 'email' and email and email_verified:
            user = first_or_error(
                User.objects.filter(email__iexact=email),
                'e-mail verificado informado pelo gov.br',
            )
            if user:
                return user

    return None


def first_or_error(queryset, description):
    users = list(queryset[:2])
    if len(users) > 1:
        raise GovBrAuthError(
            'Mais de uma conta local corresponde ao {}.'.format(description)
        )
    return users[0] if users else None


def create_user_from_claims(cpf, id_claims):
    User = get_user_model()
    if User.objects.filter(username__in=cpf_variants(cpf)).exists():
        raise GovBrAuthError(
            'Já existe conta local com o CPF informado pelo gov.br.')

    name = (id_claims.get('social_name') or id_claims.get('name') or '').strip()
    name_parts = name.split()
    first_name = name_parts[0] if name_parts else ''
    last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''

    user = User(username=cpf)
    user.first_name = limit_user_field(User, 'first_name', first_name)
    user.last_name = limit_user_field(User, 'last_name', last_name)

    if id_claims.get('email') and is_truthy(id_claims.get('email_verified')):
        user.email = limit_user_field(User, 'email', id_claims['email'])

    user.set_unusable_password()
    user.save()
    return user


def limit_user_field(User, field_name, value):
    max_length = User._meta.get_field(field_name).max_length
    return (value or '')[:max_length]
