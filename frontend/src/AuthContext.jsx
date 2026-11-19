import { createContext, useContext, useEffect, useState } from "react";
import { api, ensureCsrf, write } from "./api";
const Context = createContext(null);
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null),
    [loading, setLoading] = useState(true),
    [error, setError] = useState("");
  async function restore() {
    setLoading(true);
    setError("");
    try {
      setUser((await api.get("/auth/session")).data.user);
    } catch (e) {
      if (e.response?.status !== 401)
        setError("Unable to connect to Raagify. Please retry.");
      setUser(null);
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => {
    restore();
    const expired = () => setUser(null);
    window.addEventListener("raagify:expired", expired);
    return () => window.removeEventListener("raagify:expired", expired);
  }, []);
  async function login(email, password) {
    await ensureCsrf(true);
    await write({
      method: "post",
      url: "/auth/login",
      data: new URLSearchParams({ email, password }),
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
    await ensureCsrf(true);
    setUser((await api.get("/auth/me")).data);
  }
  async function register(data) {
    await write({ method: "post", url: "/auth/register", data });
    await login(data.email, data.password);
  }
  async function logout() {
    await write({ method: "post", url: "/auth/logout" });
    setUser(null);
    await ensureCsrf(true);
  }
  return (
    <Context.Provider
      value={{ user, loading, error, restore, login, register, logout }}
    >
      {children}
    </Context.Provider>
  );
}
export const useAuth = () => useContext(Context);
