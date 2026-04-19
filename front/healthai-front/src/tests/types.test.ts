import { describe, it, expect } from "vitest";
import type { User, LoginResponse, Activity, NutritionEntry, BiometricEntry } from "../types";

describe("Type definitions", () => {
  it("User type is correctly defined", () => {
    const user: User = {
      id: "123",
      email: "user@example.com",
      username: "testuser",
      role: "admin"
    };
    expect(user.id).toBe("123");
    expect(user.email).toBe("user@example.com");
  });

  it("LoginResponse type is correctly defined", () => {
    const response: LoginResponse = {
      access_token: "token123",
      token_type: "Bearer"
    };
    expect(response.access_token).toBe("token123");
    expect(response.token_type).toBe("Bearer");
  });

  it("Activity type enforces required fields", () => {
    const activity: Activity = {
      id: "1",
      user_id: "user1",
      activity_type: "running",
      duration_minutes: 30,
      date: "2024-03-18"
    };
    expect(activity.activity_type).toBe("running");
    expect(activity.duration_minutes).toBe(30);
  });

  it("NutritionEntry type enforces meal types", () => {
    const entry: NutritionEntry = {
      id: "1",
      user_id: "user1",
      meal_type: "breakfast",
      food_items: ["eggs", "toast"],
      calories: 400,
      protein_g: 20,
      carbs_g: 40,
      fat_g: 15,
      date: "2024-03-18"
    };
    expect(entry.meal_type).toBe("breakfast");
    expect(entry.food_items).toHaveLength(2);
  });

  it("BiometricEntry type includes health metrics", () => {
    const entry: BiometricEntry = {
      id: "1",
      user_id: "user1",
      weight_kg: 75,
      heart_rate: 72,
      date: "2024-03-18"
    };
    expect(entry.weight_kg).toBe(75);
    expect(entry.heart_rate).toBe(72);
  });
});
