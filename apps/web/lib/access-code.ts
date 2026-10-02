export const ACCESS_CODE_STORAGE_KEY = "onko-demo-access-code";
export const ACCESS_CODE_COOKIE = "onko_access_code";

export function getBrowserAccessCode(): string {
  if (typeof window === "undefined") return "";
  return window.sessionStorage.getItem(ACCESS_CODE_STORAGE_KEY) ?? "";
}

export function saveBrowserAccessCode(code: string) {
  if (typeof window === "undefined") return;
  window.sessionStorage.setItem(ACCESS_CODE_STORAGE_KEY, code);
  // No Max-Age/Expires: this is intentionally a session cookie so Server Components
  // can forward the same code without persisting it beyond the browser session.
  document.cookie = `${ACCESS_CODE_COOKIE}=${encodeURIComponent(code)}; Path=/; SameSite=Lax`;
}

export function clearBrowserAccessCode() {
  if (typeof window === "undefined") return;
  window.sessionStorage.removeItem(ACCESS_CODE_STORAGE_KEY);
  document.cookie = `${ACCESS_CODE_COOKIE}=; Path=/; Max-Age=0; SameSite=Lax`;
}
