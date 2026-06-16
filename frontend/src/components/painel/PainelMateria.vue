<template>
        <div class="painel p-3 d-flex flex-column" id="obs_materia_div" v-if="canRender">
            <div class="flex-grow-1">
                <h2 id="mat_em_votacao" class="text-subtitle text-center mb-3 pb-1">
                    Matéria em Votação
                </h2>
                <span id="materia_legislativa_texto"
                      class="fs-4 text-white d-block mb-1">{{ materia.texto }}</span>
                <span id="materia_legislativa_ementa"
                      class="fs-6 fst-italic opacity-75 text-white">{{ materia.ementa }}</span>

                <div class="mt-2 text-warning" style="font-size: 0.9rem">
                    <span id="observacao_materia">{{ materia.observacao }}</span>
                </div>

                <div id="resultado_votacao"
                     class="text-title mt-auto text-center d-block fs-2">{{ materia.resultado_votacao }}</div>
            </div>
        </div>
</template>

<script>
import { mapState } from 'vuex';
export default {
  name: 'PainelMateria',
  data() {
    return {
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
.text-title {
  color: var(--text-highlight);
  letter-spacing: 1px;
}
</style>