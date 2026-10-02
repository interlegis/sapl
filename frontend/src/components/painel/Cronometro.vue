<template>
  <tr :id="'row_' + id" v-show="visible">
    <td :class="['fs-3', titleColorClass]">{{ title }}</td>
    <td class="text-end">
      <audio ref="player" :src="audioSrc" preload="auto"></audio>
      <span :id="'cronometro_' + id"
            :class="['fw-bold', 'font-monospace', 'fs-1', titleColorClass]"
            ref="time">{{ formatTime(time) }}</span>
    </td>
  </tr>
</template>

<script>
export default {
  name: 'PainelCronometro',
  props: ['id', 'title', 'visible', 'colorClass'],
  data () {
    return {
      time: 300,
      isRunning: false,
      initialTime: 300,
      intervalId: null,
      audioSrc: require('@/assets/audio/ring.mp3')
    }
  },
  computed: {
    titleColorClass () {
      return this.colorClass || ''
    }
  },
  mounted () {
    console.log('Cronometro mounted')
    this.$emit('child-mounted')
  },
  methods: {
    changeFontSize (value) {
      const el = this.$refs.time
      if (!el) return
      let fontSize = window.getComputedStyle(el).fontSize
      fontSize = parseFloat(fontSize)
      el.style.fontSize = (fontSize + value) + 'px'
    },

    /**
     * Aplica o estado completo recebido do backend.
     *
     * @param {Object} state - { action, duration, start_ts?, remaining_at_stop? }
     *
     * Lógica:
     *  - reset / sem estado  → para, define time = duration
     *  - stop                → para, define time = remaining_at_stop (tempo no momento do stop)
     *  - start               → calcula tempo restante a partir de start_ts + duration - agora
     *                          e inicia a contagem (idempotente: se já estiver rodando com
     *                          o mesmo start_ts, não reinicia)
     */
    applyState (state) {
      if (!state || !state.action) {
        // Sem estado: apenas configura a duração e para
        this.stop()
        this.time = this.initialTime
        return
      }

      const { action, duration, start_ts, remaining_at_start, remaining_at_stop } = state

      // Atualiza a duração configurada
      if (duration != null) {
        this.initialTime = duration
      }

      if (action === 'reset') {
        this.stop()
        this.time = this.initialTime
      } else if (action === 'stop') {
        this.stop()
        // Mostra o tempo exato em que o operador parou o cronômetro
        if (remaining_at_stop != null) {
          this.time = Math.max(0, Math.round(remaining_at_stop))
        }
      } else if (action === 'start') {
        // Calcula o tempo restante a partir de remaining_at_start e start_ts
        const nowSec = Date.now() / 1000
        const elapsed = start_ts != null ? Math.max(0, nowSec - start_ts) : 0
        const baseRem = remaining_at_start != null
          ? remaining_at_start
          : (remaining_at_stop != null
              ? remaining_at_stop
              : (this.time > 0 && this.time < this.initialTime ? this.time : this.initialTime))
        const remaining = Math.max(0, baseRem - elapsed)

        // Idempotente: se já estiver rodando e a contagem estiver em sincronia
        // (diferença <= 2s), mantém o intervalo nativo para não ter saltos
        if (!this.isRunning || Math.abs(this.time - remaining) > 2) {
          this.stop()
          this.time = Math.round(remaining)
          if (remaining > 0) {
            this._startInterval()
          }
        }
      }

      this.$emit('state-changed', { id: this.id, isRunning: this.isRunning })
    },

    _startInterval () {
      this.isRunning = true
      this.intervalId = setInterval(() => {
        if (this.time > 0) {
          this.time--
          if (this.time === 30) {
            this.playSound()
          }
        } else {
          this.isRunning = false
          clearInterval(this.intervalId)
          this.playSound()
          this.$emit('state-changed', { id: this.id, isRunning: false })
        }
      }, 1000)
    },

    // start/stop/reset legados mantidos para compatibilidade com qualquer
    // chamador externo, mas internamente agora delegam para applyState().
    start () {
      if (this.isRunning) return
      this._startInterval()
    },

    stop () {
      this.isRunning = false
      clearInterval(this.intervalId)
      this.intervalId = null
    },

    reset () {
      this.stop()
      this.time = this.initialTime
    },

    playSound () {
      const audio = this.$refs.player
      if (!audio) return
      audio.play()
    },

    formatTime (seconds) {
      const hrs = Math.floor(seconds / 3600)
      const mins = Math.floor((seconds % 3600) / 60)
      const secs = seconds % 60
      return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
    }
  },
  watch: {
    initialTime (newVal) {
      if (!this.isRunning) {
        this.time = newVal
      }
    }
  },
  beforeDestroy () {
    clearInterval(this.intervalId)
  }
}
</script>

<style scoped>
/* Add your own styles here */
</style>
