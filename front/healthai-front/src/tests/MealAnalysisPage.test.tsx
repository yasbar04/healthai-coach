import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import MealAnalysisPage from "../pages/MealAnalysisPage";

// Mock AuthContext — premium user to bypass PremiumGate
vi.mock("../auth/AuthContext", () => ({
  useAuth: () => ({
    user: { id: 1, email: "premium@test.com", role: "user", plan: "premium" },
    token: "fake-token",
    isLoading: false,
    error: null,
    login: vi.fn(),
    logout: vi.fn(),
    clearError: vi.fn(),
  }),
}));

const MOCK_ANALYSIS = {
  foods_detected: [
    {
      name: "Salade verte",
      quantity_g: 100,
      calories: 25,
      macros: { protein_g: 2, carbs_g: 3, fat_g: 0.5, fiber_g: 2, sugar_g: 1, sodium_mg: 10 },
    },
    {
      name: "Thon au naturel",
      quantity_g: 130,
      calories: 143,
      macros: { protein_g: 30, carbs_g: 0, fat_g: 2.5, fiber_g: 0, sugar_g: 0, sodium_mg: 280 },
    },
  ],
  total_calories: 353,
  macros: { protein_g: 34, carbs_g: 27, fat_g: 12, fiber_g: 5, sugar_g: 4, sodium_mg: 386 },
  health_score: 86,
  imbalances: ["Apport en glucides complexes modéré"],
  suggestions: ["Ajouter une portion de légumes verts"],
  meal_type_detected: "lunch",
  analysis_confidence: 0.88,
  _demo: true,
};

vi.mock("../api/nutrition", () => ({
  nutritionApi: {
    analyzeWithAI: vi.fn().mockResolvedValue(MOCK_ANALYSIS),
    generateMealPlan: vi.fn(),
  },
}));

// Mock recharts to avoid SVG rendering issues in jsdom
vi.mock("recharts", () => ({
  RadarChart: ({ children }: any) => <div data-testid="radar-chart">{children}</div>,
  Radar: () => null,
  PolarGrid: () => null,
  PolarAngleAxis: () => null,
  ResponsiveContainer: ({ children }: any) => <div>{children}</div>,
  Tooltip: () => null,
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

describe("MealAnalysisPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the page title", () => {
    renderWithProviders(<MealAnalysisPage />);
    expect(screen.getByText("Analyse de repas par IA")).toBeInTheDocument();
  });

  it("renders the drop zone", () => {
    renderWithProviders(<MealAnalysisPage />);
    expect(screen.getByLabelText(/zone d'upload/i)).toBeInTheDocument();
  });

  it("renders analyze button (disabled without file)", () => {
    renderWithProviders(<MealAnalysisPage />);
    const btn = screen.getByRole("button", { name: /analyser ce repas/i });
    expect(btn).toBeDisabled();
  });

  it("shows health score after analysis", async () => {
    renderWithProviders(<MealAnalysisPage />);

    const file = new File(["fake-image"], "repas.jpg", { type: "image/jpeg" });
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => {
      const btn = screen.getByRole("button", { name: /analyser ce repas/i });
      expect(btn).not.toBeDisabled();
    });

    fireEvent.click(screen.getByRole("button", { name: /analyser ce repas/i }));

    await waitFor(() => {
      expect(screen.getByText("86")).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  it("displays detected foods after analysis", async () => {
    renderWithProviders(<MealAnalysisPage />);

    const file = new File(["img"], "meal.png", { type: "image/png" });
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    fireEvent.change(input, { target: { files: [file] } });

    fireEvent.click(screen.getByRole("button", { name: /analyser ce repas/i }));

    await waitFor(() => {
      expect(screen.getByText("Salade verte")).toBeInTheDocument();
      expect(screen.getByText("Thon au naturel")).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  it("shows imbalances section after analysis", async () => {
    renderWithProviders(<MealAnalysisPage />);

    const file = new File(["img"], "meal.jpg", { type: "image/jpeg" });
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    fireEvent.change(input, { target: { files: [file] } });

    fireEvent.click(screen.getByRole("button", { name: /analyser ce repas/i }));

    await waitFor(() => {
      expect(screen.getByText("Apport en glucides complexes modéré")).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  it("shows suggestions after analysis", async () => {
    renderWithProviders(<MealAnalysisPage />);

    const file = new File(["img"], "meal.jpg", { type: "image/jpeg" });
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    fireEvent.change(input, { target: { files: [file] } });

    fireEvent.click(screen.getByRole("button", { name: /analyser ce repas/i }));

    await waitFor(() => {
      expect(screen.getByText("Ajouter une portion de légumes verts")).toBeInTheDocument();
    }, { timeout: 3000 });
  });
});

describe("MealAnalysisPage — freemium gate", () => {
  it("shows premium gate for freemium users", () => {
    vi.mocked(vi.importMock("../auth/AuthContext")).useAuth = () => ({
      user: { id: 2, email: "free@test.com", role: "user", plan: "freemium" },
      token: "tok",
      isLoading: false,
      error: null,
      login: vi.fn(),
      logout: vi.fn(),
      clearError: vi.fn(),
    });
  });
});
