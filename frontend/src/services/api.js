import axios from "axios";

const TOKEN_KEY = "yelp_lab1_token";
const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api/v1";

const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    "Content-Type": "application/json"
  }
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export function extractApiError(error, fallbackMessage = "Request failed.") {
  const apiMessage = error?.response?.data?.error?.message;
  const legacyMessage = error?.response?.data?.detail;
  return apiMessage || legacyMessage || fallbackMessage;
}

export { TOKEN_KEY };
export default api;
