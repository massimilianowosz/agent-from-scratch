# Il modo migliore per capire come funziona un Agente AI? Scriverne uno da zero

Un agente AI minimale, costruito **da zero** con Python o Node.js, per capire davvero come funziona un agent loop basato su LLM e tool esterni.

Questo progetto ti guida step-by-step nella creazione di un agente capace di:

- ragionare in modo esplicito (`Thought`)
- eseguire tool esterni (`Action`)
- analizzare risultati (`Observation`)
- fornire risposte finali (`Final Answer`)

---

## 📦 Requisiti

Assicurati di avere installato:

- [Python 3.10+](https://www.python.org/downloads/) **oppure** [Node.js 18+](https://nodejs.org/)
- [Ollama](https://ollama.com/download) (per eseguire i modelli LLM in locale)
- Modello AI: `qwen2.5`

Scarica il modello con:

```bash
ollama pull qwen2.5
```

---

## 🚀 Setup (Python)

```bash
# Clona il progetto
git clone https://github.com/massimilianowosz/agent-from-scratch.git
cd agent-from-scratch

# Crea un ambiente virtuale
python -m venv venv
source venv/bin/activate  # Su Windows: .\venv\Scripts\activate

# Installa le dipendenze
pip install -r requirements.txt

# Avvia l'agente
python agent.py
```

---

## 🚀 Setup (Node.js)

```bash
# Clona il progetto
git clone https://github.com/massimilianowosz/agent-from-scratch.git
cd agent-from-scratch

# Installa le dipendenze
npm install ollama readline

# Avvia l'agente
node agent.js
```

---

## 🤖 Cosa può fare l'agente?

Al momento l'agente supporta 2 strumenti (mock):

- `meteo_tool(città)` – Restituisce il meteo di una città
- `activity_tool(condizione)` – Suggerisce un'attività in base alle condizioni meteo

Esempi di prompt:

- **"Che tempo fa a Milano?"**
- **"Cosa potrei fare oggi a Roma?"**

---

## 🔄 Come funziona

L'agente implementa un ciclo ReAct (Reasoning + Acting) che:

1. Riceve un input dall'utente
2. Genera pensieri espliciti per ragionare sul problema
3. Decide quale strumento utilizzare
4. Esegue lo strumento e analizza i risultati
5. Fornisce una risposta finale all'utente

Questo approccio permette all'agente di:
- Mostrare il suo ragionamento in modo trasparente
- Utilizzare strumenti esterni per recuperare informazioni
- Combinare diverse fonti di dati per rispondere in modo intelligente

---

## 📂 Struttura del progetto

| File        | Descrizione                                                 |
|-------------|-------------------------------------------------------------|
| `agent.py`  | Agente completo in Python con loop ReAct                    |
| `agent.js`  | Versione Node.js con lo stesso schema di reasoning          |
| `README.md` | Questo file 📘                                              |

---

## 📜 Licenza

MIT — Sentiti libero di forkare, modificare, remixare ✨

---

## ✍️ Autore

Creato con pazienza e codice da [Massimiliano Wosz](https://github.com/massimilianowosz)