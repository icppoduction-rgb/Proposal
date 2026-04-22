// @vitest-environment jsdom

import { act, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { usePolling } from "./usePolling";

function PollingProbe(props: { loader: () => Promise<number>; interval?: number }) {
  const { data, loading, error } = usePolling(props.loader, props.interval);

  return (
    <div>
      <span data-testid="loading">{loading ? "true" : "false"}</span>
      <span data-testid="data">{data === null ? "null" : String(data)}</span>
      <span data-testid="error">{error ?? ""}</span>
    </div>
  );
}

describe("usePolling", () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  it("does not start overlapping requests while the previous poll is still running", async () => {
    vi.useFakeTimers();

    let resolveLoader: ((value: number) => void) | null = null;
    const loader = vi.fn(
      () =>
        new Promise<number>((resolve) => {
          resolveLoader = resolve;
        }),
    );

    render(<PollingProbe loader={loader} interval={1000} />);
    expect(loader).toHaveBeenCalledTimes(1);

    await act(async () => {
      vi.advanceTimersByTime(5000);
    });
    expect(loader).toHaveBeenCalledTimes(1);

    await act(async () => {
      resolveLoader?.(42);
      await Promise.resolve();
      await Promise.resolve();
    });

    expect(screen.getByTestId("data").textContent).toBe("42");
    expect(screen.getByTestId("loading").textContent).toBe("false");

    await act(async () => {
      vi.advanceTimersByTime(999);
    });
    expect(loader).toHaveBeenCalledTimes(1);

    await act(async () => {
      vi.advanceTimersByTime(1);
    });
    expect(loader).toHaveBeenCalledTimes(2);
  });
});
