<template>
        <div class="painel p-3 d-flex flex-column" id="resultado_votacao_div" v-if="canRender">
            <div id="box_votacao" class="w-100">
                <table class="table-custom w-100 mb-0" id="tabela_resultados">
                    <tbody id="votacao">
                        <tr>
                            <td>Presentes</td>
                            <td>{{ numPresentes }}</td>
                        </tr>
                        <tr>
                            <td>Sim</td>
                            <td class="table-sim">{{ votosSim }}</td>
                        </tr>
                        <tr>
                            <td>Não</td>
                            <td class="table-nao">{{ votosNao }}</td>
                        </tr>
                        <tr>
                            <td>Abstenções</td>
                            <td class="table-abstencao">{{ votosAbstencao }}</td>
                        </tr>
                        <tr>
                            <td><strong>Total votos</strong></td>
                            <td class="table-total"><strong>{{ totalVotos }}</strong></td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
</template>

<script>
import { mapState } from 'vuex';
export default {
  name: 'PainelResultado',
  data() {
    return {
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
    ...mapState(["painel_aberto", "sessao_aberta", "resultado", "parlamentares"]),
    numPresentes() {
      if (this.resultado && this.resultado.numero_votos && typeof this.resultado.numero_votos.num_presentes !== 'undefined' && this.resultado.numero_votos.num_presentes !== null) {
        return this.resultado.numero_votos.num_presentes;
      }
      return this.parlamentares ? this.parlamentares.length : 0;
    },
    votosSim() {
      if (this.resultado && this.resultado.numero_votos && typeof this.resultado.numero_votos.votos_sim !== 'undefined' && this.resultado.numero_votos.votos_sim !== null && this.resultado.numero_votos.votos_sim > 0) {
        return this.resultado.numero_votos.votos_sim;
      }
      return this.parlamentares ? this.parlamentares.filter(p => p.voto === 'Sim').length : 0;
    },
    votosNao() {
      if (this.resultado && this.resultado.numero_votos && typeof this.resultado.numero_votos.votos_nao !== 'undefined' && this.resultado.numero_votos.votos_nao !== null && this.resultado.numero_votos.votos_nao > 0) {
        return this.resultado.numero_votos.votos_nao;
      }
      return this.parlamentares ? this.parlamentares.filter(p => p.voto === 'Não').length : 0;
    },
    votosAbstencao() {
      if (this.resultado && this.resultado.numero_votos && typeof this.resultado.numero_votos.abstencoes !== 'undefined' && this.resultado.numero_votos.abstencoes !== null && this.resultado.numero_votos.abstencoes > 0) {
        return this.resultado.numero_votos.abstencoes;
      }
      return this.parlamentares ? this.parlamentares.filter(p => p.voto === 'Abstenção').length : 0;
    },
    totalVotos() {
      if (this.resultado && this.resultado.numero_votos && typeof this.resultado.numero_votos.total_votos !== 'undefined' && this.resultado.numero_votos.total_votos !== null && this.resultado.numero_votos.total_votos > 0) {
        return this.resultado.numero_votos.total_votos;
      }
      return this.votosSim + this.votosNao + this.votosAbstencao;
    }
  },
};
</script>

<style scoped>
.table-custom {
  color: #ddd;
}

.table-custom tbody td {
  padding: 8px;
  font-size: 1.1rem;
}

.table-sim {
  color: #27ae60;
}

.table-nao {
  color: #c0392b;
}

.table-abstencao {
  color: #f39c12;
}

.table-total {
  color: #194BFA;
}
</style>