export async function chatCorebot(apiUrl, apiKey, message, mode = 'auto', history = [], appContext = {}) {
  const res = await fetch(`${apiUrl}/chat/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': apiKey
    },
    body: JSON.stringify({ message, history, mode, app_context: appContext })
  });
  const raw = await res.text();
  let payload = {};
  try {
    payload = JSON.parse(raw);
  } catch {
    payload = { detail: raw };
  }
  if (!res.ok) {
    throw new Error(`Corebot request failed (${res.status}): ${payload.detail || raw}`);
  }
  return payload;
}
