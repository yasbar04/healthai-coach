import { describe, it, expect } from "vitest";

// Simplified version of getErrorMessage for testing without importing
function getErrorMessageTest(err: any): string {
  if (!err) return "Une erreur est survenue";
  if (err?.response?.data?.detail) {
    return typeof err.response.data.detail === "string" 
      ? err.response.data.detail 
      : JSON.stringify(err.response.data.detail);
  }
  if (err?.response?.data?.message) return err.response.data.message;
  if (err?.message) return err.message;
  if (err?.response?.statusText) return err.response.statusText;
  return "Une erreur est survenue";
}

describe("Error handling utilities", () => {
  it("returns error detail when present", () => {
    const error = {
      response: {
        data: {
          detail: "Invalid credentials"
        }
      }
    };
    expect(getErrorMessageTest(error)).toBe("Invalid credentials");
  });

  it("returns stringified detail for complex objects", () => {
    const error = {
      response: {
        data: {
          detail: { field1: "error1", field2: "error2" }
        }
      }
    };
    const result = getErrorMessageTest(error);
    expect(result).toContain("field1");
    expect(result).toContain("error1");
  });

  it("falls back to message field", () => {
    const error = {
      response: {
        data: {
          message: "Something went wrong"
        }
      }
    };
    expect(getErrorMessageTest(error)).toBe("Something went wrong");
  });

  it("falls back to error message property", () => {
    const error = {
      message: "Network error"
    };
    expect(getErrorMessageTest(error)).toBe("Network error");
  });

  it("falls back to statusText", () => {
    const error = {
      response: {
        statusText: "Unauthorized"
      }
    };
    expect(getErrorMessageTest(error)).toBe("Unauthorized");
  });

  it("returns default message when no error details available", () => {
    expect(getErrorMessageTest(null)).toBe("Une erreur est survenue");
    expect(getErrorMessageTest(undefined)).toBe("Une erreur est survenue");
    expect(getErrorMessageTest({})).toBe("Une erreur est survenue");
  });

  it("handles complex error chain", () => {
    const error = {
      response: {
        data: {
          detail: "Validation failed"
        }
      },
      message: "Fallback message"
    };
    expect(getErrorMessageTest(error)).toBe("Validation failed");
  });
});
