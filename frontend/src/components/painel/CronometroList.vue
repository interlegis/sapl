.<template>
    <div class="col-md-6 text-left painel" v-if="canRender">
        <div class="d-flex align-items-left justify-content-left mb-2">
            <h2 class="text-subtitle mb-0">Cronômetros</h2>
        </div>
        <div class="text-value" id="box_cronometros">
            <Cronometro v-for="(title, idx) in titles" :key="idx" :title="title" :ref="'childRef_' + idx" @child-mounted="handleChildMounted"/>
        </div>
    </div>
</template>

<script>
    import { ref, onMounted } from 'vue';
    import { mapState } from 'vuex';
    import Cronometro from './Cronometro.vue';

    export default {
        name: 'CronometroList',
        components: {
            Cronometro,
        },
        data() {
            return {
                titles: ["Discurso", "Aparte", "Questão de Ordem", "Considerações Finais"],
                itemRefs: ref([]), // An array to store the refs
            }
        },
        mounted() {
          console.log('CronometroList mounted');
        },
        computed: {
            canRender () {
                return this.sessao_aberta && this.painel_aberto;
            },
           ...mapState(["painel_aberto", "sessao_aberta"])
        },
        methods: {
          handleStartStop() {
             console.log("start/stop stopwatch");
             //console.log(this.$refs.itemRefs);
          },
          handleChildMounted() {
            console.log('ChildComponent has finished mounting in the parent!');
            // Perform actions in the parent that depend on the child being fully mounted
            const childId = 0;
            const childComponent = this.$refs['childRef_' + childId];
            childComponent[0].handleStartStop();
          },
        },
    };
</script>
