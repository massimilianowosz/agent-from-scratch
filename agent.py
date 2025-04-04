import re
import ollama
from typing import Dict, Callable, Tuple, Optional

# 🧠 Memoria conversazionale globale
agent_memory = []

# 🔧 TOOL MOCK CON CASE HANDLING MIGLIORATO
def meteo_tool(città):
    # Normalizziamo i nomi delle città per gestire case insensitive
    città = città.strip()
    meteo = {
        "roma": "A Roma ci sono 18°C e cielo sereno.",
        "milano": "A Milano ci sono 15°C con pioggia leggera.",
        "napoli": "A Napoli ci sono 20°C e sole pieno."
    }
    return meteo.get(città.lower(), f"Nessuna informazione disponibile per {città}.")

# 🔧 TOOL MOCK: suggerisce attività in base al meteo
def activity_tool(condition):
    if "sereno" in condition.lower() or "sole" in condition.lower():
        return "Ti consiglio di fare una passeggiata al parco o visitare un museo all'aperto."
    elif "pioggia" in condition.lower():
        return "Potresti visitare un museo o andare al cinema."
    elif "coperto" in condition.lower():
        return "Una giornata perfetta per una libreria o un caffè accogliente."
    else:
        return "Non ho un suggerimento preciso per queste condizioni."

tools = {
    "meteo_tool": meteo_tool,
    "activity_tool": activity_tool
}

# 🧠 PROMPT CON FORMATO LANGCHAIN-STYLE MIGLIORATO
system_prompt = """Sei un agente AI che ragiona passo dopo passo e può usare strumenti esterni.

Hai accesso a questi strumenti:

meteo_tool(città): restituisce il meteo attuale per la città specificata.
activity_tool(condizione_meteo): suggerisce un'attività adatta in base alle condizioni meteorologiche.

Per rispondere alle domande dell'utente segui questo formato:

Thought: Ragiona attentamente su cosa devi fare e quale strumento utilizzare
Action: nome_strumento
Action Input: parametri per lo strumento

Quando ricevi un'osservazione, continua così:

Observation: [qui vedrai il risultato dello strumento]
Thought: Analizza il risultato e decidi se hai bisogno di altre informazioni
Action: nome_strumento
Action Input: parametri per lo strumento

Oppure, se hai tutte le informazioni necessarie per rispondere:

Thought: Ora ho tutte le informazioni per rispondere
Final Answer: La tua risposta finale all'utente

REGOLE IMPORTANTI:
1. Non inventare MAI dati o risultati. Usa ESATTAMENTE le informazioni ricevute nelle osservazioni.
2. Non modificare o alterare i valori delle osservazioni (come temperature, condizioni meteo, ecc.).
3. Usa solo gli strumenti disponibili: meteo_tool e activity_tool.
4. Rispondi con Final Answer solo quando hai tutte le informazioni necessarie.
5. Nella risposta finale, cita ESATTAMENTE i dati ricevuti dalle osservazioni.

Esempio corretto:

Utente: "Che tempo fa a Roma?"
Thought: L'utente vuole sapere il meteo attuale a Roma. Devo usare il tool meteo_tool.
Action: meteo_tool
Action Input: Roma

Observation: A Roma ci sono 18°C e cielo sereno.
Thought: Ho ricevuto l'informazione sul meteo di Roma, ora posso fornire la risposta finale. Non devo modificare il dato ricevuto.
Final Answer: A Roma ci sono 18°C e cielo sereno.

Esempio di risposta ERRATA (da non seguire):
Final Answer: A Roma ci sono 22°C e nuvole sparse. [ERRORE: questo è inventato, non è ciò che è stato restituito dallo strumento]
"""

# 🔍 EXTRACTORS
def extract_tool_call(content: str) -> Tuple[Optional[str], Optional[str]]:
    action_match = re.search(r"Action:\s*(.*?)(?:\n|$)", content, re.DOTALL)
    action_input_match = re.search(r"Action Input:\s*(.*?)(?:\n|$)", content, re.DOTALL)
    
    if not action_match or not action_input_match:
        return None, None
    
    return action_match.group(1).strip(), action_input_match.group(1).strip()

def extract_answer(content: str) -> Optional[str]:
    answer_match = re.search(r"Final Answer:\s*(.*?)(?:\n|$)", content, re.DOTALL | re.MULTILINE)
    if answer_match:
        # Cattura tutto il testo fino alla fine del messaggio o fino alla prossima riga vuota
        answer_text = answer_match.group(1).strip()
        
        # Se c'è del testo dopo "Final Answer:" su righe successive, lo includiamo
        rest_of_content = content[answer_match.end():]
        additional_lines = []
        
        for line in rest_of_content.split('\n'):
            if line.strip() and not line.startswith("Thought:") and not line.startswith("Action:"):
                additional_lines.append(line.strip())
            else:
                break
                
        if additional_lines:
            answer_text += "\n" + "\n".join(additional_lines)
            
        return answer_text
    return None

# 🚀 AGENTE MIGLIORATO CON DEBUGGING
def run_agent(user_input: str):
    global agent_memory

    if not agent_memory:
        agent_memory = [{"role": "system", "content": system_prompt}]
    
    agent_memory.append({"role": "user", "content": user_input})

    max_iterations = 5  # Limite di sicurezza per evitare loop infiniti
    iterations = 0
    
    while iterations < max_iterations:
        iterations += 1
        print(f"\n🧠 Iterazione {iterations}: Generazione risposta...\n")
        
        # Chiamata al modello usando ollama.chat con qwen2.5
        response = ollama.chat(model="qwen2.5", messages=agent_memory)
        content = response["message"]["content"]
        print(f"📤 Output del modello:\n{content}\n")
        
        # Aggiungi la risposta alla cronologia dei messaggi
        agent_memory.append({"role": "assistant", "content": content})
        
        # Controlla se abbiamo una risposta finale
        answer = extract_answer(content)
        
        if not answer and "Final Answer:" not in content and "Action:" not in content:
            return content

        if answer:
            print(f"🎯 Final Answer: {answer}")
            return answer
        
        # Altrimenti, estrai l'azione dello strumento
        tool_name, tool_param = extract_tool_call(content)
        if not tool_name:
            print("⚠️ Nessuna azione valida trovata. Interrompo.")
            return "Mi dispiace, non sono riuscito a elaborare correttamente la richiesta."
        
        if tool_name not in tools:
            print(f"⚠️ Strumento '{tool_name}' non disponibile.")
            observation = f"ERRORE: Lo strumento '{tool_name}' non è disponibile. Strumenti disponibili: {', '.join(tools.keys())}"
        else:
            # Esegui lo strumento e ottieni l'osservazione
            print(f"🔧 Esecuzione tool: {tool_name}({tool_param})")
            try:
                observation = tools[tool_name](tool_param)
                print(f"📡 Observation: {observation}")
            except Exception as e:
                observation = f"ERRORE durante l'esecuzione di {tool_name}: {str(e)}"
                print(f"⚠️ {observation}")
        
        # Se c'è un errore di "Nessuna informazione disponibile", diamo istruzioni più specifiche
        if "Nessuna informazione disponibile" in observation:
            correction_message = f"""Observation: {observation}

NOTA: Assicurati di utilizzare il nome della città corretto. Prova con una di queste città disponibili: Roma, Milano, Napoli."""
            agent_memory.append({"role": "user", "content": correction_message})
        else:
            # Aggiungi l'osservazione standard alla cronologia dei messaggi con enfasi sull'uso esatto
            agent_memory.append({
                "role": "user", 
                "content": f"""Observation: {observation}

IMPORTANTE: Utilizza esattamente questa informazione senza modificarla. Non inventare o modificare temperature, condizioni meteo o altri dati.

Continua il tuo ragionamento."""
            })
    
    print("🚨 Iterazioni massime raggiunte.")
    return "Mi dispiace, non sono riuscito a completare l'operazione nel limite di iterazioni consentito."

if __name__ == "__main__":
    print("🤖 Agente AI - Scrivi una domanda o digita 'exit' per uscire.\n")

    while True:
        user_input = input("💬 Tu: ").strip()
        
        if user_input.lower() in {"exit", "quit", ""}:
            print("👋 Uscita. A presto!")
            break
        
        result = run_agent(user_input)
        print(f"\n💬 Risposta: {result}\n")
