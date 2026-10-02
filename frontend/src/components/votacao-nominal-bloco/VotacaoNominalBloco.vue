<template>
    <div>
        <fieldset class="form-group">
            <legend>Votos:</legend>
            <div class="row">
                <template v-for="p in parlamentares">
                    <div class="col-md-4" id="styleparlamentar" :key="'nome_' + p.parlamentar_id">
                        {{ p.nome_parlamentar }}
                    </div>
                    <div class="col-md-5" :key="'voto_' + p.parlamentar_id">
                        <input v-if="p.voto" type="hidden" name="voto_parlamentar"
                               :value="p.voto + ':' + p.parlamentar_id">
                        <select class="form-control"
                                :name="p.voto ? null : 'voto_parlamentar'"
                                :disabled="!!p.voto"
                                v-model="votos[p.parlamentar_id]">
                            <option :value="'Não Votou:' + p.parlamentar_id">Não Votou</option>
                            <option :value="'Sim:' + p.parlamentar_id">Sim</option>
                            <option :value="'Não:' + p.parlamentar_id">Não</option>
                            <option :value="'Abstenção:' + p.parlamentar_id">Abstenção</option>
                        </select>
                    </div>
                </template>
            </div>
            <br>
            <legend>Situação da Votação:</legend>
            <div id="soma_votos">
                <div class="row"><div class="col-md-12">Sim: {{ tally.sim }}</div></div>
                <div class="row"><div class="col-md-12">Não: {{ tally.nao }}</div></div>
                <div class="row"><div class="col-md-12">Abstenções: {{ tally.abstencao }}</div></div>
                <div class="row"><div class="col-md-12">Ainda não votaram: {{ tally.naoVotou }}</div></div>
            </div>
            <input type="hidden" name="votos_sim" :value="tally.sim">
            <input type="hidden" name="votos_nao" :value="tally.nao">
            <input type="hidden" name="abstencoes" :value="tally.abstencao">
            <input type="hidden" name="nao_votou" :value="tally.naoVotou">
        </fieldset>
    </div>
</template>

<script>
export default {
  name: 'VotacaoNominalBloco',
  props: {
    parlamentares: {
      type: Array,
      default: () => []
    }
  },
  data () {
    const votos = {}
    this.parlamentares.forEach((p) => {
      votos[p.parlamentar_id] = (p.voto || 'Não Votou') + ':' + p.parlamentar_id
    })
    return { votos }
  },
  computed: {
    // Substitui o antigo setTimeout(conta_votos, 500), que recontava o
    // DOM inteiro a cada 500ms — a reatividade do Vue já refaz esta conta
    // sozinha quando qualquer <select> muda, sem timer nenhum.
    tally () {
      const t = { sim: 0, nao: 0, abstencao: 0, naoVotou: 0 }
      this.parlamentares.forEach((p) => {
        const valor = (this.votos[p.parlamentar_id] || '').split(':')[0]
        if (valor === 'Sim') t.sim++
        else if (valor === 'Não') t.nao++
        else if (valor === 'Abstenção') t.abstencao++
        else t.naoVotou++
      })
      return t
    }
  }
}
</script>
