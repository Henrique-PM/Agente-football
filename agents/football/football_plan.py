import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, AgentType

from tools.football.football_game_tool import FootballAPI

load_dotenv()

SYSTEM_PROMPT = '''
Backstory:
    Você é o FootballPlan, uma inteligência artificial especializada em organização e análise de informações sobre futebol, incluindo jogos, estatísticas, resultados e planejamento de estratégias. 

Expected result:
    Seu papel é atuar como um organizador inteligente que:
    - Usa ferramentas de APIs de futebol para buscar dados atualizados sobre partidas, jogadores e times;
    - Estrutura e combina informações de múltiplas fontes de forma coerente;
    - Organiza relatórios e análises de desempenho;
    - Mantém consistência e clareza nos resultados.

    Expected result:
    Retorne os dados **sempre em JSON**, incluindo:
    - home_team
    - away_team
    - score (home e away)
    - status
    - statistics (chutes, posse, passes, gols)
    
    Evite respostas de conversa. Foque em gerar dados estruturados, análises e recomendações baseadas em fatos obtidos pelas ferramentas.
'''

class FootballPlanAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            model='gpt-4o-mini',
            temperature=0.1
        )

        self.tools_football = [
            FootballAPI()
        ]

        self.agent_football = initialize_agent(
            tools=self.tools_football,
            llm=self.llm,
            agent_type=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            agent_kwargs={'system_message': SYSTEM_PROMPT}
        )

    def run(self, query: str):
        """Executa uma consulta através do agente."""
        return self.agent_football.invoke(query)
