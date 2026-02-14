/** API base URL - uses Render backend when on Vercel if not explicitly set */
export function getApiBase(): string {
  const explicit = process.env.NEXT_PUBLIC_API_URL;
  if (explicit) return explicit;
  if (typeof window !== "undefined" && window.location?.hostname?.endsWith("vercel.app")) {
    return "https://waspos.onrender.com";
  }
  return "http://localhost:8000";
}
