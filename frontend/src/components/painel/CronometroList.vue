<template>
    <!--
      v-if="canRender": cronômetros só aparecem quando o painel estiver aberto.
      Enquanto o painel está fechado, os componentes não são montados e portanto
      nenhum timer roda em background.
    -->
    <div class="painel d-flex flex-column" v-if="canRender">
        <div id="box_cronometros" class="w-100">
            <h2 class="text-center text-subtitle mb-3">Cronômetro</h2>
            <div class="d-flex align-items-center justify-content-center" style="height: 80px">
                <table class="table-custom w-100 mb-0">
                    <tbody>
                        <Cronometro
                            ref="childRef_0"
                            id="discurso"
                            title="Discurso"
                            :visible="visibleCronometro === 'discurso'"
                            color-class=""
                            @child-mounted="handleChildMounted"
                            @state-changed="handleStateChanged"
                        />
                        <Cronometro
                            ref="childRef_1"
                            id="aparte"
                            title="Aparte"
                            :visible="visibleCronometro === 'aparte'"
                            color-class="text-warning"
                            @child-mounted="handleChildMounted"
                            @state-changed="handleStateChanged"
                        />
                        <Cronometro
                            ref="childRef_2"
                            id="ordem"
                            title="Questão de Ordem"
                            :visible="visibleCronometro === 'ordem'"
                            color-class="text-info"
                            @child-mounted="handleChildMounted"
                            @state-changed="handleStateChanged"
                        />
                        <Cronometro
                            ref="childRef_3"
                            id="consideracoes"
                            title="Consid. Finais"
                            :visible="visibleCronometro === 'consideracoes'"
                            color-class=""
                            @child-mounted="handleChildMounted"
                            @state-changed="handleStateChanged"
                        />
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</template>

<script>
import { mapState } from 'pinia'
import { usePainelStore } from '@/__apps/painel/store/painelStore'
import Cronometro from './Cronometro.vue'

export default {
  name: 'CronometroList',
  components: {
    Cronometro
  },
  data () {
    return {
      // Qual cronômetro está visível no momento.
      // Regra de prioridade ao rodar: ordem > aparte > consideracoes > discurso.
      // Quando nenhum está rodando: mantém o último visível (para mostrar
      // o tempo "parado" do cronômetro que acabou de ser parado).
      visibleCronometro: 'discurso',
      childrenMounted: 0,
      allChildrenMounted: false
    }
  },
  mounted () {
    console.log('CronometroList mounted')
    // Os filhos podem não ter montado ainda — aplica via nextTick após
    // todos os filhos emitirem 'child-mounted' (ver handleChildMounted).
  },
  computed: {
    ...mapState(usePainelStore, [
      'canRender',
      'cronometro_ativo',
      'cronometro_discurso', 'cronometro_aparte',
      'cronometro_ordem', 'cronometro_consideracoes'
    ])
  },
  watch: {
    // Quando o painel abre (canRender muda para true), os filhos
    // acabam de montar — aplica o estado inicial de todos.
    canRender (newVal) {
      if (newVal) {
        this.$nextTick(() => this.applyAllStates())
      }
    },

    cronometro_ativo (newVal) {
      if (newVal) {
        this.updateVisibility()
      }
    },

    // Watchers profundos para cada cronômetro: disparam quando o objeto
    // mudar (nova action, duration, etc.) mas NÃO quando o broadcast
    // chega com o mesmo valor (deep watch compara referência, mas o
    // store substitui o objeto inteiro — a comparação de ação é feita
    // dentro de applyState do filho para ser idempotente).
    cronometro_discurso (newVal) {
      this.applyOneState('childRef_0', newVal)
    },
    cronometro_aparte (newVal) {
      this.applyOneState('childRef_1', newVal)
    },
    cronometro_ordem (newVal) {
      this.applyOneState('childRef_2', newVal)
    },
    cronometro_consideracoes (newVal) {
      this.applyOneState('childRef_3', newVal)
    }
  },
  methods: {
    /**
           * Aplica o estado de todos os cronômetros de uma vez.
           * Usado na montagem e quando o painel é aberto.
           */
    applyAllStates () {
      this.applyOneState('childRef_0', this.cronometro_discurso)
      this.applyOneState('childRef_1', this.cronometro_aparte)
      this.applyOneState('childRef_2', this.cronometro_ordem)
      this.applyOneState('childRef_3', this.cronometro_consideracoes)
      this.updateVisibility()
    },

    /**
           * Aplica o estado de um único cronômetro chamando applyState() no filho.
           * @param {string} refName - nome do ref ('childRef_0' etc.)
           * @param {Object|null} state - { action, duration, start_ts?, remaining_at_stop? }
           */
    applyOneState (refName, state) {
      const comp = this.$refs[refName]
      if (!comp) return
      comp.applyState(state)
      this.updateVisibility()
    },

    /**
           * Chamado quando um filho monta. Quando todos os 4 filhos
           * montaram, aplica o estado inicial.
           */
    handleChildMounted () {
      this.childrenMounted++
      console.log(`Cronometro child mounted (${this.childrenMounted}/4)`)
      if (this.childrenMounted >= 4) {
        this.allChildrenMounted = true
        this.applyAllStates()
      }
    },

    /**
           * Chamado quando um filho muda de estado (start/stop).
           * Atualiza a visibilidade.
           */
    handleStateChanged () {
      this.updateVisibility()
    },

    /**
           * Decide qual cronômetro mostrar.
           *
           * Prioridade ao rodar: ordem > aparte > consideracoes > discurso.
           * Se nenhum estiver rodando, mantém o último visível para exibir
           * o tempo no momento em que foi parado (comportamento igual ao discurso).
           */
    updateVisibility () {
      // Prioridade 1: se algum cronômetro estiver rodando, mostra o que está rodando
      const priority = [
        { key: 'ordem', ref: 'childRef_2' },
        { key: 'aparte', ref: 'childRef_1' },
        { key: 'consideracoes', ref: 'childRef_3' },
        { key: 'discurso', ref: 'childRef_0' }
      ]
      for (const item of priority) {
        const comp = this.$refs[item.ref]
        if (comp && comp.isRunning) {
          this.visibleCronometro = item.key
          return
        }
      }

      // Prioridade 2: nenhum rodando. Mostra o último cronômetro operado pelo operador
      if (this.cronometro_ativo) {
        this.visibleCronometro = this.cronometro_ativo
        return
      }

      // Fallback padrão
      this.visibleCronometro = 'discurso'
    }
  }
}
</script>

<style scoped>
.table-custom {
  color: #ddd;
}
::v-deep .table-custom tbody td {
  padding: 8px;
  font-size: 1.1rem;
}
</style>
