import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import ProgramPage from "../pages/ProgramPage";

// Mock AuthContext
vi.mock("../auth/AuthContext", () => ({
  useAuth: () => ({
    user: { id: 1, email: "admin@test.com", role: "admin", plan: "premium" },
    token: "fake-token",
    isLoading: false,
    error: null,
    login: vi.fn(),
    logout: vi.fn(),
    clearError: vi.fn(),
  }),
}));

const MOCK_PLAN = {
  plan_id: "test-plan",
  goal: "maintain",
  daily_calorie_target: 2000,
  days: [
    {
      day: 1,
      day_name: "Lundi",
      total_calories: 1980,
      meals: [
        {
          meal_type: "breakfast",
          name: "Porridge aux fruits rouges",
          ingredients: ["80g flocons d'avoine", "250ml lait végétal"],
          prep_time_minutes: 10,
          calories: 400,
          macros: { protein_g: 12, carbs_g: 65, fat_g: 8 },
          instructions: "Faire chauffer le lait, ajouter les flocons.",
        },
      ],
    },
  ],
  shopping_list: ["Flocons d'avoine", "Lait végétal", "Fruits rouges"],
  nutritional_summary: {
    avg_daily_calories: 2000,
    avg_protein_g: 100,
    avg_carbs_g: 150,
    avg_fat_g: 58,
  },
  _demo: true,
};

vi.mock("../api/nutrition", () => ({
  nutritionApi: {
    generateMealPlan: vi.fn().mockResolvedValue(MOCK_PLAN),
    analyzeWithAI: vi.fn(),
  },
}));

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>
  );
}

describe("ProgramPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the page title", () => {
    renderWithProviders(<ProgramPage />);
    expect(screen.getByText("Programme alimentaire")).toBeInTheDocument();
  });

  it("renders all config selects", () => {
    renderWithProviders(<ProgramPage />);
    expect(screen.getByText("Maintien")).toBeInTheDocument();
    expect(screen.getByText("7 jours")).toBeInTheDocument();
    expect(screen.getByText("3 repas/jour")).toBeInTheDocument();
    expect(screen.getByText("Moyen")).toBeInTheDocument();
  });

  it("renders generate button", () => {
    renderWithProviders(<ProgramPage />);
    expect(
      screen.getByRole("button", { name: /générer mon programme ia/i })
    ).toBeInTheDocument();
  });

  it("shows budget options", () => {
    renderWithProviders(<ProgramPage />);
    expect(screen.getByText("Économique")).toBeInTheDocument();
    expect(screen.getByText("Premium")).toBeInTheDocument();
  });

  it("displays meal plan after generation", async () => {
    renderWithProviders(<ProgramPage />);
    fireEvent.click(screen.getByRole("button", { name: /générer mon programme ia/i }));

    await waitFor(() => {
      expect(screen.getByText("Porridge aux fruits rouges")).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  it("shows day tabs after plan is generated", async () => {
    renderWithProviders(<ProgramPage />);
    fireEvent.click(screen.getByRole("button", { name: /générer mon programme ia/i }));

    await waitFor(() => {
      expect(screen.getByRole("tab", { name: "Lundi" })).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  it("shows demo badge when _demo is true", async () => {
    renderWithProviders(<ProgramPage />);
    fireEvent.click(screen.getByRole("button", { name: /générer mon programme ia/i }));

    await waitFor(() => {
      expect(screen.getByText(/mode démo/i)).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  it("shows shopping list toggle", async () => {
    renderWithProviders(<ProgramPage />);
    fireEvent.click(screen.getByRole("button", { name: /générer mon programme ia/i }));

    await waitFor(() => {
      expect(screen.getByText(/liste de courses/i)).toBeInTheDocument();
    }, { timeout: 3000 });
  });
});
