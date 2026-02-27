export async function chatCorebot(apiUrl, apiKey, message, mode = 'auto', history = [], appContext = {}) {
  const res = await fetch(`${apiUrl}/chat/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': apiKey
    },
    body: JSON.stringify({ message, history, mode, app_context: appContext })
  });
  return res.json();
}
