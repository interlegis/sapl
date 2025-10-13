import './scss/votacao.scss'
import Vue from 'vue'
import { FormSelectPlugin } from 'bootstrap-vue'
import axios from 'axios'

axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = 'X-CSRFToken'

Vue.use(FormSelectPlugin)

console.log('votacao main.js carregado')

const v = new Vue({ // eslint-disable-line
  delimiters: ['[[', ']]'],
  el: '#votacao',
  data () {
    return {
        votacao_aberta: true,
        edit_votes: true,
        disable_resultado: false,
        resultado_selected: "",
        observacoes: "",
        error_message: "",
        tipo_votacao: 2,
        tipo_votacao_descricao: "Votação Nominal",
        materia: "Projeto de Lei Ordinária nº 3 de 2025",
        ementa: "Institui no Município de Pato Branco o Projeto Chá de Fralda Social. ",
        parlamentares: [
                {
                    "parlamentar_id": 197,
                    "nome_parlamentar": "Alexandre Zoche",
                    "filiacao": "PRD"
                },
                {
                    "parlamentar_id": 196,
                    "nome_parlamentar": "Anne Cristine Gomes da Silva Cavali",
                    "filiacao": "PSD"
                },
                {
                    "parlamentar_id": 194,
                    "nome_parlamentar": "Diogo Domingos Grando",
                    "filiacao": "PRD"
                },
                {
                    "parlamentar_id": 186,
                    "nome_parlamentar": "Eduardo Albani Dala Costa",
                    "filiacao": "Republicanos"
                },
                {
                    "parlamentar_id": 3,
                    "nome_parlamentar": "Fabricio Preis de Mello",
                    "filiacao": "PL"
                },
                {
                    "parlamentar_id": 6,
                    "nome_parlamentar": "Joecir Bernardi",
                    "filiacao": "PSD"
                },
                {
                    "parlamentar_id": 187,
                    "nome_parlamentar": "Lindomar Rodrigo Brandão",
                    "filiacao": "PP"
                },
                {
                    "parlamentar_id": 195,
                    "nome_parlamentar": "Rafael Foss",
                    "filiacao": "União"
                },
                {
                    "parlamentar_id": 11,
                    "nome_parlamentar": "Rodrigo José Correia",
                    "filiacao": "União"
                },
                {
                    "parlamentar_id": 192,
                    "nome_parlamentar": "Thania Maria Caminski Gehlen",
                    "filiacao": "PP"
                }
        ],
        //TODO: check if votos_parlamentares is null
        votos_parlamentares: {
              186: {
                "voto": "Não",
                "materia_id": 31919,
                "parlamentar_id": 186,
                "parlamentar_nome": "Eduardo Albani Dala Costa"
              },
              195: {
                "voto": "Não",
                "materia_id": 31919,
                "parlamentar_id": 195,
                "parlamentar_nome": "Rafael Foss"
              },
              196: {
                "voto": "Não",
                "materia_id": 31919,
                "parlamentar_id": 196,
                "parlamentar_nome": "Anne Cristine Gomes da Silva Cavali"
              },
              3: {
                "voto": "Sim",
                "materia_id": 31919,
                "parlamentar_id": 3,
                "parlamentar_nome": "Fabricio Preis de Mello"
              },
              11: {
                "voto": "Não",
                "materia_id": 31919,
                "parlamentar_id": 11,
                "parlamentar_nome": "Rodrigo José Correia"
              },
              194: {
                "voto": "Não",
                "materia_id": 31919,
                "parlamentar_id": 194,
                "parlamentar_nome": "Diogo Domingos Grando"
              },
              197: {
                "voto": "Não",
                "materia_id": 31919,
                "parlamentar_id": 197,
                "parlamentar_nome": "Alexandre Zoche"
              },
              6: {
                "voto": "Não",
                "materia_id": 31919,
                "parlamentar_id": 6,
                "parlamentar_nome": "Joecir Bernardi"
              },
              187: {
                "voto": "Abstenção",
                "materia_id": 31919,
                "parlamentar_id": 187,
                "parlamentar_nome": "Lindomar Rodrigo Brandão"
              },
              192: {
                "voto": "Sim",
                "materia_id": 31919,
                "parlamentar_id": 192,
                "parlamentar_nome": "Thania Maria Caminski Gehlen"
              }
        },
        options: [
            { text: 'Sim', value: 'voto_sim' },
            { text: 'Não', value: 'voto_nao' },
            { text: 'Abstenção', value: 'abstencao' },
            { text: 'Não Votou', value: 'nao_votou' },
        ],
        tipos_resultados: [
              {
                "id": 13,
                "nome": "Aprovada a retirada de pauta"
              },
              {
                "id": 10,
                "nome": "Aprovada por dois terços"
              },
              {
                "id": 2,
                "nome": "Aprovada por maioria absoluta"
              },
              {
                "id": 1,
                "nome": "Aprovada por maioria simples - conforme o art. 37 do RI o presidente não vota"
              },
              {
                "id": 8,
                "nome": "Aprovada por maioria simples - conforme o art. 37 do RI o presidente votou pelo desempate"
              },
              {
                "id": 15,
                "nome": "Aprovada."
              },
              {
                "id": 7,
                "nome": "Empate - conforme o art. 37 do RI o presidente vota para desempate"
              },
              {
                "id": 16,
                "nome": "IMPROCEDENTE"
              },
              {
                "id": 12,
                "nome": "Leitura em Plenário"
              },
              {
                "id": 17,
                "nome": "PROCEDENTE"
              },
              {
                "id": 11,
                "nome": "Prejudicada"
              },
              {
                "id": 5,
                "nome": "Rejeitada"
              },
              {
                "id": 14,
                "nome": "Rejeitada a retirada de pauta"
              },
              {
                "id": 9,
                "nome": "Rejeitada por maioria simples - conforme o art. 37 do RI o presidente votou pelo desempate"
              }
        ],
    }
  },

  watch: {},

  computed: {
    total_votos() {
        // TODO: use number index instead of string ("sim", "não") as keys.
        var groupedVotes = Map.groupBy(Object.values(this.votos_parlamentares), ({ voto }) => voto )
        // initialize total_votos
        total_votos = [
            {"tipo": "Sim", "total": 0},
            {"tipo": "Não", "total": 0},
            {"tipo": "Abstenção", "total": 0},
            {"tipo": "Não Votou", total: 0}
        ]
        for (const [key, value] of groupedVotes.entries()) {
             const index = total_votos.findIndex(item => item.tipo === key);
             total_votos[index].total = value.length
        }
        return total_votos
    }
  },

  created () {},

  methods: {},

  mounted () {
    console.log("Votacao app mounted!")
  }
})
