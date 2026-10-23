/**
 * Servicio de llamadas HTTP y streaming SSE al backend de FastAPI.
 */

export async function loginApi(email, password) {
  const res = await fetch('/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Error al iniciar sesión');
  }
  return res.json();
}

export async function registerApi(email, password) {
  const res = await fetch('/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Error al registrar usuario');
  }
  return res.json();
}

export async function getDocumentsApi(token) {
  const res = await fetch('/documents', {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    throw new Error('Error al listar documentos');
  }
  return res.json();
}

export async function uploadDocumentApi(file, token) {
  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch('/documents/upload', {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: formData,
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Error al subir y procesar el documento');
  }
  return res.json();
}

export async function deleteDocumentApi(documentId, token) {
  const res = await fetch(`/documents/${documentId}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    throw new Error('Error al eliminar el documento');
  }
  return res.json();
}

/**
 * Lee el flujo de Server-Sent Events (SSE) desde POST /chat/stream.
 */
export async function streamChatApi({
  message,
  documentId = null,
  token,
  onCitations,
  onToken,
  onDone,
  onError,
}) {
  let doneCalled = false;
  const safeDone = () => {
    if (!doneCalled && onDone) {
      doneCalled = true;
      onDone();
    }
  };

  try {
    const response = await fetch('/chat/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        message,
        document_id: documentId || null,
        match_count: 4,
      }),
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || 'Error en la petición de chat');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        const trimmed = line.trim();
        if (trimmed.startsWith('data: ')) {
          try {
            const data = JSON.parse(trimmed.slice(6));
            if (data.type === 'citations' && onCitations) {
              onCitations(data.citations);
            } else if (data.type === 'token' && onToken) {
              onToken(data.content);
            } else if (data.type === 'done') {
              safeDone();
            } else if (data.type === 'error' && onError) {
              onError(new Error(data.message));
            }
          } catch {
            // Ignorar líneas no parseables
          }
        }
      }
    }

    safeDone();
  } catch (error) {
    if (onError) onError(error);
  }
}
