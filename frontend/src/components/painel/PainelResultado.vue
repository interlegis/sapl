<template>
        <div class="col-md-6 text-left painel" id="resultado_votacao_div" v-if="canRender">
            <div class="d-flex align-items-left justify-content-left mb-2">
              <h2 class="text-subtitle mb-0">Resultado</h2>
              <button class="btn btn-sm btn-secondary ms-2" v-on:click="changeFontSize(-1)">
                  A-
              </button>
              <button class="btn btn-sm btn-secondary ms-2" v-on:click="changeFontSize(1)">
                  A+
              </button>
            </div>
            <div ref="votacao" id="box_votacao">
                <div id="votacao" class="text-value">
                  <li>Sim: {{ resultado.numero_votos.votos_sim }}</li>
                  <li>Não: {{ resultado.numero_votos.votos_nao }}</li>
                  <li>Abstenções: {{ resultado.numero_votos.abstencoes }}</li>
                  <li>Presentes: {{ resultado.numero_votos.num_presentes }}</li>
                  <li>Total votos: {{ resultado.numero_votos.total_votos }}</li>
                </div>
                <div id="resultado_votacao" class="text-title">{{ resultado.resultado_votacao }}</div>
            </div>
        </div>
</template>

<script>
import { mapState } from 'vuex';
export default {
  name: 'PainelResultado',
  data() {
    return {
        /*
        resultado: {
           numero_votos: {
                votos_sim: 0,
                votos_nao: 0,
                abstencoes: 0,
                total_votos: 0,
                num_presentes: 0,
           },
           resultado_votacao: '',
        }
        */
    };
  },
  mounted() {
    console.log('PainelResultado mounted');
  },
  beforeDestroy() {},
  computed: {
    canRender () {
        return this.sessao_aberta && this.painel_aberto;
    },
    ...mapState(["painel_aberto", "sessao_aberta", "resultado"])
  },
  methods: {
    changeFontSize(value) {
      const el = this.$refs.votacao;
      if (!el) return;
      let fontSize = window.getComputedStyle(el).fontSize;
      fontSize = parseFloat(fontSize); // safely convert "16px" → 16
      el.style.fontSize = (fontSize + value) + 'px';
    },
  }
};
</script>

<style scoped>
/* Optional styling */
</style>