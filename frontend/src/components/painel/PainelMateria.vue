<template>
        <div class="col-md-6 text-center painel" id="obs_materia_div" v-if="canRender">
            <h2 class="text-subtitle" id="mat_em_votacao">Matéria em Votação</h2>
            <span id="materia_legislativa_texto" class="text-value">{{ materia.texto }}</span>
            <br>
            <span id="materia_legislativa_ementa" class="text-value">{{ materia.ementa }} </span>
            <br>
            <span id="observacao_materia" class="text-value">{{ materia.observacao }}</span>
        </div>
</template>

<script>
import { mapState } from 'vuex';
export default {
  name: 'PainelMateria',
  data() {
    return {
       /*
       materia: {
            texto: '',
            ementa: '',
            observacao: '',
       }
       */
    };
  },
  mounted() {
    console.log('PainelMateria mounted');
  },
  beforeDestroy() {},
  computed: {
    canRender () {
        return this.sessao_aberta && this.painel_aberto;
    },
    ...mapState(["painel_aberto", "sessao_aberta", "materia"])
  }
};
</script>

<style scoped>
/* Optional styling */
</style>