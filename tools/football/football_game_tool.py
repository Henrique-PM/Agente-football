import os
import json
import requests
from typing import Type
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from langchain.tools import BaseTool
from dotenv import load_dotenv

load_dotenv()

class FootballAPIInput(BaseModel):
    """Entrada para buscar dados de futebol."""
    query: str = Field(..., description="JSON com parâmetros de busca")

class FootballAPI(BaseTool):
    name: str = "football_api"
    description: str = (
        "Busca partidas e estatísticas de futebol usando API-Football. "
        "Suporta múltiplas ações: "
        "1. Buscar fixtures por liga/temporada "
        "2. Buscar jogos recentes de um time específico "
        "3. Buscar confronto direto entre dois times "
        "4. Buscar próximos jogos "
        "5. Buscar estatísticas detalhadas de partidas"
    )
    args_schema: Type[BaseModel] = FootballAPIInput

    def _get_team_id(self, team_name: str, headers: dict) -> int:
        """Busca o ID de um time pelo nome."""
        url = "https://v3.football.api-sports.io/teams"
        response = requests.get(url, headers=headers, params={"search": team_name})
        data = response.json()
        
        if data.get("response"):
            return data["response"][0]["team"]["id"]
        return None

    def _run(self, query: str) -> dict:
        try:
            params = json.loads(query)
            api_key = os.getenv("FOOTBALL_API_KEY")
            
            if not api_key:
                return {"error": "API key não configurada em FOOTBALL_API_KEY"}

            headers = {"x-apisports-key": api_key}
            action = params.get("action", "get_fixtures")

            # Ação 1: Buscar fixtures por liga/temporada
            if action == "get_fixtures":
                return self._get_fixtures(params, headers)
            
            # Ação 2: Buscar jogos recentes de um time
            elif action == "get_team_recent_matches":
                return self._get_team_recent_matches(params, headers)
            
            # Ação 3: Confronto direto
            elif action == "head_to_head":
                return self._get_head_to_head(params, headers)
            
            # Ação 4: Próximos jogos
            elif action == "get_upcoming_matches":
                return self._get_upcoming_matches(params, headers)
            
            # Ação 5: Estatísticas de uma partida
            elif action == "get_match_statistics":
                return self._get_match_statistics(params, headers)
            
            else:
                return {"error": f"Ação '{action}' não suportada"}

        except Exception as e:
            return {"error": str(e)}

    def _get_fixtures(self, params: dict, headers: dict) -> dict:
        """Busca fixtures básicas por liga/temporada."""
        league_id = params.get("league_id")
        season = params.get("season", 2024)
        date_from = params.get("date_from")
        date_to = params.get("date_to")

        url = "https://v3.football.api-sports.io/fixtures"
        req_params = {
            "league": league_id,
            "season": season,
            "status": "FT"
        }
        
        if date_from:
            req_params["from"] = date_from
        if date_to:
            req_params["to"] = date_to

        response = requests.get(url, headers=headers, params=req_params)
        data = response.json()

        if response.status_code != 200 or not data.get("response"):
            return {"error": data.get("errors", "Erro desconhecido")}

        fixtures = []
        for fixture in data["response"]:
            fixtures.append({
                "fixture_id": fixture["fixture"]["id"],
                "date": fixture["fixture"]["date"],
                "home_team": fixture["teams"]["home"]["name"],
                "away_team": fixture["teams"]["away"]["name"],
                "score": fixture["score"]["fulltime"],
                "status": fixture["fixture"]["status"]["short"]
            })

        return {"fixtures": fixtures, "total": len(fixtures)}

    def _get_team_recent_matches(self, params: dict, headers: dict) -> dict:
        """Busca últimos N jogos de um time."""
        team_name = params.get("team_name")
        last_n = params.get("last_n_games", 10)
        season = params.get("season", 2024)
        
        # Buscar ID do time
        team_id = self._get_team_id(team_name, headers)
        if not team_id:
            return {"error": f"Time '{team_name}' não encontrado"}

        # Buscar jogos do time
        url = "https://v3.football.api-sports.io/fixtures"
        req_params = {
            "team": team_id,
            "season": season,
            "last": last_n,
            "status": "FT"
        }

        response = requests.get(url, headers=headers, params=req_params)
        data = response.json()

        if response.status_code != 200:
            return {"error": "Erro ao buscar jogos do time"}

        matches = []
        stats = {
            "gols_marcados": 0,
            "gols_sofridos": 0,
            "vitorias": 0,
            "empates": 0,
            "derrotas": 0
        }

        for fixture in data.get("response", []):
            home = fixture["teams"]["home"]
            away = fixture["teams"]["away"]
            score = fixture["score"]["fulltime"]
            
            is_home = home["name"] == team_name
            team_goals = score["home"] if is_home else score["away"]
            opponent_goals = score["away"] if is_home else score["home"]
            opponent = away["name"] if is_home else home["name"]
            
            stats["gols_marcados"] += team_goals or 0
            stats["gols_sofridos"] += opponent_goals or 0
            
            if team_goals > opponent_goals:
                stats["vitorias"] += 1
                result = "V"
            elif team_goals < opponent_goals:
                stats["derrotas"] += 1
                result = "D"
            else:
                stats["empates"] += 1
                result = "E"

            matches.append({
                "date": fixture["fixture"]["date"],
                "opponent": opponent,
                "home_away": "Casa" if is_home else "Fora",
                "result": result,
                "score": f"{team_goals}-{opponent_goals}",
                "team_goals": team_goals,
                "opponent_goals": opponent_goals
            })

        stats["total_jogos"] = len(matches)
        stats["media_gols_marcados"] = round(stats["gols_marcados"] / max(len(matches), 1), 2)
        stats["media_gols_sofridos"] = round(stats["gols_sofridos"] / max(len(matches), 1), 2)
        stats["aproveitamento"] = round((stats["vitorias"] * 3 + stats["empates"]) / (len(matches) * 3) * 100, 1)

        return {
            "team": team_name,
            "matches": matches,
            "statistics": stats
        }

    def _get_head_to_head(self, params: dict, headers: dict) -> dict:
        """Busca histórico de confrontos entre dois times."""
        team1_name = params.get("team1")
        team2_name = params.get("team2")
        
        team1_id = self._get_team_id(team1_name, headers)
        team2_id = self._get_team_id(team2_name, headers)
        
        if not team1_id or not team2_id:
            return {"error": "Um dos times não foi encontrado"}

        url = "https://v3.football.api-sports.io/fixtures/headtohead"
        req_params = {
            "h2h": f"{team1_id}-{team2_id}",
            "last": 10
        }

        response = requests.get(url, headers=headers, params=req_params)
        data = response.json()

        if response.status_code != 200:
            return {"error": "Erro ao buscar confrontos diretos"}

        matches = []
        stats = {
            "vitorias_team1": 0,
            "vitorias_team2": 0,
            "empates": 0,
            "gols_team1": 0,
            "gols_team2": 0
        }

        for fixture in data.get("response", []):
            home = fixture["teams"]["home"]["name"]
            away = fixture["teams"]["away"]["name"]
            score = fixture["score"]["fulltime"]
            
            if home == team1_name:
                t1_goals, t2_goals = score["home"], score["away"]
            else:
                t1_goals, t2_goals = score["away"], score["home"]
            
            stats["gols_team1"] += t1_goals or 0
            stats["gols_team2"] += t2_goals or 0
            
            if t1_goals > t2_goals:
                stats["vitorias_team1"] += 1
            elif t1_goals < t2_goals:
                stats["vitorias_team2"] += 1
            else:
                stats["empates"] += 1

            matches.append({
                "date": fixture["fixture"]["date"],
                "home": home,
                "away": away,
                "score": f"{score['home']}-{score['away']}"
            })

        return {
            "team1": team1_name,
            "team2": team2_name,
            "matches": matches,
            "statistics": stats
        }

    def _get_upcoming_matches(self, params: dict, headers: dict) -> dict:
        """Busca próximos jogos de um time."""
        team_name = params.get("team_name")
        next_n = params.get("next_n_games", 5)
        
        team_id = self._get_team_id(team_name, headers)
        if not team_id:
            return {"error": f"Time '{team_name}' não encontrado"}

        url = "https://v3.football.api-sports.io/fixtures"
        req_params = {
            "team": team_id,
            "next": next_n
        }

        response = requests.get(url, headers=headers, params=req_params)
        data = response.json()

        upcoming = []
        for fixture in data.get("response", []):
            upcoming.append({
                "date": fixture["fixture"]["date"],
                "home_team": fixture["teams"]["home"]["name"],
                "away_team": fixture["teams"]["away"]["name"],
                "league": fixture["league"]["name"]
            })

        return {"team": team_name, "upcoming_matches": upcoming}

    def _get_match_statistics(self, params: dict, headers: dict) -> dict:
        """Busca estatísticas detalhadas de uma partida."""
        fixture_id = params.get("fixture_id")
        
        url = "https://v3.football.api-sports.io/fixtures/statistics"
        response = requests.get(url, headers=headers, params={"fixture": fixture_id})
        data = response.json()

        return data.get("response", {})

    async def _arun(self, query: str):
        raise NotImplementedError("Execução assíncrona não suportada.")