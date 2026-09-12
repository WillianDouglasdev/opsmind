import { useCallback, useEffect, useState } from "react";

export default function useApiResource(loader) {
  const [state, setState] = useState({ status: "loading", data: null, error: null });
  const [revision, setRevision] = useState(0);
  const retry = useCallback(() => {
    setState({ status: "loading", data: null, error: null });
    setRevision((value) => value + 1);
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    queueMicrotask(() => {
      if (!controller.signal.aborted) setState({ status: "loading", data: null, error: null });
    });
    loader({ signal: controller.signal }).then((data) => {
      if (!controller.signal.aborted) setState({ status: "success", data, error: null });
    }).catch((error) => {
      if (!controller.signal.aborted) {
        setState({ status: "error", data: null, error });
        if (import.meta.env.DEV) console.error("[OpsMind] Leitura operacional indisponível", error);
      }
    });
    return () => controller.abort();
  }, [loader, revision]);

  return { ...state, retry };
}
