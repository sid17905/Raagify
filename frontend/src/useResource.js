import { useCallback, useEffect, useState } from "react";
import { api, message } from "./api";
export default function useResource(url) {
  const [state, setState] = useState({ data: null, loading: true, error: "" }),
    [version, setVersion] = useState(0);
  const refresh = useCallback(() => setVersion((v) => v + 1), []);
  useEffect(() => {
    const controller = new AbortController();
    setState({ data: null, loading: true, error: "" });
    api
      .get(url, { signal: controller.signal })
      .then((r) => {
        if (!controller.signal.aborted)
          setState({ data: r.data, loading: false, error: "" });
      })
      .catch((e) => {
        if (!controller.signal.aborted)
          setState({ data: null, loading: false, error: message(e) });
      });
    return () => controller.abort();
  }, [url, version]);
  return {
    ...state,
    refresh,
    setData: (data) => setState({ data, loading: false, error: "" }),
  };
}
