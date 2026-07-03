import axios, { AxiosError } from "axios";

const baseURL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL,
  timeout: 120000,
});

// Client dédié aux appels longs (analyse photo llava ~2-4 min)
export const slowApi = axios.create({
  baseURL,
  timeout: 300000, // 5 min
});

// Utility to extract error message
export function getErrorMessage(err: any): string {
  if (!err) return "Une erreur est survenue";
  
  // Axios error with response data
  if (err?.response?.data?.detail) {
    return typeof err.response.data.detail === "string" 
      ? err.response.data.detail 
      : JSON.stringify(err.response.data.detail);
  }
  
  // Generic errors
  if (err?.response?.data?.message) return err.response.data.message;
  if (err?.message) return err.message;
  if (err?.response?.statusText) return err.response.statusText;
  
  return "Une erreur est survenue";
}

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("healthai_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (r) => r,
  (err: AxiosError) => {
    if (err?.response?.status === 401) {
      localStorage.removeItem("healthai_token");
      window.dispatchEvent(new Event("unauthorized"));
    }
    return Promise.reject(err);
  }
);

// Client dédié au microservice de recommandations
export const recClient = axios.create({
  baseURL: import.meta.env.VITE_REC_SERVICE_URL || "http://localhost:8001/api/v1",
  timeout: 30000,
});

recClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("healthai_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

slowApi.interceptors.request.use((config) => {
  const token = localStorage.getItem("healthai_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

slowApi.interceptors.response.use(
  (r) => r,
  (err: AxiosError) => {
    if (err?.response?.status === 401) {
      localStorage.removeItem("healthai_token");
      window.dispatchEvent(new Event("unauthorized"));
    }
    return Promise.reject(err);
  }
);
