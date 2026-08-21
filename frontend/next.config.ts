import path from "node:path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Turbopack otherwise walks up looking for a workspace root and finds an
  // unrelated lockfile above the git repo (outside this project entirely) --
  // pin it explicitly to this directory to silence that false positive.
  turbopack: {
    root: path.resolve(__dirname),
  },
  // Without this, the browser's default Cross-Origin-Opener-Policy blocks
  // the postMessage Google's account-chooser popup uses to hand back the
  // sign-in credential -- the button appears to work (account picker opens,
  // an account can be chosen) but the credential never reaches our
  // callback, so no request to /api/auth/google ever fires. Found live via
  // a real deployment, not locally (localhost doesn't trigger the same
  // browser popup-isolation behavior a real cross-origin HTTPS deploy does).
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          {
            key: "Cross-Origin-Opener-Policy",
            value: "same-origin-allow-popups",
          },
        ],
      },
    ];
  },
};

export default nextConfig;
