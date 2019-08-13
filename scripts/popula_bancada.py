from datetime import datetime

from sapl.parlamentares.models import Bancada, MembroBancada, Parlamentar, Legislatura, CargoBancada, CargoMembroBancada


def main():
    popula_bancada()
    popula_membro_bancada()
    popula_cargo_bancada()
    popula_cargo_membro_bancada()


def popula_bancada():
    Bancada.objects.create(
        nome='Bancada 1',
        descricao='Descrição da Bancada 1.',
        ativo=True)
    Bancada.objects.create(
        nome='Bancada 2',
        descricao='Descrição da Bancada 2.',
        ativo=False)
    Bancada.objects.create(
        nome='Bancada 3',
        descricao='Descrição da Bancada 3.',
        ativo=True)


def popula_membro_bancada():
    MembroBancada.objects.create(
        parlamentar=Parlamentar.objects.all()[0],
        bancada=Bancada.objects.get(nome='Bancada 1'),
        data_inicio='2018-1-1',
        data_fim='2019-12-31',
        legislatura=Legislatura.objects.first())
    MembroBancada.objects.create(
        parlamentar=Parlamentar.objects.all()[1],
        bancada=Bancada.objects.get(nome='Bancada 1'),
        data_inicio='2018-1-1',
        data_fim='2019-12-31',
        legislatura=Legislatura.objects.first())
    MembroBancada.objects.create(
        parlamentar=Parlamentar.objects.all()[2],
        bancada=Bancada.objects.get(nome='Bancada 1'),
        data_inicio='2018-1-1',
        data_fim='2019-12-31',
        legislatura=Legislatura.objects.first())
    MembroBancada.objects.create(
        parlamentar=Parlamentar.objects.all()[3],
        bancada=Bancada.objects.get(nome='Bancada 1'),
        data_inicio='2018-1-1',
        data_fim='2019-12-31',
        legislatura=Legislatura.objects.first())
    MembroBancada.objects.create(
        parlamentar=Parlamentar.objects.all()[4],
        bancada=Bancada.objects.get(nome='Bancada 1'),
        data_inicio='2018-1-1',
        data_fim='2019-12-31',
        legislatura=Legislatura.objects.first())

    MembroBancada.objects.create(
        parlamentar=Parlamentar.objects.all()[5],
        bancada=Bancada.objects.get(nome='Bancada 2'),
        data_inicio='2018-1-1',
        data_fim='2019-12-31',
        legislatura=Legislatura.objects.first())
    MembroBancada.objects.create(
        parlamentar=Parlamentar.objects.all()[6],
        bancada=Bancada.objects.get(nome='Bancada 2'),
        data_inicio='2018-1-1',
        data_fim='2019-12-31',
        legislatura=Legislatura.objects.first())
    MembroBancada.objects.create(
        parlamentar=Parlamentar.objects.all()[7],
        bancada=Bancada.objects.get(nome='Bancada 2'),
        data_inicio='2018-1-1',
        data_fim='2019-12-31',
        legislatura=Legislatura.objects.first())
    MembroBancada.objects.create(
        parlamentar=Parlamentar.objects.all()[8],
        bancada=Bancada.objects.get(nome='Bancada 2'),
        data_inicio='2018-1-1',
        data_fim='2019-12-31',
        legislatura=Legislatura.objects.first())
    MembroBancada.objects.create(
        parlamentar=Parlamentar.objects.all()[9],
        bancada=Bancada.objects.get(nome='Bancada 2'),
        data_inicio='2018-1-1',
        data_fim='2019-12-31',
        legislatura=Legislatura.objects.first())

    MembroBancada.objects.create(
        parlamentar=Parlamentar.objects.all()[10],
        bancada=Bancada.objects.get(nome='Bancada 3'),
        data_inicio='2018-1-1',
        data_fim='2019-12-31',
        legislatura=Legislatura.objects.first())
    MembroBancada.objects.create(
        parlamentar=Parlamentar.objects.all()[11],
        bancada=Bancada.objects.get(nome='Bancada 3'),
        data_inicio='2018-1-1',
        data_fim='2019-12-31',
        legislatura=Legislatura.objects.first())
    MembroBancada.objects.create(
        parlamentar=Parlamentar.objects.all()[12],
        bancada=Bancada.objects.get(nome='Bancada 3'),
        data_inicio='2018-1-1',
        data_fim='2019-12-31',
        legislatura=Legislatura.objects.first())
    MembroBancada.objects.create(
        parlamentar=Parlamentar.objects.all()[13],
        bancada=Bancada.objects.get(nome='Bancada 3'),
        data_inicio='2018-1-1',
        data_fim='2019-12-31',
        legislatura=Legislatura.objects.first())
    MembroBancada.objects.create(
        parlamentar=Parlamentar.objects.all()[14],
        bancada=Bancada.objects.get(nome='Bancada 3'),
        data_inicio='2018-1-1',
        data_fim='2019-12-31',
        legislatura=Legislatura.objects.first())


def popula_cargo_bancada():
    CargoBancada.objects.create(
        nome='Cargo 1',
        descricao='Descrição do Cargo 1.')
    CargoBancada.objects.create(
        nome='Cargo 2',
        descricao='Descrição do Cargo 2.')
    CargoBancada.objects.create(
        nome='Cargo 3',
        descricao='Descrição do Cargo 3.')


def popula_cargo_membro_bancada():
    CargoMembroBancada.objects.create(
        cargo=CargoBancada.objects.get(nome='Cargo 1'),
        membro=MembroBancada.objects.get(parlamentar=Parlamentar.objects.all()[0]),
        data_inicio='2018-1-30',
        data_fim='2019-5-31')
    CargoMembroBancada.objects.create(
        cargo=CargoBancada.objects.get(nome='Cargo 1'),
        membro=MembroBancada.objects.get(parlamentar=Parlamentar.objects.all()[1]),
        data_inicio='2018-1-30',
        data_fim='2019-5-31')
    CargoMembroBancada.objects.create(
        cargo=CargoBancada.objects.get(nome='Cargo 1'),
        membro=MembroBancada.objects.get(parlamentar=Parlamentar.objects.all()[2]),
        data_inicio='2018-1-30',
        data_fim='2019-5-31')
    CargoMembroBancada.objects.create(
        cargo=CargoBancada.objects.get(nome='Cargo 1'),
        membro=MembroBancada.objects.get(parlamentar=Parlamentar.objects.all()[3]),
        data_inicio='2018-1-30',
        data_fim='2019-5-31')
    CargoMembroBancada.objects.create(
        cargo=CargoBancada.objects.get(nome='Cargo 1'),
        membro=MembroBancada.objects.get(parlamentar=Parlamentar.objects.all()[4]),
        data_inicio='2018-1-30',
        data_fim='2019-5-31')
    CargoMembroBancada.objects.create(
        cargo=CargoBancada.objects.get(nome='Cargo 1'),
        membro=MembroBancada.objects.get(parlamentar=Parlamentar.objects.all()[5]),
        data_inicio='2018-1-30',
        data_fim='2019-5-31')
    CargoMembroBancada.objects.create(
        cargo=CargoBancada.objects.get(nome='Cargo 1'),
        membro=MembroBancada.objects.get(parlamentar=Parlamentar.objects.all()[6]),
        data_inicio='2018-1-30',
        data_fim='2019-5-31')
    CargoMembroBancada.objects.create(
        cargo=CargoBancada.objects.get(nome='Cargo 1'),
        membro=MembroBancada.objects.get(parlamentar=Parlamentar.objects.all()[7]),
        data_inicio='2018-1-30',
        data_fim='2019-5-31')
    CargoMembroBancada.objects.create(
        cargo=CargoBancada.objects.get(nome='Cargo 1'),
        membro=MembroBancada.objects.get(parlamentar=Parlamentar.objects.all()[8]),
        data_inicio='2018-1-30',
        data_fim='2019-5-31')
    CargoMembroBancada.objects.create(
        cargo=CargoBancada.objects.get(nome='Cargo 1'),
        membro=MembroBancada.objects.get(parlamentar=Parlamentar.objects.all()[9]),
        data_inicio='2018-1-30',
        data_fim='2019-5-31')
    CargoMembroBancada.objects.create(
        cargo=CargoBancada.objects.get(nome='Cargo 1'),
        membro=MembroBancada.objects.get(parlamentar=Parlamentar.objects.all()[10]),
        data_inicio='2018-1-30',
        data_fim='2019-5-31')
    CargoMembroBancada.objects.create(
        cargo=CargoBancada.objects.get(nome='Cargo 1'),
        membro=MembroBancada.objects.get(parlamentar=Parlamentar.objects.all()[11]),
        data_inicio='2018-1-30',
        data_fim='2019-5-31')
    CargoMembroBancada.objects.create(
        cargo=CargoBancada.objects.get(nome='Cargo 1'),
        membro=MembroBancada.objects.get(parlamentar=Parlamentar.objects.all()[12]),
        data_inicio='2018-1-30',
        data_fim='2019-5-31')

    CargoMembroBancada.objects.create(
        cargo=CargoBancada.objects.get(nome='Cargo 2'),
        membro=MembroBancada.objects.get(parlamentar=Parlamentar.objects.all()[13]),
        data_inicio='2018-1-30',
        data_fim='2019-5-31')
    CargoMembroBancada.objects.create(
        cargo=CargoBancada.objects.get(nome='Cargo 3'),
        membro=MembroBancada.objects.get(parlamentar=Parlamentar.objects.all()[14]),
        data_inicio='2018-1-30',
        data_fim='2019-5-31')


if __name__ == '__main__':
    main()
