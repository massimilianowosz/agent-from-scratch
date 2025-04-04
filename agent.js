const readline = require('readline');
const { Ollama } = require('ollama');

// 🧠 Memoria conversazionale globale
let agentMemory = [];

const client = new Ollama();

// 🔧 TOOL MOCK: meteo
function meteo_tool(città) {
  città = città.trim().toLowerCase();
  const meteo = {
    roma: 'A Roma ci sono 18°C e cielo sereno.',
    milano: 'A Milano ci sono 15°C con pioggia leggera.',
    napoli: 'A Napoli ci sono 20°C e sole pieno.'
  };
  return meteo[città] || `Nessuna informazione disponibile per ${città}.`;
}

// 🔧 TOOL MOCK: suggerisce attività in base al meteo
function activity_tool(condition) {
  const cond = condition.toLowerCase();
  if (cond.includes('sereno') || cond.includes('sole')) {
    return 'Ti consiglio di fare una passeggiata al parco o visitare un museo all\'aperto.';
  } else if (cond.includes('pioggia')) {
    return 'Potresti visitare un museo o andare al cinema.';
  } else if (cond.includes('coperto')) {
    return 'Una giornata perfetta per una libreria o un caffè accogliente.';
  } else {
    return 'Non ho un suggerimento preciso per queste condizioni.';
  }
}

const tools = {
  meteo_tool,
  activity_tool
};

// 🧠 PROMPT
const systemPrompt = `Sei un agente AI che ragiona passo dopo passo e può usare strumenti esterni.

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
`;

// 🔍 Extractors
function extractToolCall(content) {
  const actionMatch = content.match(/Action:\s*(.*)/);
  const inputMatch = content.match(/Action Input:\s*(.*)/);
  if (!actionMatch || !inputMatch) return [null, null];
  return [actionMatch[1].trim(), inputMatch[1].trim()];
}

function extractAnswer(content) {
  const match = content.match(/Final Answer:\s*(.*)/);
  if (!match) return null;

  let answer = match[1].trim();

  const lines = content.split('\n');
  let i = lines.findIndex(line => line.includes("Final Answer:")) + 1;
  while (i < lines.length && lines[i] && !lines[i].startsWith("Thought:") && !lines[i].startsWith("Action:")) {
    answer += '\n' + lines[i].trim();
    i++;
  }

  return answer;
}

// 🚀 AGENTE
async function runAgent(userInput) {
  if (agentMemory.length === 0) {
    agentMemory.push({ role: "system", content: systemPrompt });
  }

  agentMemory.push({ role: "user", content: userInput });

  const maxIterations = 5;
  let iterations = 0;

  while (iterations < maxIterations) {
    iterations++;
    console.log(`\n🧠 Iterazione ${iterations}: Generazione risposta...\n`);

    const response = await client.chat({
        model: 'qwen2.5',
        messages: agentMemory
      });
    const content = response.message.content;
    console.log(`📤 Output del modello:\n${content}\n`);

    agentMemory.push({ role: "assistant", content });

    const answer = extractAnswer(content);
    if (answer) {
      console.log(`🎯 Final Answer: ${answer}`);
      return answer;
    }

    const [toolName, toolParam] = extractToolCall(content);
    if (!toolName) {
      return "⚠️ Nessuna azione valida trovata. Interrompo.";
    }

    if (!tools[toolName]) {
      const errorObs = `ERRORE: Lo strumento '${toolName}' non è disponibile. Strumenti disponibili: ${Object.keys(tools).join(', ')}`;
      agentMemory.push({ role: "user", content: `Observation: ${errorObs}` });
      continue;
    }

    let observation = "";
    try {
        const cleanParam = toolParam.replace(/^["']|["']$/g, '');
        observation = tools[toolName](cleanParam);
        console.log(`🔧 Esecuzione tool: ${toolName}(${toolParam})`);
        console.log(`📡 Observation: ${observation}`);
    } catch (err) {
        observation = `ERRORE durante l'esecuzione di ${toolName}: ${err.message}`;
    }

    if (observation.includes("Nessuna informazione disponibile")) {
      agentMemory.push({
        role: "user",
        content: `Observation: ${observation}

NOTA: Assicurati di usare una delle seguenti città: Roma, Milano, Napoli.`
      });
    } else {
      agentMemory.push({
        role: "user",
        content: `Observation: ${observation}

IMPORTANTE: Utilizza esattamente questa informazione senza modificarla. Non inventare o modificare temperature, condizioni meteo o altri dati.

Continua il tuo ragionamento.`
      });
    }
  }

  return "🚨 Iterazioni massime raggiunte. Non sono riuscito a completare la richiesta.";
}

// 💬 INTERFACCIA CLI
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

console.log("🤖 Agente AI - Scrivi una domanda o digita 'exit' per uscire.");

rl.prompt();
rl.on('line', async (input) => {
  const userInput = input.trim();
  if (userInput === 'exit' || userInput === 'quit') {
    console.log("👋 Uscita. A presto!");
    rl.close();
    return;
  }

  const result = await runAgent(userInput);
  console.log(`\n💬 Risposta: ${result}\n`);
  rl.prompt();
});
