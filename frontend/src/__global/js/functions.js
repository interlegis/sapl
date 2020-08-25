import skinTinymce from 'tinymce-light-skin'

window.removeTinymce = function () {
  while (window.tinymce.editors.length > 0) {
    window.tinymce.remove(window.tinymce.editors[0])
  }
}

window.initTextRichEditor = function (elements, readonly = false) {
  window.removeTinymce()
  const configTinymce = {
    force_br_newlines: false,
    force_p_newlines: false,
    forced_root_block: '',
    content_style: skinTinymce.contentStyle,
    skin: false,
    plugins: ['lists table code'],
    menubar: 'file edit view format table tools',
    toolbar: 'undo redo | styleselect | bold italic | alignleft aligncenter alignright alignjustify | bullist numlist outdent indent',
    min_height: 200

  }

  if (readonly) {
    configTinymce.readonly = 1
    configTinymce.menubar = false
    configTinymce.toolbar = false
  }

  if (elements != null) {
    configTinymce.elements = elements
    configTinymce.mode = 'exact'
  } else {
    configTinymce.mode = 'textareas'
  }
  skinTinymce.use()
  window.tinymce.init(configTinymce)
}

window.refreshDatePicker = function () {
  $.datepicker.setDefaults($.datepicker.regional['pt-BR'])
  $('.dateinput').datepicker()

  const dateinput = document.querySelectorAll('.dateinput')
  _.each(dateinput, function (input, index) {
    input.setAttribute('autocomplete', 'off')
  })
}

window.getCookie = function (name) {
  var cookieValue = null
  if (document.cookie && document.cookie !== '') {
    var cookies = document.cookie.split(';')
    for (var i = 0; i < cookies.length; i++) {
      var cookie = $.trim(cookies[i])
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
    var dialog = $('#modal_autor').dialog({
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
      var name_in_query = $('#q').val()
      // var q_0 = "q_0=nome__icontains"
      // var q_1 = name_in_query
      // query = q_1

      $.get('/api/autor?q=' + name_in_query, function (data) {
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

        var select = $(
          '<select id="resultados" style="min-width: 90%; max-width:90%;" size="5"/>'
        )

        data.results.forEach(function (item) {
          select.append(
            $('<option>')
              .attr('value', item.value)
              .text(item.text)
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
