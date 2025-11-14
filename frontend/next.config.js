/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  webpack: (config, { isServer }) => {
    // Fix para undici y otras dependencias de Node.js
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        net: false,
        tls: false,
      };
    }
    
    // Ignorar módulos problemáticos en el cliente
    config.externals = config.externals || [];
    if (!isServer) {
      config.externals.push({
        'undici': 'commonjs undici',
      });
    }
    
    return config;
  },
}

module.exports = nextConfig

