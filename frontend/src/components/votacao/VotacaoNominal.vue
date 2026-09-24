<template>
    <fieldset>
        <legend>Votação Nominal</legend>

        <div v-if="error_message" class="alert alert-danger">
            {{ error_message }}
        </div>

        <div class="alert" :class="registroAberto ? 'alert-warning' : 'alert-info'">
            <strong>Status da votação:</strong> em aberto ·
            <span v-if="registroAberto">novos votos <strong>bloqueados</strong> — os vereadores que ainda não votaram não conseguem mais votar até a Mesa reabrir</span>
            <span v-else>novos votos <strong>permitidos</strong> — os vereadores ainda podem votar pelo tablet enquanto a Mesa registra</span>
        </div>

        <button type="button" class="btn btn-sm mb-3"
                :class="registroAberto ? 'btn-secondary' : 'btn-info'"
                @click="onToggleRegistro">
            {{ registroAberto ? 'Reabrir Votação para Novos Votos' : 'Bloquear Novos Votos' }}
        </button>

        <votacao-materia></votacao-materia>
        <br />

        <votacao-votos :votos-status="votosStatus" :votos-travados="votosTravados" @cast-vote="onCastVote" ref="votos"></votacao-votos>

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
import { mapState } from 'pinia';
import { usePainelStore } from '@/__apps/painel/store/painelStore';
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
    },
    votosStatus: {
      type: Object,
      default: () => ({})
    },
    votosTravados: {
      type: Object,
      default: () => ({})
    },
    registroAberto: {
      type: Boolean,
      default: false
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
    ...mapState(usePainelStore, ['parlamentares', 'materia']),
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
    },
    onToggleRegistro() {
      this.$emit('toggle-registro', !this.registroAberto);
    }
  },
  mounted() {
    console.log('VotacaoNominal mounted');
  }
};
</script>