import { useEffect, useRef, useState } from 'react';

interface UseAsyncEffectReturn {
  loading: boolean;
  error: string | null;
}

/**
 * useEffect for async operations with built-in cancellation safety.
 * Pass an async `effect` that receives a `cancelled()` checker.
 * If the component unmounts or deps change, `cancelled()` returns true
 * before data is committed, preventing state updates on stale components.
 */
export function useAsyncEffect(
  effect: (cancelled: () => boolean) => Promise<void>,
  deps: React.DependencyList
): UseAsyncEffectReturn {
  const cancelledRef = useRef(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    cancelledRef.current = false;

    async function run() {
      try {
        setLoading(true);
        setError(null);
        await effect(() => cancelledRef.current);
      } catch (err) {
        if (cancelledRef.current) return;
        setError(err instanceof Error ? err.message : '加载失败');
      } finally {
        if (!cancelledRef.current) setLoading(false);
      }
    }

    run();

    return () => {
      cancelledRef.current = true;
    };
  }, deps);

  return { loading, error };
}
