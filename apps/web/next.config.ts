import type { NextConfig } from 'next'

const apiBaseUrl = (
  process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api/v1'
).replace(/\/$/, '')
const isE2EBuild = process.env.NEXT_E2E_BUILD === 'true'

const nextConfig: NextConfig = {
  distDir: process.env.NEXT_DIST_DIR ?? '.next',
  output: isE2EBuild ? undefined : 'standalone',
  transpilePackages: ['@econexao/contracts', '@econexao/ui'],
  async rewrites() {
    return [
      {
        source: '/api/public/:path*',
        destination: `${apiBaseUrl}/:path*`,
      },
    ]
  },
}

export default nextConfig
