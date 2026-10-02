<template>
    <div v-if="status !== 'open'" class="ws-status-banner" :class="bannerClass">
        {{ message }}
    </div>
</template>

<script>
export default {
  name: 'WsStatusBanner',
  props: {
    // 'connecting' | 'open' | 'reconnecting' | 'error'
    status: { type: String, default: 'connecting' },
    message: { type: String, default: 'Conectando ao servidor de tempo real…' }
  },
  computed: {
    bannerClass () {
      return this.status === 'error' ? 'ws-status-banner--error' : 'ws-status-banner--warning'
    }
  }
}
</script>

<style scoped>
.ws-status-banner {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 2000;
  padding: 10px 16px;
  text-align: center;
  font-weight: bold;
  color: #fff;
}
.ws-status-banner--warning {
  background: #b8860b;
}
.ws-status-banner--error {
  background: #b00020;
}
</style>
