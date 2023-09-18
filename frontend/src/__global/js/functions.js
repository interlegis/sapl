
window.refreshDatePicker = function () {
  $.datepicker.setDefaults($.datepicker.regional['pt-BR'])
  $('.dateinput').datepicker()

  const dateinput = document.querySelectorAll('.dateinput')
  _.each(dateinput, function (input, index) {
    input.setAttribute('autocomplete', 'off')
  })
}

window.getCookie = function (name) {
  let cookieValue = null
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';')
    for (let i = 0; i < cookies.length; i++) {
      const cookie = $.trim(cookies[i])
      if (cookie.substring(0, name.length + 1) === name + '=') {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1))
        break
      }
    }
  }
  return cookieValue
}

window.autorModal = function () {
  $(function () {
    const dialog = $('#modal_autor').dialog({
      autoOpen: false,
      modal: true,
      width: 500,
      height: 340,
      show: {
        effect: 'blind',
        duration: 500
      },
      hide: {
        effect: 'explode',
        duration: 500
      }
    })

    $('#button-id-limpar').click(function () {
      $('#nome_autor').text('')

      function clean_if_exists (fieldname) {
        if ($(fieldname).length > 0) {
          $(fieldname).val('')
        }
      }

      clean_if_exists('#id_autor')
      clean_if_exists('#id_autoria__autor')
      clean_if_exists('#id_autorianorma__autor')
    })

    $('#button-id-pesquisar').click(function () {
      $('#q').val('')
      $('#div-resultado')
        .children()
        .remove()
      $('#modal_autor').dialog('open')
      $('#selecionar').attr('hidden', 'hidden')
    })

    $('#pesquisar').click(function () {
      const json_data = {
        q: $('#q').val()
        // get_all: true
      }
      $.get('/api/base/autor', json_data, function (data) {
        $('#div-resultado')
          .children()
          .remove()
        if (data.pagination.total_entries === 0) {
          $('#selecionar').attr('hidden', 'hidden')
          $('#div-resultado').html(
            "<span class='alert'><strong>Nenhum resultado</strong></span>"
          )
          return
        }

        const select = $(
          '<select id="resultados" style="min-width: 90%; max-width:90%;" size="5"/>'
        )

        data.results.forEach(function (item) {
          select.append(
            $('<option>')
              .attr('value', item.id)
              .text(item.nome)
          )
        })

        $('#div-resultado')
          .append('<br/>')
          .append(select)
        $('#selecionar').removeAttr('hidden', 'hidden')

        if (data.pagination.total_pages > 1) {
          $('#div-resultado').prepend(
            '<span><br/>Mostrando 10 primeiros autores relativos a sua busca.<br/></span>'
          )
        }

        $('#selecionar').click(function () {
          const res = $('#resultados option:selected')
          const id = res.val()
          const nome = res.text()

          $('#nome_autor').text(nome)

          // MateriaLegislativa pesquisa Autor via a tabela Autoria
          if ($('#id_autoria__autor').length) {
            $('#id_autoria__autor').val(id)
          }
          // Protocolo pesquisa a própria tabela de Autor
          if ($('#id_autor').length) {
            $('#id_autor').val(id)
          }
          // MateriaLegislativa pesquisa Autor via a tabela AutoriaNorma
          if ($('#id_autorianorma__autor').length) {
            $('#id_autorianorma__autor').val(id)
          }

          dialog.dialog('close')
        })
      })
    })
  })

  /* function get_nome_autor(fieldname) {
    if ($(fieldname).length > 0) { // se campo existir
      if ($(fieldname).val() != "") { // e não for vazio
        var id = $(fieldname).val();
        $.get("/proposicao/get-nome-autor?id=" + id, function(data, status){
            $("#nome_autor").text(data.nome);
        });
      }
    }
  }

  get_nome_autor("#id_autor");
  get_nome_autor("#id_autoria__autor"); */
}

window.refreshMask = function () {
  $('.telefone').mask('(99) 9999-9999', { placeholder: '(__) ____ -____' })
  $('.cpf').mask('000.000.000-00', { placeholder: '___.___.___-__' })
  $('.cep').mask('00000-000', { placeholder: '_____-___' })
  $('.rg').mask('0.000.000', { placeholder: '_.___.___' })
  $('.titulo_eleitor').mask('0000.0000.0000.0000', {
    placeholder: '____.____.____.____'
  })
  $('.dateinput').mask('00/00/0000', { placeholder: '__/__/____' })
  $('.hora, input[name=hora_inicio], input[name=hora_fim], input[name=hora]').mask('00:00', {
    placeholder: 'hh:mm'
  })
  $('.hora_hms').mask('00:00:00', { placeholder: 'hh:mm:ss' })
  $('.timeinput').mask('00:00:00', { placeholder: 'hh:mm:ss' })
  $('.cronometro').mask('00:00:00', { placeholder: 'hh:mm:ss' })
}
