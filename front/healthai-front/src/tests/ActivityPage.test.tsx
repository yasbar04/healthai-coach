import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import ActivityPage from "../pages/ActivityPage";

// Mock AuthContext
vi.mock("../auth/AuthContext", () => ({
  useAuth: () => ({
    user: { id: 1, email: "test@test.com", role: "admin", plan: "premium" },
    token: "fake-token",
    isLoading: false,
    error: null,
    login: vi.fn(),
    logout: vi.fn(),
    clearError: vi.fn(),
  }),
}));

// Mock usersApi
vi.mock("../api/users", () => ({
  usersApi: {
    getProfile: vi.fn().mockResolvedValue({ goal: "maintain", weight_kg: 70 }),
    updateProfile: vi.fn(),
  },
}));

// Mock activityApi
vi.mock("../api/activity", () => ({
  activityApi: {
    getRecommendation: vi.fn().mockRejectedValue(new Error("Service unavailable")),
    logActivity: vi.fn().mockResolvedValue({ id: 1 }),
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

describe("ActivityPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the page title", () => {
    renderWithProviders(<ActivityPage />);
    expect(screen.getByText("Activité physique")).toBeInTheDocument();
  });

  it("renders goal select with options", () => {
    renderWithProviders(<ActivityPage />);
    expect(screen.getByText("Perdre du poids")).toBeInTheDocument();
    expect(screen.getByText("Prendre de la masse")).toBeInTheDocument();
    expect(screen.getByText("Maintenir")).toBeInTheDocument();
    expect(screen.getByText("Endurance")).toBeInTheDocument();
  });

  it("renders fitness level select", () => {
    renderWithProviders(<ActivityPage />);
    expect(screen.getByText("Débutant")).toBeInTheDocument();
    expect(screen.getByText("Intermédiaire")).toBeInTheDocument();
    expect(screen.getByText("Avancé")).toBeInTheDocument();
  });

  it("renders generate button", () => {
    renderWithProviders(<ActivityPage />);
    const btn = screen.getByRole("button", { name: /générer ma séance ia/i });
    expect(btn).toBeInTheDocument();
  });

  it("loads demo workout when service is unavailable", async () => {
    renderWithProviders(<ActivityPage />);
    const btn = screen.getByRole("button", { name: /générer ma séance ia/i });
    fireEvent.click(btn);

    await waitFor(() => {
      expect(screen.getByText(/mode démo/i)).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  it("shows demo workout content after error fallback", async () => {
    renderWithProviders(<ActivityPage />);
    fireEvent.click(screen.getByRole("button", { name: /générer ma séance ia/i }));

    await waitFor(() => {
      expect(screen.getByText(/minutes/i)).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  it("shows duration options including 45 minutes", () => {
    renderWithProviders(<ActivityPage />);
    expect(screen.getByText("45 minutes")).toBeInTheDocument();
    expect(screen.getByText("1 heure")).toBeInTheDocument();
  });
});
