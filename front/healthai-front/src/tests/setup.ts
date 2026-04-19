import { expect, afterEach, vi } from "vitest";
import { cleanup } from "@testing-library/react";

// Auto cleanup after each test
afterEach(() => {
  cleanup();
});

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};

if (typeof global !== "undefined") {
  (global as any).localStorage = localStorageMock;
}
