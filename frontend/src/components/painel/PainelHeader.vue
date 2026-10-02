<template>
    <div>
        <h1 id="sessao_plenaria" class="text-title fw-bold text-uppercase">{{ sessao_plenaria }}</h1>
        <h2 class="text-danger" v-if="message"><span id="message">{{ message }}</span></h2>
    </div>
</template>

<script>
import { mapState } from 'pinia';
import { usePainelStore } from '@/__apps/painel/store/painelStore';
export default {
  name: 'PainelHeader',
  props: {
  },

  methods: {
  },
  computed: {
    ...mapState(usePainelStore, {
      sessao_aberta: 'sessao_aberta',
      message: 'message',
      sessao_plenaria: (store) => (store.sessao && store.sessao.sessao_plenaria) || '',
    })
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