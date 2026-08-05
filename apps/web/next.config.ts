import type { NextConfig } from 'next'

const apiBaseUrl = (
  process.env.NEXT_PUBLIC_API_URL ?? 'https://econexao-api.onrender.com/api/v1'
).replace(/\/$/, '')
const isStandalone = process.env.NEXT_STANDALONE === 'true'

const nextConfig: NextConfig = {
  distDir: process.env.NEXT_DIST_DIR ?? '.next',
  output: isStandalone ? 'standalone' : undefined,
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
