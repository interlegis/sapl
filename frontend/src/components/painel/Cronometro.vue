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
  name: 'Cronometro',
  props: ['id', 'title', 'visible', 'colorClass'],
  data() {
    return {
      time: 300,
      isRunning: false,
      initialTime: 300,
      intervalId: null,
      audioSrc: require('@/assets/audio/ring.mp3'),
    }
  },
  computed: {
    titleColorClass() {
      return this.colorClass || '';
    }
  },
  mounted() {
      console.log('Cronometro mounted');
      this.$emit('child-mounted');
  },
  methods: {
    changeFontSize(value) {
      const el = this.$refs.time;
      if (!el) return;
      let fontSize = window.getComputedStyle(el).fontSize;
      fontSize = parseFloat(fontSize);
      el.style.fontSize = (fontSize + value) + 'px';
    },
    handleStartStop() {
      this.isRunning = !this.isRunning;

      if (this.isRunning) {
        this.intervalId = setInterval(() => {
          if (this.time > 0) {
            this.time--;
            if (this.time == 30) {
                this.playSound();
            }
          } else {
            this.isRunning = false;
            clearInterval(this.intervalId);
            this.playSound();
          }
        }, 1000);
      } else {
        clearInterval(this.intervalId);
      }
    },

    handleReset() {
      this.isRunning = false;
      clearInterval(this.intervalId);
      this.time = this.initialTime;
    },

    playSound() {
        const audio = this.$refs.player
        if (!audio) return
        audio.play()
    },

    formatTime(seconds) {
      const hrs = Math.floor(seconds / 3600);
      const mins = Math.floor((seconds % 3600) / 60);
      const secs = seconds % 60;
      return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
  },
  watch: {
    initialTime(newVal) {
      if (!this.isRunning) {
        this.time = newVal;
      }
    }
  },
  beforeDestroy() {
    clearInterval(this.intervalId);
  }
}
</script>

<style scoped>
/* Add your own styles here */
</style>