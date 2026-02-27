const form = document.getElementById("chat-form");
const input = document.getElementById("chat-input");
const log = document.getElementById("chat-log");
const sessionEl = document.getElementById("session-id");
const fileInput = document.getElementById("chat-file");
const fileName = document.getElementById("file-name");

const sessionId = crypto.randomUUID();
sessionEl.textContent = sessionId;

const appendMessage = (role, text) => {
  const wrapper = document.createElement("div");
  wrapper.className = `message ${role}`;

  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.textContent = role === "user" ? "U" : "A";

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;

  wrapper.appendChild(avatar);
  wrapper.appendChild(bubble);
  log.appendChild(wrapper);
  log.scrollTop = log.scrollHeight;
};

const autoResize = () => {
  input.style.height = "auto";
  input.style.height = `${Math.min(input.scrollHeight, 140)}px`;
};

input.addEventListener("input", autoResize);

fileInput.addEventListener("change", () => {
  const file = fileInput.files[0];
  fileName.textContent = file ? file.name : "Nenhum arquivo";
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = input.value.trim();
  const file = fileInput.files[0];
  if (!message && !file) return;

  if (file && file.type !== "application/pdf") {
    appendMessage("assistant", "Apenas PDF e permitido.");
    return;
  }

  if (message) {
    appendMessage("user", message);
  }
  if (file) {
    appendMessage("user", `Arquivo PDF enviado: ${file.name}`);
  }
  input.value = "";
  autoResize();

  const sendBtn = document.getElementById("send-btn");
  sendBtn.disabled = true;
  sendBtn.textContent = "Enviando...";

  try {
    const payload = new FormData();
    payload.append("user_input", message);
    payload.append("session_id", sessionId);
    payload.append("user_id", "web");
    if (file) {
      payload.append("file", file);
    }

    const response = await fetch("/api/chat", {
      method: "POST",
      body: payload,
    });

    if (!response.ok) {
      throw new Error("Erro ao enviar mensagem.");
    }

    const data = await response.json();
    appendMessage("assistant", data.assistant || "Sem resposta.");
  } catch (error) {
    appendMessage("assistant", "Nao consegui enviar sua mensagem agora.");
  } finally {
    sendBtn.disabled = false;
    sendBtn.textContent = "Enviar";
    fileInput.value = "";
    fileName.textContent = "Nenhum arquivo";
  }
});

input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
});
