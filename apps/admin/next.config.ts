import type { NextConfig } from 'next'
const isStandalone = process.env.NEXT_STANDALONE === 'true'

const nextConfig: NextConfig = {
  output: isStandalone ? 'standalone' : undefined,
  transpilePackages: ['@econexao/ui', '@econexao/contracts'],
}

export default nextConfig
