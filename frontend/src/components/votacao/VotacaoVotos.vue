<template>
    <fieldset class="form-group" v-if="parlamentares && parlamentares.length > 0">
        <legend>Votos</legend>
        <div class="row">
            <template v-for="p in parlamentares">
                <div class="col-md-4" id="styleparlamentar" :key="'nome_' + p.parlamentar_id">
                    {{ p.nome_parlamentar }}
                </div>
                <div class="col-md-5" :key="'voto_' + p.parlamentar_id">
                    <select class="form-control"
                            :name="'voto_parlamentar_' + p.parlamentar_id"
                            :value="p.voto || 'Não Votou'"
                            @change="onVoteChange(p.parlamentar_id, $event.target.value)">
                        <option value="Não Votou">Não Votou</option>
                        <option value="Sim">Sim</option>
                        <option value="Não">Não</option>
                        <option value="Abstenção">Abstenção</option>
                    </select>
                </div>
            </template>
        </div>
    </fieldset>
    <div class="alert alert-info alert-dismissible" role="alert" v-else>
        <div>Não existe nenhum parlamentar presente para que a votação ocorra.</div>
    </div>
</template>

<script>
import { mapState } from 'vuex';
export default {
  name: 'VotacaoVotos',
  computed: {
    ...mapState(['parlamentares'])
  },
  methods: {
    onVoteChange(parlamentar_id, voto) {
      this.$emit('cast-vote', { parlamentar_id, voto });
    }
  },
  mounted() {
    console.log('VotacaoVotos mounted');
  }
};
</script>
