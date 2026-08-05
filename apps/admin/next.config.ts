import type { NextConfig } from 'next'

const apiBaseUrl = (
  process.env.NEXT_PUBLIC_API_URL ?? 'https://fifty-donkeys-vanish.loca.lt/api/v1'
).replace(/\/$/, '')
const isStandalone = process.env.NEXT_STANDALONE === 'true'

const nextConfig: NextConfig = {
  output: isStandalone ? 'standalone' : undefined,
  transpilePackages: ['@econexao/ui'],
  async rewrites() {
    return [
      {
        source: '/api/admin/:path*',
        destination: `${apiBaseUrl}/:path*`,
      },
      {
        source: '/api/public/:path*',
        destination: `${apiBaseUrl}/:path*`,
      },
    ]
  },
}

export default nextConfig
