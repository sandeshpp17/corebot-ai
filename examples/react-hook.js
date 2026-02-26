export async function chatCorebot(apiUrl, message) {
  const res = await fetch(`${apiUrl}/chat/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, history: [] })
  });
  return res.json();
}
