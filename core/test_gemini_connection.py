# test_gemini_connection.py
import os
import google.generativeai as genai
import sys

# --- Configuração ---
# É CRÍTICO que sua chave de API Gemini esteja definida
# como uma variável de ambiente antes de executar este script.
# Ex: export GEMINI_API_KEY='SUA_CHAVE_AQUI' (Linux/macOS)
# Ex: $env:GEMINI_API_KEY='SUA_CHAVE_AQUI' (PowerShell no Windows)
# Ex: set GEMINI_API_KEY=SUA_CHAVE_AQUI (CMD no Windows)
# OU descomente e defina diretamente AQUI SOMENTE PARA TESTE:
# os.environ['GEMINI_API_KEY'] = 'SUA_CHAVE_API_GEMINI_REAL'

api_key = os.environ.get('GEMINI_API_KEY')
if not api_key:
    print("ERRO: GEMINI_API_KEY não encontrada nas variáveis de ambiente.")
    print("Por favor, defina a variável de ambiente antes de executar o script.")
    sys.exit(1) # Sai com código de erro

try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('models/gemini-1.5-flash') # Use o mesmo modelo do seu views.py

    print("--- Teste de API Gemini ---")
    print(f"Chave API carregada (parcial): {api_key[:5]}...{api_key[-5:]}")

    # Prompt de teste simples
    test_prompt_system = "You are a helpful AI."
    test_prompt_user = "Generate a very short, simple greeting."

    print(f"Enviando prompt: '{test_prompt_user}' para o Gemini...")

    # Tenta gerar conteúdo com um timeout para não travar
    response = model.generate_content(
        [test_prompt_system, test_prompt_user],
        generation_config=genai.GenerationConfig(
            temperature=0.7, # Um pouco de criatividade
            max_output_tokens=50 # Queremos uma resposta curta
        ),
        request_options={'timeout': 60} # Timeout de 60 segundos
    )
    print("Resposta recebida do Gemini:")
    print("---------------------------")
    print(response.text)
    print("---------------------------")
    print("Teste de conexão com Gemini BEM-SUCEDIDO!")

except google.api_core.exceptions.GoogleAPIError as e:
    print(f"\nERRO DA API GEMINI: {e}")
    print("CAUSAS COMUNS:")
    if "403" in str(e) or "authentication" in str(e).lower() or "unauthenticated" in str(e).lower():
        print("  - Chave API incorreta, expirada, ou sem permissões.")
        print("  - Verifique sua chave no Google AI Studio/Console e as permissões.")
    elif "429" in str(e) or "rate limit" in str(e).lower():
        print("  - Limite de taxa excedido. Tente novamente em alguns segundos/minutos.")
    elif "500" in str(e) or "internal" in str(e).lower():
        print("  - Erro interno do servidor Gemini. Tente novamente mais tarde.")
    elif "timeout" in str(e).lower():
        print("  - A chamada excedeu o tempo limite. Problema de rede ou latência da API do Gemini.")
    elif "safety" in str(e).lower() or "blocked" in str(e).lower():
        print("  - Conteúdo bloqueado pelas configurações de segurança. Tente um prompt diferente e menos sensível.")
    else:
        print(f"  - Erro desconhecido da API. Mensagem completa: {e}")
except Exception as e:
    print(f"\nERRO INESPERADO DURANTE O TESTE DE CONEXÃO: {e}")
    print("  - Pode ser um problema de rede geral, firewall ou ambiente.")

print("\nFim do teste.")