/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  
  // Docker 배포를 위한 standalone 빌드
  output: 'standalone',
  
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    NEXT_PUBLIC_WS_URL: process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000',
  },
}

module.exports = nextConfig

