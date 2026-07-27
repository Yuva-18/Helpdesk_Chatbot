// Chat interface logic: sends queries to /chat and renders responses

const API_BASE_URL = ""; // relative — frontend is served same-origin by app/main.py

const messagesEl = document.getElementById("messages");
const formEl = document.getElementById("chat-form");
const inputEl = document.getElementById("question-input");
const sendButtonEl = document.getElementById("send-button");

function scrollToBottom() {
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function addUserMessage(text) {
  const row = document.createElement("div");
  row.className = "bubble-row user";

  const bubble = document.createElement("div");
  bubble.className = "bubble user";
  bubble.textContent = text;

  row.appendChild(bubble);
  messagesEl.appendChild(row);
  scrollToBottom();
}

function addTypingIndicator() {
  const row = document.createElement("div");
  row.className = "bubble-row bot";
  row.id = "typing-row";

  const bubble = document.createElement("div");
  bubble.className = "bubble bot-typing";

  const indicator = document.createElement("div");
  indicator.className = "typing-indicator";
  indicator.innerHTML = "<span></span><span></span><span></span>";

  bubble.appendChild(indicator);
  row.appendChild(bubble);
  messagesEl.appendChild(row);
  scrollToBottom();
}

function removeTypingIndicator() {
  const row = document.getElementById("typing-row");
  if (row) {
    row.remove();
  }
}

function addBotAnswer(data) {
  const row = document.createElement("div");
  row.className = "bubble-row bot";

  const bubble = document.createElement("div");
  bubble.className = data.is_confident ? "bubble bot-confident" : "bubble bot-fallback";

  const answerText = document.createElement("div");
  answerText.textContent = data.answer;
  bubble.appendChild(answerText);

  if (data.is_confident) {
    const footer = document.createElement("div");
    footer.className = "bubble-footer";

    const dot = document.createElement("span");
    dot.className = "status-dot confident";

    const label = document.createElement("span");
    label.className = "footer-text";
    label.textContent = data.category ? `${data.category} · verified answer` : "Verified answer";

    footer.appendChild(dot);
    footer.appendChild(label);
    bubble.appendChild(footer);
  } else if (data.support_email) {
    const link = document.createElement("a");
    link.className = "support-link";
    link.href = `mailto:${data.support_email}`;
    link.textContent = `Email ${data.support_email}`;
    bubble.appendChild(link);
  }

  row.appendChild(bubble);
  messagesEl.appendChild(row);
  scrollToBottom();
}

function addErrorMessage(text) {
  const row = document.createElement("div");
  row.className = "bubble-row bot";

  const bubble = document.createElement("div");
  bubble.className = "bubble bot-error";
  bubble.textContent = text;

  row.appendChild(bubble);
  messagesEl.appendChild(row);
  scrollToBottom();
}

async function askQuestion(question) {
  addTypingIndicator();
  sendButtonEl.disabled = true;
  inputEl.disabled = true;

  try {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });

    removeTypingIndicator();

    if (!response.ok) {
      addErrorMessage("Something went wrong reaching the helpdesk service. Please try again.");
      return;
    }

    const data = await response.json();
    addBotAnswer(data);
  } catch (err) {
    removeTypingIndicator();
    addErrorMessage("Couldn't reach the helpdesk service. Please check your connection and try again.");
  } finally {
    sendButtonEl.disabled = false;
    inputEl.disabled = false;
    inputEl.focus();
  }
}

formEl.addEventListener("submit", (event) => {
  event.preventDefault();
  const question = inputEl.value.trim();
  if (!question) {
    return;
  }
  addUserMessage(question);
  inputEl.value = "";
  askQuestion(question);
});
