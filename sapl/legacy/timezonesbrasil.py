import unicodedata

from pytz import timezone

UF_PARA_TIMEZONE = '''
    AC  America/Rio_Branco
    AL  America/Maceio
    AP  America/Belem
    AM  America/Manaus
    BA  America/Bahia
    CE  America/Fortaleza
    DF  America/Sao_Paulo
    ES  America/Sao_Paulo
    GO  America/Sao_Paulo
    MA  America/Fortaleza
    MT  America/Cuiaba
    MS  America/Campo_Grande
    MG  America/Sao_Paulo
    PR  America/Sao_Paulo
    PB  America/Fortaleza
    PA  America/Belem
    PE  America/Recife
    PI  America/Fortaleza
    RJ  America/Sao_Paulo
    RN  America/Fortaleza
    RS  America/Sao_Paulo
    RO  America/Porto_Velho
    RR  America/Boa_Vista
    SC  America/Sao_Paulo
    SE  America/Maceio
    SP  America/Sao_Paulo
    TO  America/Araguaina
'''
UF_PARA_TIMEZONE = dict(line.split()
                        for line in UF_PARA_TIMEZONE.strip().splitlines())


def normalizar_texto(texto):
    # baseado em https://gist.github.com/j4mie/557354
    norm = unicodedata.normalize('NFKD', texto.lower())
    return norm.encode('ASCII', 'ignore').decode('ascii')

# Exceções (Anazonas e Pará):
#     leste do Amazonas: America/Manaus
#     oeste do Amazonas: America/Eirunepe
#     leste do Pará:     America/Belem
#     oeste do Pará:     America/Santarem
# fontes:
#     https://en.wikipedia.org/wiki/Time_in_Brazil
#     https://www.zeitverschiebung.net/en/timezone/america--belem
#     https://www.zeitverschiebung.net/en/timezone/america--santarem
#     https://www.zeitverschiebung.net/en/timezone/america--manaus
#     https://www.zeitverschiebung.net/en/timezone/america--eirunepe


TZ_CIDADES_AMAZONAS_E_PARA = [
    ('America/Manaus', '''
        Manaus
        Itacoatiara
        Parintins
        Manacapuru
        Coari
        Tefé
        Humaitá
        Tabatinga
        Rio Preto da Eva
        Maués
        Carauari
        Fonte Boa
        São Gabriel da Cachoeira
        Boca do Acre
        Manicoré
        Nova Olinda do Norte
        Borba
        São Paulo de Olivença
        Barreirinha
        Codajás
        Iranduba
        Novo Aripuanã
        Urucurituba
        Manaquiri
        Guajará
        Autazes
        Santo Antônio do Içá
        Urucará
        Anori
        Pauini
        Barcelos
        Careiro da Várzea
        Canutama
        Jutaí
        Alvarães
'''),
    ('America/Eirunepe', '''
        Eirunepé
        Benjamin Constant
        Envira
'''),
    ('America/Belem', '''
        Belém
        Ananindeua
        Macapá
        Marabá
        Castanhal
        Santana
        Abaetetuba
        Tucuruí
        Paragominas
        Bragança
        Benevides
        Capanema
        Breves
        Cametá
        Salinópolis
        Tomé Açu
        Capitão Poço
        Barcarena
        Vigia
        São Miguel do Guamá
        Conceição do Araguaia
        Igarapé Miri
        Igarapé Açu
        Moju
        Portel
        Itupiranga
        Viseu
        Soure
        Mocajuba
        São Félix do Xingu
        Augusto Corrêa
        Tucumã
        Santa Maria do Pará
        Acará
        Maracanã
        Baião
        Curuçá
        Marapanim
        Oeiras do Pará
        São João de Pirabas
        Santo Antônio do Tauá
        São Caetano de Odivelas
        Ourém
        Muaná
        Afuá
        Mazagão
        Gurupá
        Bujaru
        Senador José Porfírio
        Irituia
        parauapebas
        brejo grande do araguaia
        santana do araguaia
        ourilandia do norte
        marituba
        canaa dos carajas
        goianesia do para
'''),
    ('America/Santarem', '''
        Santarém
        Altamira
        Itaituba
        Oriximiná
        Alenquer
        Ábidos
        Monte Alegre
        Almeirim
        Terra Santa
        Juruti
        Porto de Moz
        Nhamundá
        Prainha
        medicilandia
'''),
]
TZ_CIDADES_AMAZONAS_E_PARA = {normalizar_texto(cidade.strip()): tz
                              for tz, linhas in TZ_CIDADES_AMAZONAS_E_PARA
                              for cidade in linhas.strip().splitlines()}


def get_nome_timezone(cidade, uf):
    uf = uf.upper()
    tz = UF_PARA_TIMEZONE[uf]
    if uf in ['PA', 'AM']:
        cidade = normalizar_texto(cidade)
        return TZ_CIDADES_AMAZONAS_E_PARA[cidade]
    else:
        return tz


def get_timezone(cidade, uf):
    return timezone(get_nome_timezone(cidade, uf))


def test_get_nome_timezone():
    for cidade, uf, tz in [
            ('Fortaleza', 'CE', 'America/Fortaleza'),
            ('Salvador', 'BA', 'America/Bahia'),
            ('Belem', 'PA', 'America/Belem'),        # sem acento
            ('Belém', 'PA', 'America/Belem'),        # com acento
            ('Santarem', 'PA', 'America/Santarem'),  # sem acento
            ('Santarém', 'PA', 'America/Santarem'),  # com acento
            ('Manaus', 'AM', 'America/Manaus'),
            ('Eirunepe', 'AM', 'America/Eirunepe'),  # sem acento
            ('Eirunepé', 'AM', 'America/Eirunepe'),  # com acento
    ]:
        assert get_nome_timezone(cidade, uf) == tz, (cidade, uf, tz)
