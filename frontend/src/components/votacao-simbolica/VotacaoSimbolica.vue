<template>
    <fieldset class="form-group">
        <legend>Votação Simbólica</legend>

        <div v-if="error_message || localError" class="alert alert-danger">
            [[ error_message || localError ]]
        </div>

        <div>
            <b>Matéria:</b> [[ materia.texto ]]
            <br />
            <b>Ementa:</b> [[ materia.ementa ]]
            <br /><br />
            <b>Total presentes:</b> [[ totalPresentes ]] (com presidente)
            <br />
            <b>Total votantes:</b> [[ totalVotantes ]] (com presidente)
        </div>
        <br />

        <div class="row">
            <div class="col-md-4">Sim*:
                <input type="number" min="0" v-model.number="votosSim" class="form-control" />
            </div>
            <div class="col-md-4">Não*:
                <input type="number" min="0" v-model.number="votosNao" class="form-control" />
            </div>
            <div class="col-md-4">Abstenções*:
                <input type="number" min="0" v-model.number="abstencoes" class="form-control" />
            </div>
        </div>

        <div class="row mt-3">
            <div class="col-md-6">
                A totalização inclui o voto do Presidente?*
                <select v-model="votoPresidente" class="form-control">
                    <option :value="1">Sim</option>
                    <option :value="0">Não</option>
                </select>
            </div>
            <div class="col-md-6">
                Resultado da Votação*
                <select v-model="resultadoSelected" class="form-control">
                    <option value="">---------</option>
                    <option v-for="tipo in tipos_resultado" :key="tipo.id" :value="tipo.id">
                        [[ tipo.nome ]]
                    </option>
                </select>
            </div>
        </div>

        <div class="row mt-3">
            <div class="col-md-12">
                Observações
                <textarea v-model="observacao" rows="7" class="form-control"></textarea>
            </div>
        </div>

        <br />
        <div class="row">
            <div class="col-md-12">
                <div class="form-group row justify-content-between">
                    <input type="button" value="Cancelar Votação" class="btn btn-warning" @click="$emit('cancelar')" />
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
  name: 'VotacaoSimbolica',
  props: {
    errorMessage: {
      type: String,
      default: ''
    },
    totalPresentes: {
      type: [String, Number],
      default: 0
    },
    totalVotantes: {
      type: [String, Number],
      default: 0
    }
  },
  data () {
    return {
      votosSim: 0,
      votosNao: 0,
      abstencoes: 0,
      votoPresidente: 0,
      resultadoSelected: '',
      observacao: '',
      localError: ''
    }
  },
  computed: {
    ...mapState(usePainelStore, ['materia', 'tipos_resultado']),
    error_message () {
      return this.errorMessage
    }
  },
  methods: {
    onSalvar () {
      if (!this.resultadoSelected) {
        this.localError = 'Selecione o resultado da votação antes de salvar.'
        return
      }
      this.localError = ''
      this.$emit('salvar', {
        votos_sim: this.votosSim,
        votos_nao: this.votosNao,
        abstencoes: this.abstencoes,
        voto_presidente: this.votoPresidente,
        resultado_votacao: this.resultadoSelected,
        observacao: this.observacao
      })
    }
  },
  mounted () {
    console.log('VotacaoSimbolica mounted')
  }
}
</script>
