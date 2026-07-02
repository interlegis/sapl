<template>
    <div v-if="materia && materia.texto">
        <div>
            Matéria: {{ materia.texto }}
            <br />
            Ementa: {{ materia.ementa }}
        </div>
    </div>
    <div v-else class="alert alert-info">
        Nenhuma matéria aberta para votação.
    </div>
</template>

<script>
import { mapState } from 'vuex';
export default {
  name: 'VotacaoMateria',
  computed: {
    ...mapState(['materia'])
  },
  mounted() {
    console.log('VotacaoMateria mounted');
  }
};
</script>
