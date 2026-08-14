import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // The API is a separate service (FastAPI on Cloud Run), so every call is
  // cross-origin. The base URL is a build-time public var rather than a rewrite:
  // the chat endpoint streams Server-Sent Events, and putting a Next.js rewrite
  // in front of an SSE response is a reliable way to get it buffered.
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000",
  },
};

export default nextConfig;
