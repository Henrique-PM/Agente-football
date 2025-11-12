from agenteSystem.agente_system_plan import SystemAgent
import json

def print_resultado(resultado):
    """Imprime o resultado de forma bonita e legível."""
    print("\n" + "="*70)
    print("📊 RESPOSTA DO SISTEMA")
    print("="*70 + "\n")
    
    if isinstance(resultado, dict):
        # Resposta direta
        if "resposta_direta" in resultado:
            print("💬 RESPOSTA:")
            print(f"   {resultado['resposta_direta']}\n")
        
        # Estatísticas
        if "estatisticas" in resultado:
            print("📈 ESTATÍSTICAS:")
            for key, value in resultado["estatisticas"].items():
                print(f"   • {key}: {value}")
            print()
        
        # Sugestões de apostas
        if "sugestoes_apostas" in resultado:
            print("🎲 SUGESTÕES DE APOSTAS:")
            for i, aposta in enumerate(resultado["sugestoes_apostas"], 1):
                print(f"\n   {i}. {aposta.get('mercado', 'N/A')}")
                print(f"      Sugestão: {aposta.get('sugestao', 'N/A')}")
                print(f"      Confiança: {aposta.get('confianca', 'N/A')}")
                print(f"      Justificativa: {aposta.get('justificativa', 'N/A')}")
            print()
        
        # Observações
        if "observacoes" in resultado:
            print("📝 OBSERVAÇÕES:")
            print(f"   {resultado['observacoes']}\n")
        
        # Confiança
        if "confianca_analise" in resultado:
            print(f"🎯 CONFIANÇA DA ANÁLISE: {resultado['confianca_analise'].upper()}\n")
        
        # Se houver erro
        if "error" in resultado:
            print(f"❌ ERRO: {resultado['error']}\n")
        
        # Mostrar JSON completo se necessário
        if "resposta" in resultado:
            print("📄 RESPOSTA COMPLETA:")
            print(resultado['resposta'])
            print()
    else:
        print(json.dumps(resultado, indent=2, ensure_ascii=False))
    
    print("="*70 + "\n")

def main():
    system_agent = SystemAgent()
    
    print("\n" + "⚽"*35)
    print("⚽  SISTEMA DE ANÁLISE DE FUTEBOL & APOSTAS  ⚽")
    print("⚽"*35)
    print("\n📌 EXEMPLOS DE PERGUNTAS:")
    print("   • Quantos gols o Flamengo fez nos últimos 10 jogos?")
    print("   • O Flamengo ganha hoje contra o River Plate?")
    print("   • Quais apostas posso fazer no jogo Palmeiras x São Paulo?")
    print("   • Mostre o histórico de confrontos entre Corinthians e Santos")
    print("   • Como está a forma recente do Real Madrid?")
    print("   • Quais os próximos jogos do Barcelona?")
    print("\n" + "-"*70)
    
    while True:
        user_input = input("\n💭 Digite sua pergunta (ou 'sair' para encerrar): ")
        
        if user_input.lower() in ["sair", "exit", "quit"]:
            print("\n👋 Encerrando o sistema... Boas apostas! 🎲\n")
            break

        print("\n⏳ Processando sua pergunta...")
        
        try:
            resultado = system_agent.run(user_input)
            print_resultado(resultado)
        except Exception as e:
            print(f"\n❌ Erro ao processar: {str(e)}\n")

if __name__ == "__main__":
    main()