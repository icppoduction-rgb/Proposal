import { createContext, useContext, useEffect, useMemo, useState } from "react";

export type Language = "en" | "ru";

type TranslationDictionary = Record<string, unknown>;
type TranslationParams = Record<string, string | number>;

interface I18nContextValue {
  language: Language;
  loading: boolean;
  setLanguage: (language: Language) => void;
  t: (key: string, params?: TranslationParams) => string;
  tEnum: (baseKey: string, value: string) => string;
}

const LANGUAGE_STORAGE_KEY = "proposal-language";
const DEFAULT_LANGUAGE: Language = "ru";

const fallbackMessages: TranslationDictionary = {
  app: { loading: "Initializing workspace" },
  common: {
    email: "Email",
    password: "Password",
    logout: "Logout",
    na: "n/a",
    role: {
      admin: "Administrator",
      analyst: "Analyst",
    },
    artifactStatus: {
      candidate: "Candidate",
      promoted: "In production",
      deprecated: "Deprecated",
    },
    jobStatus: {
      pending: "Queued",
      running: "Running",
      completed: "Completed",
      failed: "Failed",
      cancelled: "Cancelled",
    },
    sourceType: {
      host: "Host",
      network: "Network",
    },
    validationStatus: {
      pending: "Pending validation",
      validated: "Validated",
      failed: "Validation failed",
    },
    activeState: {
      active: "Active",
      inactive: "Inactive",
    },
  },
  login: {
    error: "Unable to sign in",
    submit: "Enter workspace",
    language: {
      en: "EN",
      ru: "RU",
    },
  },
  api: {
    errors: {
      internalServerError: "Internal server error",
      unauthorized: "Authorization is required",
      forbidden: "Access denied",
      notFound: "Resource not found",
      badRequest: "Invalid request",
      request: "Request failed",
      requestWithStatus: "Request failed: {status}",
    },
  },
};

const I18nContext = createContext<I18nContextValue | undefined>(undefined);

let activeMessages: TranslationDictionary = fallbackMessages;

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function getStoredLanguage(): Language {
  const storedValue = localStorage.getItem(LANGUAGE_STORAGE_KEY);
  return storedValue === "en" || storedValue === "ru" ? storedValue : DEFAULT_LANGUAGE;
}

function resolveTranslationValue(messages: TranslationDictionary, key: string): unknown {
  return key.split(".").reduce<unknown>((currentValue, segment) => {
    if (!isRecord(currentValue)) {
      return undefined;
    }
    return currentValue[segment];
  }, messages);
}

function interpolate(template: string, params?: TranslationParams): string {
  if (!params) {
    return template;
  }
  return template.replace(/\{(\w+)\}/g, (_, key: string) => String(params[key] ?? `{${key}}`));
}

function translate(messages: TranslationDictionary, key: string, params?: TranslationParams): string {
  const value = resolveTranslationValue(messages, key);
  if (typeof value !== "string") {
    return key;
  }
  return interpolate(value, params);
}

async function fetchLanguagePack(language: Language): Promise<TranslationDictionary> {
  const response = await fetch(`/api/i18n/${language}`);
  if (!response.ok) {
    throw new Error(`Unable to load language pack: ${language}`);
  }
  return (await response.json()) as TranslationDictionary;
}

export function translateApiErrorMessage(message: string, status?: number): string {
  const normalizedMessage = message.trim();
  const messageKeyByError: Record<string, string> = {
    "Internal Server Error": "api.errors.internalServerError",
    Unauthorized: "api.errors.unauthorized",
    "Missing bearer token": "api.errors.unauthorized",
    "Token expired": "api.errors.unauthorized",
    "Invalid token": "api.errors.unauthorized",
    "Refresh token expired": "api.errors.unauthorized",
    "Invalid refresh token": "api.errors.unauthorized",
    Forbidden: "api.errors.forbidden",
    "Not Found": "api.errors.notFound",
    "Bad Request": "api.errors.badRequest",
  };

  if (messageKeyByError[normalizedMessage]) {
    return translate(activeMessages, messageKeyByError[normalizedMessage]);
  }
  if (!normalizedMessage) {
    return status
      ? translate(activeMessages, "api.errors.requestWithStatus", { status })
      : translate(activeMessages, "api.errors.request");
  }
  return normalizedMessage;
}

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [language, setLanguageState] = useState<Language>(() => getStoredLanguage());
  const [messages, setMessages] = useState<TranslationDictionary>(fallbackMessages);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isActive = true;
    setLoading(true);

    fetchLanguagePack(language)
      .then((nextMessages) => {
        if (!isActive) {
          return;
        }
        activeMessages = nextMessages;
        setMessages(nextMessages);
        localStorage.setItem(LANGUAGE_STORAGE_KEY, language);
      })
      .catch(() => {
        if (!isActive) {
          return;
        }
        activeMessages = fallbackMessages;
        setMessages(fallbackMessages);
      })
      .finally(() => {
        if (isActive) {
          setLoading(false);
        }
      });

    return () => {
      isActive = false;
    };
  }, [language]);

  const value = useMemo<I18nContextValue>(
    () => ({
      language,
      loading,
      setLanguage(nextLanguage) {
        if (nextLanguage !== language) {
          setLanguageState(nextLanguage);
        }
      },
      t(key, params) {
        return translate(messages, key, params);
      },
      tEnum(baseKey, enumValue) {
        const key = `${baseKey}.${enumValue}`;
        const translatedValue = translate(messages, key);
        return translatedValue === key ? enumValue : translatedValue;
      },
    }),
    [language, loading, messages],
  );

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  const context = useContext(I18nContext);
  if (!context) {
    throw new Error("useI18n must be used within I18nProvider");
  }
  return context;
}
