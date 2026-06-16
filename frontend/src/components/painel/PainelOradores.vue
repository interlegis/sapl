<template>
        <div class="text-center painel" id="aparecer_oradores" v-if="canRender && oradores.length > 0">
            <h2 class="text-subtitle">Oradores</h2>
            <div id="orador">
                <table id="oradores_list">
                  <tr v-for="o in oradores" :key="o.ordem_pronunciamento">
                    <td style="padding-right:20px; color:white">
                        {{ o.ordem_pronunciamento }}º - {{ o.nome_parlamentar }}
                    </td>
                  </tr>
                </table>
            </div>
        </div>
</template>

<script>
import { mapState } from 'vuex';
export default {
  name: 'PainelOradores',
  data() {
    return {
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
#oradores_list tr td {
  font-size: 1.2rem;
  padding: 5px;
  text-align: start;
}
</style>