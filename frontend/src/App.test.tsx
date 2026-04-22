// @vitest-environment jsdom

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import { AuthProvider } from "./hooks/useAuth";
import { I18nProvider } from "./i18n";

describe("App", () => {
  it("renders login screen for anonymous users", async () => {
    localStorage.clear();
    localStorage.setItem("proposal-language", "en");

    render(
      <BrowserRouter>
        <I18nProvider>
          <AuthProvider>
            <App />
          </AuthProvider>
        </I18nProvider>
      </BrowserRouter>,
    );

    expect(await screen.findByRole("button", { name: /enter workspace/i })).toBeTruthy();
  });
});
