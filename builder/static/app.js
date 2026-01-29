const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');
const chatHistory = document.getElementById('chat-history');
const codeBlock = document.querySelector('#code-output code');

function getCsrfToken() {
  const tokenInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
  return tokenInput ? tokenInput.value : '';
}

function addMessage(role, content) {
  const wrapper = document.createElement('div');
  wrapper.className = `chat-message ${role}`;
  const roleLabel = document.createElement('span');
  roleLabel.className = 'role';
  roleLabel.textContent = role.charAt(0).toUpperCase() + role.slice(1);
  const paragraph = document.createElement('p');
  paragraph.textContent = content;
  wrapper.appendChild(roleLabel);
  wrapper.appendChild(paragraph);
  chatHistory.appendChild(wrapper);
  chatHistory.scrollTop = chatHistory.scrollHeight;
}

chatForm?.addEventListener('submit', async (event) => {
  event.preventDefault();
  const message = chatInput.value.trim();
  if (!message) return;

  addMessage('user', message);
  chatInput.value = '';

  try {
    const response = await fetch('/chat/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCsrfToken(),
      },
      body: JSON.stringify({ message }),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || 'Unable to generate code.');
    }

    addMessage('assistant', data.assistant_reply);
    if (codeBlock) {
      codeBlock.textContent = data.streamlit_code;
    }
  } catch (error) {
    addMessage('assistant', `Error: ${error.message}`);
  }
});
