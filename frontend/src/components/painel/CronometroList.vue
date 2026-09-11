<template>
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
                        />
                        <Cronometro
                            ref="childRef_1"
                            id="aparte"
                            title="Aparte"
                            :visible="visibleCronometro === 'aparte'"
                            color-class="text-warning"
                            @child-mounted="handleChildMounted"
                        />
                        <Cronometro
                            ref="childRef_2"
                            id="ordem"
                            title="Questão de Ordem"
                            :visible="visibleCronometro === 'ordem'"
                            color-class="text-info"
                            @child-mounted="handleChildMounted"
                        />
                        <Cronometro
                            ref="childRef_3"
                            id="consideracoes"
                            title="Consid. Finais"
                            :visible="visibleCronometro === 'consideracoes'"
                            color-class=""
                            @child-mounted="handleChildMounted"
                        />
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</template>

<script>
    import { mapState } from 'pinia';
    import { usePainelStore } from '@/__apps/painel/store/painelStore';
    import Cronometro from './Cronometro.vue';

    export default {
        name: 'CronometroList',
        components: {
            Cronometro,
        },
        data() {
            return {
                visibleCronometro: 'discurso',
            }
        },
        mounted() {
          console.log('CronometroList mounted');
          // Sincroniza o estado inicial a partir do snapshot já presente
          // no store (não dá pra confiar num watcher `immediate` aqui:
          // ele dispararia em `created`, antes dos refs dos filhos
          // existirem).
          this.applyCronometroAction('childRef_0', this.cronometro_discurso);
          this.applyCronometroAction('childRef_1', this.cronometro_aparte);
          this.applyCronometroAction('childRef_2', this.cronometro_ordem);
          this.applyCronometroAction('childRef_3', this.cronometro_consideracoes);
        },
        computed: {
           ...mapState(usePainelStore, [
             "canRender",
             "cronometro_discurso", "cronometro_aparte",
             "cronometro_ordem", "cronometro_consideracoes"
           ])
        },
        watch: {
          // Só dispara em mudança de valor — o broadcast do painel chega a
          // cada voto/matéria aberta, não só em ações de cronômetro; um
          // toggle-em-toda-mensagem reiniciaria o cronômetro à toa.
          cronometro_discurso(newVal) { this.applyCronometroAction('childRef_0', newVal); },
          cronometro_aparte(newVal) { this.applyCronometroAction('childRef_1', newVal); },
          cronometro_ordem(newVal) { this.applyCronometroAction('childRef_2', newVal); },
          cronometro_consideracoes(newVal) { this.applyCronometroAction('childRef_3', newVal); },
        },
        methods: {
          applyCronometroAction(ref, action) {
            const comp = this.$refs[ref];
            if (!comp) return;
            if (action === 'start') {
              comp.start();
            } else if (action === 'stop') {
              comp.stop();
            } else if (action === 'reset') {
              comp.reset();
            }
            this.updateVisibility();
          },
          handleChildMounted() {
            console.log('Cronometro child mounted');
          },
          updateVisibility() {
            // Show priority: ordem > aparte > consideracoes > discurso
            const refs = [
              { key: 'ordem', ref: 'childRef_2' },
              { key: 'aparte', ref: 'childRef_1' },
              { key: 'consideracoes', ref: 'childRef_3' },
              { key: 'discurso', ref: 'childRef_0' },
            ];
            for (const item of refs) {
              const comp = this.$refs[item.ref];
              if (comp && comp.isRunning) {
                this.visibleCronometro = item.key;
                return;
              }
            }
            // Default to discurso if none running
            this.visibleCronometro = 'discurso';
          }
        },
    };
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

