<template>
    <div class="container-fluid text-center py-4">
        <template v-if="!errorMessage">
            <h1 class="mb-3">{{ sessaoPlenaria }}</h1>

            <h2 class="mb-3">
                Voto:
                <span :class="votoColorClass">{{ votoParlamentar }}</span>
            </h2>
            <p v-if="statusMessage" class="text-info">{{ statusMessage }}</p>

            <div class="my-4">
                <h3 class="mb-2">Matéria em Votação</h3>
                <div class="fs-4">{{ materia.texto }}</div>
                <div class="fs-6 fst-italic">{{ materia.ementa }}</div>
            </div>

            <form method="POST" :action="voteActionUrl">
                <input type="hidden" name="csrfmiddlewaretoken" :value="csrfToken">
                <div class="d-flex justify-content-center gap-3 flex-wrap">
                    <button type="submit" name="voto" value="Sim" class="btn btn-lg btn-success btn-voto">Sim</button>
                    <button type="submit" name="voto" value="Não" class="btn btn-lg btn-danger btn-voto">Não</button>
                    <button type="submit" name="voto" value="Abstenção" class="btn btn-lg btn-secondary btn-voto">Abstenção</button>
                </div>
            </form>
        </template>

        <template v-else>
            <h1 class="my-5">⏸</h1>
            <h2 class="text-warning">{{ errorMessage }}</h2>
        </template>

        <div class="mt-5">
            <button type="button" class="btn btn-lg btn-primary me-2" @click="reload">Atualizar</button>
            <button type="button" class="btn btn-lg btn-secondary" @click="closeWindow">Sair</button>
        </div>
    </div>
</template>

<script>
import { mapState } from 'pinia'
import { usePainelStore } from '@/__apps/painel/store/painelStore'

export default {
  name: 'VotoIndividual',
  data () {
    return {
      materiaId: '',
      errorMessage: '',
      statusMessage: '',
      votoParlamentar: '',
      csrfToken: ''
    }
  },
  computed: {
    ...mapState(usePainelStore, ['materia', 'sessao']),
    sessaoPlenaria () {
      return this.sessao && this.sessao.sessao_plenaria
    },
    voteActionUrl () {
      return window.VOTO_INDIVIDUAL_URL
    },
    votoColorClass () {
      if (this.votoParlamentar === 'Sim') return 'text-success'
      if (this.votoParlamentar === 'Não') return 'text-danger'
      if (this.votoParlamentar === 'Abstenção') return 'text-white'
      return ''
    }
  },
  mounted () {
    const el = document.getElementById('csrf-token')
    this.csrfToken = el ? el.value : ''
  },
  methods: {
    reload () {
      document.location.reload()
    },
    closeWindow () {
      window.close()
    }
  }
}
</script>
