import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from agents.analyser.analyser_plan import AnalyserPlanAgent
from agents.football.football_plan import FootballPlanAgent

load_dotenv()

class SystemAgent:
    def __init__(self):
        self.football_agent = FootballPlanAgent()
        self.analyser_agent = AnalyserPlanAgent()
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)

    def run(self, user_query: str):
        """
        Recebe a pergunta do usuário, coleta dados, analisa e retorna relatório JSON.
        """
        try:
            hoje = "2022-07-11"
            trinta_dias_atras = "2022-05-23"
            
            extraction_prompt = f"""Você é um extrator de informações sobre futebol. Analise a pergunta e retorne APENAS um JSON válido, sem explicações.

            Pergunta: "{user_query}"

            Retorne exatamente neste formato:
            {{
                "teams": [],
                "league_id": null,
                "season": 2024,
                "date_from": null,
                "date_to": null,
                "analysis_type": "recent_performance",
                "question_type": "general"
            }}

            REGRAS DE EXTRAÇÃO:
            - teams: Liste TODOS os times mencionados (ex: ["Flamengo", "River Plate"])
            - league_id: 71 para Brasileirão, 13 para Libertadores, null se não mencionado
            - season: 2022
            - date_from: Se mencionar "últimos X jogos" ou "última rodada", use "{trinta_dias_atras}"
            - date_to: Data final, use "{hoje}" se mencionado "hoje" ou "atual"
            - analysis_type: "recent_performance", "prediction", "head_to_head" ou "betting"
            - question_type: "goals_scored", "match_prediction", "betting_tips", "team_form"

            EXEMPLOS:
            P: "Quantos gols o Flamengo fez nos últimos jogos?"
            R: {{"teams": ["Flamengo"], "league_id": 71, "season": 2022, "date_from": "{trinta_dias_atras}", "date_to": "{hoje}", "analysis_type": "recent_performance", "question_type": "goals_scored"}}

            P: "Flamengo ganha do River Plate?"
            R: {{"teams": ["Flamengo", "River Plate"], "league_id": null, "season": 2022, "date_from": null, "date_to": null, "analysis_type": "prediction", "question_type": "match_prediction"}}

            Retorne APENAS o JSON, sem texto adicional:"""
            
            response = self.llm.invoke(extraction_prompt)
            parsed_input_str = response.content if hasattr(response, 'content') else str(response)
            
            try:
                if "```json" in parsed_input_str:
                    parsed_input_str = parsed_input_str.split("```json")[1].split("```")[0].strip()
                elif "```" in parsed_input_str:
                    parsed_input_str = parsed_input_str.split("```")[1].split("```")[0].strip()
                
                params = json.loads(parsed_input_str)
            except Exception as e:
                return {
                    "error": "Não foi possível interpretar a entrada do usuário.",
                    "raw": parsed_input_str,
                    "exception": str(e)
                }

            print(f"\n🔍 Parâmetros extraídos: {json.dumps(params, indent=2, ensure_ascii=False)}")
            
            if not params.get("teams") or len(params.get("teams", [])) == 0:
                return {
                    "error": "Não consegui identificar nenhum time na sua pergunta. Por favor, mencione pelo menos um time.",
                    "exemplo": "Tente perguntas como: 'Como está o Flamengo?' ou 'Flamengo vs Palmeiras'"
                }
            
            data_collection = []
            
            for team in params.get("teams", []):
                print(f"📊 Buscando dados de: {team}")
                team_query = {
                    "action": "get_team_recent_matches",
                    "team_name": team,
                    "league_id": params.get("league_id"),
                    "season": params.get("season", 2022),
                    "last_n_games": 10
                }
                
                try:
                    team_data = self.football_agent.run(json.dumps(team_query))
                    data_collection.append({
                        "team": team,
                        "data": team_data
                    })
                except Exception as e:
                    print(f"⚠️ Erro ao buscar dados de {team}: {str(e)}")
                    data_collection.append({
                        "team": team,
                        "data": {"error": str(e)}
                    })
            
            # Se há 2 times, buscar confronto direto
            if len(params.get("teams", [])) == 2:
                print(f"⚔️ Buscando confronto direto: {params['teams'][0]} vs {params['teams'][1]}")
                try:
                    h2h_query = {
                        "action": "head_to_head",
                        "team1": params["teams"][0],
                        "team2": params["teams"][1]
                    }
                    h2h_data = self.football_agent.run(json.dumps(h2h_query))
                    data_collection.append({
                        "type": "head_to_head",
                        "data": h2h_data
                    })
                except Exception as e:
                    print(f"⚠️ Erro ao buscar confronto direto: {str(e)}")

            # Verificar se conseguimos coletar algum dado
            if not data_collection or all(d.get("data", {}).get("error") for d in data_collection):
                return {
                    "error": "Não foi possível coletar dados da API de futebol.",
                    "possivel_causa": "API key inválida ou limite de requisições atingido",
                    "dados_tentados": params
                }

            print("✅ Dados coletados com sucesso!")
            
            # Passo 3: Análise inteligente
            analysis_prompt = f"""
            Pergunta original: {user_query}
            
            Dados coletados: {json.dumps(data_collection, indent=2)}
            
            Contexto da pergunta: {json.dumps(params, indent=2)}
            """
            
            analysis = self.analyser_agent.run(analysis_prompt)

            # Passo 4: Gerar resposta final em linguagem natural
            final_response_prompt = f"""
            Com base na análise abaixo, responda a pergunta do usuário de forma clara e direta:
            
            Pergunta: "{user_query}"
            
            Análise: {json.dumps(analysis, indent=2)}
            
            Forneça:
            1. Resposta direta à pergunta
            2. Estatísticas relevantes
            3. Se for sobre apostas, sugira mercados interessantes com base nos dados
            4. Se for sobre previsão, dê sua análise fundamentada
            
            Retorne JSON no formato:
            {{
                "resposta_direta": "...",
                "estatisticas": {{}},
                "sugestoes_apostas": [],
                "confianca_analise": "alta/média/baixa",
                "observacoes": "..."
            }}
            """
            
            print("🧠 Gerando análise final...")
            final_answer_response = self.llm.invoke(final_response_prompt)
            final_answer = final_answer_response.content if hasattr(final_answer_response, 'content') else str(final_answer_response)
            
            # Limpar markdown se existir
            if "```json" in final_answer:
                final_answer = final_answer.split("```json")[1].split("```")[0].strip()
            elif "```" in final_answer:
                final_answer = final_answer.split("```")[1].split("```")[0].strip()
            
            try:
                result = json.loads(final_answer)
                print("✅ Análise concluída!")
                return result
            except json.JSONDecodeError as e:
                print(f"⚠️ Erro ao parsear JSON final: {str(e)}")
                return {
                    "resposta": final_answer,
                    "analise_completa": analysis,
                    "dados_brutos": data_collection,
                    "nota": "A resposta não pôde ser formatada como JSON, mas está disponível em texto"
                }

        except Exception as e:
            return {"error": str(e), "traceback": str(e.__traceback__)}