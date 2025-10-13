<template v-if="sessao_aberta">
    <div>
        <div class="d-flex justify-content-center">
            <h1 id="sessao_plenaria" class="title text-title">{{ sessao_plenaria }} </h1>
        </div>
        <div class="row ">
            <div class="col text-center">
                <span id="sessao_plenaria_data" class="text-value"> Data Início: {{ sessao_plenaria_data }} </span>
            </div>
            <div class="col text-center">
                <span id="sessao_plenaria_hora_inicio" class="text-value"> Hora Início: {{ sessao_plenaria_hora_inicio }} </span>
            </div>
        </div>
        <div class="row justify-content-center">
            <div class="col-1">
                <img v-bind:src="brasao" id="logo-painel" class="logo-painel" alt=""/>
            </div>
        </div>
        <div class="row justify-content-center">
            <h2 class="text-danger"><span id="message">{{ message }}</span></h2>
        </div>

        <div class="row">
            <div class="col text-center"><span class="text-value data-hora" id="date">{{ data_atual }}</span></div>
            <div class="col text-center"><span class="text-value data-hora" id="relogio">{{ relogio }}</span></div>
        </div>
    </div>
</template>

<script>
import { mapState } from 'vuex';
export default {
  name: 'PainelHeader',
  props: {
  },

  data() {
    return {
      sessao_plenaria: "Sessao Plenaria Teste",
      sessao_plenaria_data: "22/10/2025",
      sessao_plenaria_hora_inicio: "13:30",
      brasao: "",
      data_atual: "",
      relogio: "",
      currentDateTimeId: null, // stores the id returned by setInterval()
    }
  },

  methods: {
    startCurrentDateTime() {
         this.data_atual = moment().utcOffset(-3).format("DD/MM/YY");  // RECOVER UTC OFFSET!!!!
         this.currentDateTimeId = setInterval(() => {
            this.relogio = moment.utc().utcOffset(-3).format("HH:mm:ss");
         }, 500);
    },
    beforeDestroy() {
        // Clear the interval before the component is destroyed
        if (this.currentDateTimeId) {
          clearInterval(this.currentDateTimeId);
          console.log('currentDateTimeId Interval cleared.');
        }
    },
  },
  computed: {
    ...mapState(["sessao_aberta", "painel_aberto", "message", "mostrar_voto"])
  },
  mounted() {
    console.log('PainelHeader component mounted');
    this.startCurrentDateTime();
  }
}
</script>