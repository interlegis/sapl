<template>
    <div id="parlamentares">
        <div class="container-fluid" id="parlamentares_container" v-if="canRender">
            <div class="parlamentares-grid" id="parlamentares_row">
                <div v-for="p in parlamentares"
                     :key="p.parlamentar_id"
                     :class="['parlamentar-card', 'mt-3', votoClass(p)]">
                    <div class="voto-faixa" v-if="votoText(p)">
                        <p>{{ votoText(p) }}</p>
                    </div>

                    <div class="foto-container">
                        <img :src="p.fotografia || defaultAvatar" :alt="p.nome_parlamentar">
                    </div>

                    <div class="mt-2 text-center">
                        <div class="nome">{{ p.nome_parlamentar }}</div>
                        <div class="partido">{{ p.filiacao }}</div>
                    </div>
                </div>
            </div>
        </div>
        <span class="text-white" v-else>
            <center>A listagem de parlamentares só aparecerá quando o painel estiver aberto.</center>
        </span>
    </div>
</template>

<script>
import { mapState } from 'vuex';
import defaultAvatarImg from '@/assets/img/avatar.png';

export default {
  name: 'PainelParlamentares',
  data() {
    return {
      defaultAvatar: defaultAvatarImg,
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
  methods: {
    votoClass(parlamentar) {
      const voto = parlamentar.voto;
      if (!voto) return '';
      if (this.mostrar_voto) {
        if (voto === 'Sim') return 'voto-sim';
        if (voto === 'Não') return 'voto-nao';
        if (voto === 'Abstenção') return 'voto-abstencao';
      } else {
        if (voto === 'Sim' || voto === 'Não' || voto === 'Abstenção' || voto === 'Voto Informado') {
          return 'voto-informado';
        }
      }
      return '';
    },
    votoText(parlamentar) {
      const voto = parlamentar.voto;
      if (!voto) return '';
      if (this.mostrar_voto) {
        if (voto === 'Sim') return 'S';
        if (voto === 'Não') return 'N';
        if (voto === 'Abstenção') return 'A';
      } else {
        if (voto === 'Sim' || voto === 'Não' || voto === 'Abstenção' || voto === 'Voto Informado') {
          return 'I';
        }
      }
      return '';
    },
  },
};
</script>

<style scoped>
.parlamentares-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, 190px);
  width: 100%;
}

.parlamentar-card {
  width: 150px;
  border-radius: 3px;
  overflow: hidden;
  position: relative;
}

.foto-container {
  border-radius: 3px;
  overflow: hidden;
  height: 150px;
}

.parlamentar-card img {
  width: 100%;
  height: 150px;
  display: block;
  object-fit: fill;
}

.parlamentar-card .nome {
  font-weight: bold;
  font-size: 0.95rem;
  color: #fff;
  line-height: 1.1;
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.8);
  margin-bottom: 2px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.parlamentar-card .partido {
  font-size: 0.8rem;
  color: #ddd;
  font-weight: 600;
  text-transform: uppercase;
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.8);
}

.voto-faixa {
  position: absolute;
  width: 90px;
  height: 90px;
  top: -45px;
  right: -45px;
  transform: rotate(45deg);
  display: flex;
  align-items: flex-end;
  justify-content: center;
  color: #fff;
  font-weight: 700;
  box-shadow: -2px 2px 5px rgba(0, 0, 0, 0.2);
  z-index: 10;
  line-height: 1;
}

.voto-faixa p {
  transform: rotate(-45deg);
  font-size: 2rem;
  text-transform: uppercase;
}

.voto-sim .voto-faixa {
  background-color: #27ae60;
}

.voto-nao .voto-faixa {
  background-color: #c0392b;
}

.voto-abstencao .voto-faixa {
  background-color: #f39c12;
}

.voto-informado .voto-faixa {
  background-color: #d35400;
}

.voto-ausente .voto-faixa {
  background-color: #7f8c8d;
}
</style>