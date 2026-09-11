// frontend/src/__apps/painel/store/painelStore.js
//
// Store Pinia do painel. Substitui o store Vuex inline: um único ponto de
// entrada (`applyData`), alimentado pelo payload normalizado a partir do
// full-snapshot broadcast do backend (sapl/painel/views.py::
// build_dados_painel()) — não há mais eventos incrementais
// (`vote.update`/`stopwatch.update`); qualquer mudança de estado é
// republicada como um novo snapshot completo.

import { defineStore } from 'pinia'
import { DEFAULT_STATE, normalizePainelData } from '../ws/normalizePainel'

function deepClone (x) {
  return JSON.parse(JSON.stringify(x))
}

export const usePainelStore = defineStore('painel', {
  state: () => deepClone(DEFAULT_STATE),

  getters: {
    canRender: (s) => !!(s.sessao_aberta && s.painel_aberto),

    // Getters usados pelo app `votacao` (apuração ao vivo a partir dos votos).
    totalVotos: (s) => {
      const totals = [
        { tipo: 'Sim', total: 0 },
        { tipo: 'Não', total: 0 },
        { tipo: 'Abstenção', total: 0 },
        { tipo: 'Não Votou', total: 0 }
      ]
      s.parlamentares.forEach((p) => {
        if (p.voto) {
          const entry = totals.find((t) => t.tipo === p.voto)
          if (entry) entry.total++
        }
      })
      return totals
    },
    numPresentes: (s) => s.parlamentares.length,
    totalVotados: (s) =>
      s.parlamentares.filter((p) => p.voto && p.voto !== 'Não Votou').length
  },

  actions: {
    // Aplica o payload completo (`type: "data"`) do WebSocket.
    applyData (raw) {
      const next = normalizePainelData(raw)

      // flags simples
      this.sessao_aberta = next.sessao_aberta
      this.painel_aberto = next.painel_aberto
      this.mostrar_voto = next.mostrar_voto
      this.message = next.message

      // objeto aninhado: patch (preserva reatividade dos campos)
      Object.assign(this.sessao, next.sessao)

      // cronômetros: só start/stop/reset explícitos (ver Cronometro.vue/
      // CronometroList.vue) reagem a mudança de valor — nunca a um toggle
      // por broadcast, que dispara em qualquer voto/matéria aberta, não só
      // em ações de cronômetro.
      this.cronometro_discurso = next.cronometro_discurso
      this.cronometro_aparte = next.cronometro_aparte
      this.cronometro_ordem = next.cronometro_ordem
      this.cronometro_consideracoes = next.cronometro_consideracoes

      // arrays: trocar referência (voto já vem aplicado por parlamentar
      // dentro de next.parlamentares — get_votos() no backend já inlina o
      // voto de cada presente, não há mais um mapa separado a reaplicar)
      this.parlamentares = next.parlamentares
      this.oradores = next.oradores

      // objetos grandes: substituir
      this.materia = next.materia
      this.resultado = next.resultado

      // tipos de resultado (app votacao): nunca vem no broadcast do
      // WebSocket (ver GAP 3 do plano de merge) — só sobrescreve quando o
      // payload realmente traz a lista, preservando o valor populado uma
      // vez a partir do contexto inicial renderizado pelo Django.
      if (next.tipos_resultado && next.tipos_resultado.length) {
        this.tipos_resultado = next.tipos_resultado
      }
    }
  }
})
