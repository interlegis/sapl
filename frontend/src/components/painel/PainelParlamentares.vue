<template>
        <div class="col-md-4" v-if="canRender">
            <div class="text-center painel">
                <h2 class="text-subtitle">Parlamentares</h2>
                <span id="parlamentares" class="text-value text-center"></span>
                <table id="parlamentares_list">
                        <tr v-for="p in parlamentares" :key="p.parlamentar_id" class="text-value text-center">
                            <td style="padding-right:20px; color:yellow" > {{ p.nome_parlamentar }}</td>
                            <td style="padding-right:20px; color:yellow">  {{ p.filiacao }}</td>
                            <td style="padding-right:20px; color:yellow" v-if="mostrar_voto">{{ p.voto }}</td>
                        </tr>
                </table>
            </div>
        </div>
</template>

<script>
import { mapState } from 'vuex';
export default {
  name: 'PainelParlamentares',
  data() {
    return {
      //parlamentares: [],
    };
  },
  mounted() {
    console.log('PainelParlamentares mounted');
  },
  beforeDestroy() {},
  computed: {
    canRender () {
        return this.sessao_aberta && this.painel_aberto;
    },
    ...mapState(["painel_aberto", "sessao_aberta", "parlamentares", "mostrar_voto"])
  },
};
</script>

<style scoped>
/* Optional styling */
</style>