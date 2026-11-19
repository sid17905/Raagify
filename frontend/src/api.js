import axios from "axios";
export const api = axios.create({
  baseURL: "/api",
  withCredentials: true,
  xsrfCookieName: "XSRF-TOKEN",
  xsrfHeaderName: "X-XSRF-TOKEN",
});
api.interceptors.response.use(
  (r) => r,
  (e) => {
    if (e.response?.status === 401 && !e.config?.url?.startsWith("/auth/"))
      window.dispatchEvent(new Event("raagify:expired"));
    return Promise.reject(e);
  },
);
let csrf;
export async function ensureCsrf(force = false) {
  if (!csrf || force) {
    const { data } = await api.get("/auth/csrf");
    csrf = data.token;
  }
  return csrf;
}
export async function write(config) {
  const token = await ensureCsrf();
  return api({
    ...config,
    headers: { ...config.headers, "X-XSRF-TOKEN": token },
  });
}
export function message(error) {
  return (
    error?.response?.data?.message || error?.message || "Something went wrong"
  );
}
