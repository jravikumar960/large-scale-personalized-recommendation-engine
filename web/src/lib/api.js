const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";
const TIMEOUT_MS = 30000;

async function request(path) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), TIMEOUT_MS);
  try {
    const response = await fetch(`${API_BASE}${path}`, { signal: controller.signal });
    if (!response.ok) {
      let detail = `Request failed with status ${response.status}`;
      try {
        const body = await response.json();
        if (typeof body?.detail === "string") detail = body.detail;
        else if (Array.isArray(body?.detail)) detail = body.detail.map((item) => item?.msg || JSON.stringify(item)).join("; ");
        else if (body?.detail && typeof body.detail === "object") detail = JSON.stringify(body.detail);
        else if (typeof body?.message === "string") detail = body.message;
      } catch {
        // Keep the generic status message when the body is not JSON.
      }
      throw new Error(detail);
    }
    return response.json();
  } catch (error) {
    if (error.name === "AbortError") throw new Error("Request timed out");
    throw error;
  } finally {
    clearTimeout(timeout);
  }
}

export const api = {
  health: () => request("/health"),
  recommendations: (userId, k) => request(`/recommendations/${userId}?k=${k}`),
  item: (itemId) => request(`/items/${itemId}`),
  search: (q, genre, limit = 12) => request(`/movies/search?q=${encodeURIComponent(q || "")}&genre=${encodeURIComponent(genre || "")}&limit=${limit}`),
  metrics: () => request("/metrics"),
};
