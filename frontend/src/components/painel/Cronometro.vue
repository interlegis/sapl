<template>
  <div>
      <audio
      ref="player"
      :src="audioSrc"
      preload="auto"
    ></audio>
  <span ref="time">{{ title }}: {{ formatTime(time) }}<br/></span>
  </div>
</template>

<script>
export default {
  name: 'Cronometro',
  props: ['id', 'title'],
  data() {
    return {
      time: 300,
      isRunning: false,
      initialTime: 300,
      intervalId: null,
      audioSrc: require('@/assets/audio/ring.mp3'),
    }
  },
    mounted() {
        console.log('Cronometro mounted');
        console.log(this.audioSrc);
        this.$emit('child-mounted'); // Emit a custom event
    },
  methods: {
    changeFontSize(value) {
      const el = this.$refs.time;
      if (!el) return;
      let fontSize = window.getComputedStyle(el).fontSize;
      fontSize = parseFloat(fontSize); // safely convert "16px" → 16
      el.style.fontSize = (fontSize + value) + 'px';
    },
    handleStartStop() {
      this.isRunning = !this.isRunning;

      if (this.isRunning) {
        this.intervalId = setInterval(() => {
          if (this.time > 0) {
            this.time--;
            // play buzz at 00:00:30
            if (this.time == 30000) {
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

        const playPromise = audio.play()
    },

    formatTime(seconds) {
      const hrs = Math.floor(seconds / 3600);
      const mins = Math.floor((seconds % 3600) / 60);
      const secs = seconds % 60;

      if (hrs > 0) {
        return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
      }
      return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
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