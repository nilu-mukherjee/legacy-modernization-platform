/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable React strict mode for better development warnings.
  reactStrictMode: true,

  // Proxy API calls to the FastAPI backend in development.
  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: "http://localhost:8000/api/v1/:path*",
      },
    ];
  },

  // Allow GitHub avatar images.
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "avatars.githubusercontent.com",
      },
    ],
  },
};

export default nextConfig;
