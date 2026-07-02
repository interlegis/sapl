<template>
    <div v-if="parlamentares && parlamentares.length > 0">
        <div class="row">
            <div class="col-md-12">
                <label for="resultado_votacao"><strong>Resultado da Votação</strong></label>
                <select v-model="resultadoSelecionado" id="resultado_votacao" class="select form-control" :disabled="disabled">
                    <option value="">---------</option>
                    <option v-for="tipo in tipos_resultado"
                            :key="tipo.id"
                            :value="tipo.id">
                        {{ tipo.nome }}
                    </option>
                </select>
            </div>
        </div>

        <br />
        <div class="row">
            <div class="col-md-12">
                Observações<br/>
                <textarea id="observacao" v-model="textoObservacoes" style="width:100%;" rows="7"></textarea>
            </div>
        </div>

        <br /><br />
        <div class="row">
            <div class="col-md-12">
                <div class="form-group row justify-content-between">
                    <input type="button" id="cancelar-votacao" value="Cancelar Votação"
                           class="btn btn-warning" @click="$emit('cancelar')" />
                    <input type="button" id="salvar-votacao" value="Fechar Votação"
                           class="btn btn-primary" @click="$emit('fechar')" />
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import { mapState } from 'vuex';
export default {
  name: 'VotacaoObservacoes',
  props: {
    disabled: {
      type: Boolean,
      default: false
    },
    observacoes: {
      type: String,
      default: ''
    },
    resultadoSelected: {
      type: [String, Number],
      default: ''
    }
  },
  data() {
    return {
      textoObservacoes: this.observacoes,
      resultadoSelecionado: this.resultadoSelected,
    }
  },
  watch: {
    observacoes(val) {
      this.textoObservacoes = val;
    },
    textoObservacoes(val) {
      this.$emit('update:observacoes', val);
    },
    resultadoSelected(val) {
      this.resultadoSelecionado = val;
    },
    resultadoSelecionado(val) {
      this.$emit('update:resultadoSelected', val);
    }
  },
  computed: {
    ...mapState(['parlamentares', 'tipos_resultado'])
  },
  mounted() {
    console.log('VotacaoObservacoes mounted');
  }
};
</script>
