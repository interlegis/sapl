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
                            :value="votosStatus[p.parlamentar_id] || 'Não Votou'"
                            :disabled="!!votosTravados[p.parlamentar_id]"
                            @change="onVoteChange(p.parlamentar_id, $event.target.value)">
                        <option value="Não Votou">Não Votou</option>
                        <option value="Sim">Sim</option>
                        <option value="Não">Não</option>
                        <option value="Abstenção">Abstenção</option>
                    </select>
                    <span v-if="votosTravados[p.parlamentar_id]" class="badge badge-info">Já votado (tablet)</span>
                </div>
            </template>
        </div>
    </fieldset>
    <div class="alert alert-info alert-dismissible" role="alert" v-else>
        <div>Não existe nenhum parlamentar presente para que a votação ocorra.</div>
    </div>
</template>

<script>
import { mapState } from 'pinia';
import { usePainelStore } from '@/__apps/painel/store/painelStore';
export default {
  name: 'VotacaoVotos',
  props: {
    // Estado real (não mascarado por mostrar_voto) de quem já votou, por
    // parlamentar_id — nunca vem do store (visão pública do painel).
    votosStatus: {
      type: Object,
      default: () => ({})
    },
    // Quais parlamentar_id devem ficar travados pro operador — só quando
    // votado_pelo_parlamentar é true no payload (voto pelo próprio
    // tablet). Distinto de votosStatus: um voto lançado pelo operador
    // neste mesmo <select> também aparece em votosStatus (tem valor), mas
    // não deve se autotravar.
    votosTravados: {
      type: Object,
      default: () => ({})
    }
  },
  computed: {
    ...mapState(usePainelStore, ['parlamentares'])
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
