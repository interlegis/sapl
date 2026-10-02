<template>
    <fieldset class="form-group">
        <legend>Leitura de Matéria</legend>

        <div v-if="error_message" class="alert alert-danger">
            {{ error_message }}
        </div>

        <div>
            <b>Matéria:</b> {{ materia.texto }}
            <br />
            <b>Ementa:</b> {{ materia.ementa }}
        </div>
        <br />

        <div class="row">
            <div class="col-md-12">
                Observações
                <textarea v-model="observacao" rows="7" class="form-control"></textarea>
            </div>
        </div>

        <br />
        <div class="row">
            <div class="col-md-12">
                <div class="form-group row justify-content-between">
                    <a :href="cancelUrl" class="btn btn-warning">Cancelar Leitura</a>
                    <input type="button" value="Salvar" class="btn btn-primary" @click="onSalvar" />
                </div>
            </div>
        </div>
    </fieldset>
</template>

<script>
import { mapState } from 'pinia'
import { usePainelStore } from '@/__apps/painel/store/painelStore'

export default {
  name: 'LeituraMateria',
  props: {
    errorMessage: {
      type: String,
      default: ''
    },
    cancelUrl: {
      type: String,
      default: '#'
    },
    initialObservacao: {
      type: String,
      default: ''
    },
    initialMateriaTexto: {
      type: String,
      default: ''
    },
    initialMateriaEmenta: {
      type: String,
      default: ''
    }
  },
  data () {
    return {
      observacao: this.initialObservacao
    }
  },
  computed: {
    ...mapState(usePainelStore, { storeMateria: 'materia' }),
    error_message () {
      return this.errorMessage
    },
    // O broadcast do painel só reflete a matéria em votação/leitura DEPOIS
    // que a ação abre a matéria; o texto/ementa iniciais vêm sempre do
    // contexto Django (a matéria já é conhecida pela URL, oid/mid).
    materia () {
      if (this.storeMateria && this.storeMateria.texto) return this.storeMateria
      return { texto: this.initialMateriaTexto, ementa: this.initialMateriaEmenta }
    }
  },
  methods: {
    onSalvar () {
      this.$emit('salvar', { observacao: this.observacao })
    }
  },
  mounted () {
    console.log('LeituraMateria mounted')
  }
}
</script>
