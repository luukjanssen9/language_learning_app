import path from "node:path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Turbopack otherwise walks up looking for a workspace root and finds an
  // unrelated lockfile above the git repo (outside this project entirely) --
  // pin it explicitly to this directory to silence that false positive.
  turbopack: {
    root: path.resolve(__dirname),
  },
};

export default nextConfig;
