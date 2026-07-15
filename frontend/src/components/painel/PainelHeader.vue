<template>
    <div>
        <h1 id="sessao_plenaria" class="text-title fw-bold text-uppercase">{{ sessao_plenaria }}</h1>
        <h2 class="text-danger" v-if="message"><span id="message">{{ message }}</span></h2>
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
      sessao_plenaria: "",
    }
  },

  methods: {
  },
  computed: {
    ...mapState(["sessao_aberta", "message"])
  },
  mounted() {
    console.log('PainelHeader component mounted');
  }
}
</script>

<style scoped>
.text-title {
  color: var(--text-highlight);
  letter-spacing: 1px;
}
</style>