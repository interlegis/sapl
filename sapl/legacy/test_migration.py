from random import shuffle

from .migration import (get_autorias_sem_repeticoes,
                        get_reapontamento_de_autores_repetidos)


def test_unifica_autores_repetidos_no_legado():

    # cod_parlamentar, cod_autor
    autores = [[0, 0],
               [1, 10],
               [1, 11],
               [1, 12],
               [2, 20],
               [2, 21],
               [2, 22],
               [3, 30],
               [3, 31],
               [4, 40],
               [5, 50]]
    reapontamento, apagar = get_reapontamento_de_autores_repetidos(autores)
    assert reapontamento == {10: 10, 11: 10, 12: 10,
                             20: 20, 21: 20, 22: 20,
                             30: 30, 31: 30}
    assert sorted(apagar) == [11, 12, 21, 22, 31]

    # cod_autor, cod_materia, ind_primeiro_autor
    autoria = [[10, 111, 0],  # não é repetida, mas envolve um autor repetido

               [22, 222, 1],  # não é repetida, mas envolve um autor repetido

               [10, 777, 1],  # repetição c ind_primeiro_autor==1 no INÍCIO
               [10, 777, 0],
               [11, 777, 0],
               [12, 777, 0],

               [30, 888, 0],  # repetição c ind_primeiro_autor==1 no MEIO
               [31, 888, 1],
               [30, 888, 0],

               [11, 999, 0],  # repetição SEM ind_primeiro_autor==1
               [12, 999, 0],

               [21, 999, 0],  # repetição SEM ind_primeiro_autor==1
               [22, 999, 0],
               ]
    shuffle(autoria)  # não devemos supor ordem na autoria
    nova_autoria = get_autorias_sem_repeticoes(autoria, reapontamento)
    assert nova_autoria == sorted([(10, 111, 0),
                                   (20, 222, 1),
                                   (10, 777, 1),
                                   (30, 888, 1),
                                   (10, 999, 0),
                                   (20, 999, 0),
                                   ])
