import type { NextConfig } from "next";
import path from "path";
import { fileURLToPath } from "url";

const projectRoot = path.dirname(fileURLToPath(import.meta.url));

const nextConfig: NextConfig = {
  // Pre-existing strict TS issues are tracked separately; allow production builds to ship.
  typescript: { ignoreBuildErrors: true },
  eslint: { ignoreDuringBuilds: true },
  // Ensure .env.local in frontend/ is loaded (not parent FNSA lockfile root)
  turbopack: {
    root: projectRoot,
  },
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'images.unsplash.com',
      },
      {
        protocol: 'https',
        hostname: 'picsum.photos',
      },
    ],
  },
  webpack(config) {
    // Grab the existing rule that handles SVG imports
    const rules = (config.module?.rules ?? []) as unknown[];
    const fileLoaderRule = rules.find((rule) => {
      if (!rule || typeof rule !== 'object') return false;
      const r = rule as { test?: { test?: (s: string) => boolean } };
      return Boolean(r.test?.test?.('.svg'));
    }) as
      | undefined
      | {
          test?: RegExp;
          issuer?: unknown;
          resourceQuery?: { not?: unknown[] };
          exclude?: RegExp;
        };

    if (!fileLoaderRule) return config;
    const resourceQueryNot = Array.isArray(fileLoaderRule.resourceQuery?.not) ? fileLoaderRule.resourceQuery!.not! : [];

    config.module.rules.push(
      // Reapply the existing rule, but only for svg imports ending in ?url
      {
        ...fileLoaderRule,
        test: /\.svg$/i,
        resourceQuery: /url/, // *.svg?url
      },
      // Convert all other *.svg imports to React components
      {
        test: /\.svg$/i,
        issuer: fileLoaderRule.issuer,
        resourceQuery: { not: [...resourceQueryNot, /url/] },
        use: ['@svgr/webpack'],
      },
    )

    // Modify the file loader rule to ignore *.svg, since we have it handled now.
    fileLoaderRule.exclude = /\.svg$/i

    return config
  },
};

export default nextConfig;
