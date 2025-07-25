import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'Permissions-Policy',
            value: 'compute-pressure=()'
          }
        ]
      }
    ];
  }
};

export default nextConfig;
