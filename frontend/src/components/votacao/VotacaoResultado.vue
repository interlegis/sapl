<template>
    <div v-if="parlamentares && parlamentares.length > 0">
        <legend>Situação da Votação:</legend>
        <div id="soma_votos">
            <div class="row">
                <div class="col-md-12">Sim: {{ votosSim }}</div>
            </div>
            <div class="row">
                <div class="col-md-12">Não: {{ votosNao }}</div>
            </div>
            <div class="row">
                <div class="col-md-12">Abstenções: {{ votosAbstencao }}</div>
            </div>
            <div class="row">
                <div class="col-md-12">Ainda não votaram: {{ naoVotou }}</div>
            </div>
        </div>
    </div>
</template>

<script>
import { mapGetters, mapState } from 'vuex';
export default {
  name: 'VotacaoResultado',
  computed: {
    ...mapState(['parlamentares']),
    ...mapGetters(['totalVotos']),
    votosSim() {
      const entry = this.totalVotos.find(t => t.tipo === 'Sim');
      return entry ? entry.total : 0;
    },
    votosNao() {
      const entry = this.totalVotos.find(t => t.tipo === 'Não');
      return entry ? entry.total : 0;
    },
    votosAbstencao() {
      const entry = this.totalVotos.find(t => t.tipo === 'Abstenção');
      return entry ? entry.total : 0;
    },
    naoVotou() {
      const entry = this.totalVotos.find(t => t.tipo === 'Não Votou');
      return entry ? entry.total : 0;
    }
  },
  mounted() {
    console.log('VotacaoResultado mounted');
  }
};
</script>
