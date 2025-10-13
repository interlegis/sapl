<template>
        <div class="col-md-6 text-center painel" id="aparecer_oradores" v-if="canRender">
            <h2 class="text-subtitle">Oradores</h2>
            <table id="oradores_list">
              <tr v-for="o in oradores" :key="o.ordem_pronunciamento"><td style="padding-right:20px; color:white">
                  {{ o.ordem_pronunciamento }}º &nbsp {{ o.nome_parlamentar }}</td>
              </tr>
            </table>
        </div>
</template>

<script>
import { mapState } from 'vuex';
export default {
  name: 'PainelOradores',
  data() {
    return {
      // oradores: [],
    };
  },
  mounted() {
    console.log('PainelOradores mounted');
  },
  beforeDestroy() {},
  computed: {
    canRender () {
        return this.sessao_aberta && this.painel_aberto;
    },
    ...mapState(["painel_aberto", "sessao_aberta", "oradores"])
  }
};
</script>

<style scoped>
/* Optional styling */
</style>