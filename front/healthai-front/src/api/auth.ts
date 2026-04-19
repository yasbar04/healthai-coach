import { api } from "./client";
import type { User, LoginResponse } from "../types";

export async function login(email: string, password: string): Promise<LoginResponse> {
  const res = await api.post("/auth/login", { email, password });
  return res.data;
}

export async function me(): Promise<User> {
  const res = await api.get("/users/me");
  return res.data;
}
