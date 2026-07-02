<template>
    <fieldset>
        <legend>Votação Nominal</legend>

        <div v-if="error_message" class="alert alert-danger">
            {{ error_message }}
        </div>

        <votacao-materia></votacao-materia>
        <br />

        <votacao-votos @cast-vote="onCastVote" ref="votos"></votacao-votos>

        <votacao-resultado ref="resultado"></votacao-resultado>

        <votacao-observacoes
            :observacoes.sync="observacoes"
            :resultado-selected.sync="resultado_selected"
            :disabled="disable_resultado"
            @cancelar="onCancelar"
            @fechar="onFechar"
            ref="observacoesComp">
        </votacao-observacoes>
    </fieldset>
</template>

<script>
import { mapState } from 'vuex';
export default {
  name: 'VotacaoNominal',
  props: {
    isOpen: {
      type: Boolean,
      default: false
    },
    errorMessage: {
      type: String,
      default: ''
    }
  },
  data() {
    return {
      edit_votes: true,
      disable_resultado: false,
      resultado_selected: '',
      observacoes: '',
    }
  },
  computed: {
    ...mapState(['parlamentares', 'materia']),
    error_message() {
      return this.errorMessage;
    }
  },
  methods: {
    onCastVote({ parlamentar_id, voto }) {
      this.$emit('cast-vote', { parlamentar_id, voto });
    },
    onCancelar() {
      this.$emit('cancelar');
    },
    onFechar() {
      this.$emit('fechar', {
        resultado_selected: this.resultado_selected,
        observacoes: this.observacoes
      });
    }
  },
  mounted() {
    console.log('VotacaoNominal mounted');
  }
};
</script>