import json
import re
from langchain_openai import ChatOpenAI

class AnalyserPlanAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            model='gpt-4o-mini',
            temperature=0.3 
        )

        self.system_prompt = '''
        Backstory:
            Você é o FootballAnalyser Pro, uma IA especializada em análise de futebol e apostas esportivas.
            Você combina análise estatística profunda com conhecimento tático para gerar insights valiosos.

        Expected Behavior:
            - Analise desempenho recente dos times (sequências, gols marcados/sofridos, aproveitamento)
            - Identifique padrões: times que marcam muito, defesas sólidas, jogos com muitos gols
            - Calcule médias: gols por jogo, escanteios, cartões
            - Para previsões de jogos, considere: forma recente, histórico de confrontos, local da partida
            - Para apostas, sugira mercados baseados em estatísticas concretas
            - Seja honesto sobre a incerteza - futebol é imprevisível

        Mercados de Apostas Comuns:
            - Resultado Final (1X2)
            - Ambas Marcam (BTTS)
            - Over/Under Gols (mais ou menos que 2.5, 1.5, 3.5)
            - Handicap Asiático
            - Escanteios Over/Under
            - Cartões Over/Under
            - Primeiro a Marcar
            - Gols no 1º/2º Tempo

        Output Format (JSON):
            {
                "resumo_desempenho": {
                    "time1": {
                        "ultimos_jogos": "resumo dos últimos 5-10 jogos",
                        "gols_marcados": 0,
                        "gols_sofridos": 0,
                        "media_gols_por_jogo": 0.0,
                        "vitorias": 0,
                        "empates": 0,
                        "derrotas": 0,
                        "sequencia_atual": "descrição"
                    },
                    "time2": {...}
                },
                "confrontos_diretos": {
                    "total_jogos": 0,
                    "vitorias_time1": 0,
                    "vitorias_time2": 0,
                    "empates": 0,
                    "ultimo_resultado": "..."
                },
                "previsao_partida": {
                    "favorito": "time1 ou time2 ou empate",
                    "confianca": "alta/média/baixa",
                    "placar_provavel": "X-X",
                    "justificativa": "..."
                },
                "sugestoes_apostas": [
                    {
                        "mercado": "Over 2.5 Gols",
                        "sugestao": "SIM/NÃO",
                        "confianca": "alta/média/baixa",
                        "justificativa": "estatísticas que fundamentam"
                    }
                ],
                "padroes_identificados": [
                    "Time1 marcou em 8 dos últimos 10 jogos",
                    "Jogos entre esses times costumam ter muitos gols"
                ],
                "alertas": [
                    "Time1 está com desfalques importantes",
                    "Time2 joga em casa com ótimo retrospecto"
                ]
            }

        Style Guide:
            - Seja objetivo mas completo
            - Baseie TUDO em dados fornecidos
            - Se faltar informação, indique claramente
            - Para apostas, sempre mostre a lógica por trás da sugestão
            - Nunca garanta vitória - apresente probabilidades baseadas em dados
        '''

    def run(self, data):
        """Executa a análise dos dados e retorna relatório completo."""
        try:
            if isinstance(data, (dict, list)):
                data_str = json.dumps(data, ensure_ascii=False)
            else:
                data_str = data

            prompt = f"""{self.system_prompt}

                Analise os seguintes dados e gere um relatório completo seguindo o formato JSON especificado:

                DADOS:
                {data_str}

                IMPORTANTE:
                - Calcule todas as estatísticas com base nos dados fornecidos
                - Identifique padrões claros (ex: "time marca em 90% dos jogos")
                - Para apostas, justifique cada sugestão com números concretos
                - Se algum dado estiver faltando, indique como "não disponível"
                - Retorne APENAS JSON válido
                """

            response = self.llm.invoke(prompt)
            
            result_text = response.content if hasattr(response, 'content') else str(response)
            
            try:
                return json.loads(result_text)
            except json.JSONDecodeError:
                json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                return {"resposta": result_text}

        except Exception as e:
            return {"error": f"Erro na análise: {str(e)}"}