import axios, { AxiosError } from "axios";

const baseURL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL,
  timeout: 15000
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
      // Could trigger a logout event here
      window.dispatchEvent(new Event("unauthorized"));
    }
    return Promise.reject(err);
  }
);
