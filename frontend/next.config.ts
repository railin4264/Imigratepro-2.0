import path from "path";
import type { NextConfig } from "next";

// NEXT_PUBLIC_API_URL is inlined into the client bundle at build time (see
// src/lib/api.ts) -- if it's left unset in a production build, that bundle
// falls back to plain http://localhost:8000, and every request (session
// cookie included) would go out over an unencrypted connection in the
// deployed app. Local dev is intentionally exempt: http://localhost has no
// real network path to intercept, and forcing a cert for `next dev` would
// just be friction with no security benefit.
if (process.env.NODE_ENV === "production") {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL;
  if (!apiUrl) {
    throw new Error(
      "NEXT_PUBLIC_API_URL must be set for a production build (no insecure localhost fallback in prod)."
    );
  }
  if (!apiUrl.startsWith("https://")) {
    throw new Error(`NEXT_PUBLIC_API_URL must use https:// in production, got: ${apiUrl}`);
  }
}

const nextConfig: NextConfig = {
  turbopack: {
    root: path.join(__dirname),
  },
};

export default nextConfig;
