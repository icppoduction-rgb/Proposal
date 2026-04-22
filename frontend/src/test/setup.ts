import "@testing-library/jest-dom";
import { vi } from "vitest";

const storage = new Map<string, string>();

const languagePacks = {
  en: {
    app: { loading: "Initializing workspace" },
    common: {
      email: "Email",
      password: "Password",
      logout: "Logout",
    },
    login: {
      submit: "Enter workspace",
      error: "Unable to sign in",
      language: {
        en: "EN",
        ru: "RU",
      },
    },
  },
  ru: {
    app: { loading: "\u0418\u043d\u0438\u0446\u0438\u0430\u043b\u0438\u0437\u0430\u0446\u0438\u044f \u043f\u0430\u043d\u0435\u043b\u0438 \u0443\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u0438\u044f" },
    common: {
      email: "Email",
      password: "\u041f\u0430\u0440\u043e\u043b\u044c",
      logout: "\u0412\u044b\u0445\u043e\u0434",
    },
    login: {
      submit: "\u0412\u043e\u0439\u0442\u0438 \u0432 \u0440\u0430\u0431\u043e\u0447\u0443\u044e \u043e\u0431\u043b\u0430\u0441\u0442\u044c",
      error: "\u041d\u0435 \u0443\u0434\u0430\u043b\u043e\u0441\u044c \u0432\u044b\u043f\u043e\u043b\u043d\u0438\u0442\u044c \u0432\u0445\u043e\u0434",
      language: {
        en: "EN",
        ru: "RU",
      },
    },
  },
};

Object.defineProperty(window, "localStorage", {
  value: {
    getItem(key: string) {
      return storage.get(key) ?? null;
    },
    setItem(key: string, value: string) {
      storage.set(key, value);
    },
    removeItem(key: string) {
      storage.delete(key);
    },
    clear() {
      storage.clear();
    },
  },
  configurable: true,
});

vi.stubGlobal(
  "fetch",
  vi.fn(async (input: string | URL | Request) => {
    const url = typeof input === "string" ? input : input instanceof URL ? input.toString() : input.url;

    if (url.endsWith("/api/i18n/en")) {
      return new Response(JSON.stringify(languagePacks.en), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    }

    if (url.endsWith("/api/i18n/ru")) {
      return new Response(JSON.stringify(languagePacks.ru), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    }

    return new Response("Not Found", { status: 404 });
  }),
);
