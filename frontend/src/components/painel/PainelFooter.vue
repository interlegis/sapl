<template>
    <div class="painel position-relative bottom-0 hora-brasao">
        <div class="row justify-content-center align-items-center">
            <div class="col-4 text-center" id="logo-container" v-if="brasao">
                <img :src="brasao" id="logo-painel" class="logo-painel" alt="Brasão" />
            </div>
            <div :class="['text-center', brasao ? 'col-4' : 'col-12 mt-5']" id="relogio-container">
                <span class="fs-1 fw-bold" id="relogio">{{ relogio }}</span>
            </div>
        </div>
    </div>
</template>

<script>
import { mapState } from 'vuex';
export default {
  name: 'PainelFooter',
  props: {
  },

  data() {
    return {
      brasao: "",
      data_atual: "",
      relogio: "",
      currentDateTimeId: null,
    }
  },

  methods: {
    startCurrentDateTime() {
         this.data_atual = moment().utcOffset(-3).format("DD/MM/YY");
         this.currentDateTimeId = setInterval(() => {
            this.relogio = moment.utc().utcOffset(-3).format("HH:mm:ss");
         }, 500);
    },
  },
  beforeDestroy() {
      if (this.currentDateTimeId) {
        clearInterval(this.currentDateTimeId);
        console.log('currentDateTimeId Interval cleared.');
      }
  },
  computed: {
    ...mapState(["sessao_aberta", "painel_aberto"])
  },
  mounted() {
    console.log('PainelFooter component mounted');
    this.startCurrentDateTime();
  }
}
</script>

<style scoped>
.logo-painel {
  max-height: 150px;
  width: auto;
}
.hora-brasao {
  border-top: 1px solid #333;
}
</style>