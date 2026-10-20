/** @type {import('next').NextConfig} */
const nextConfig = {
  // O painel de resultados lê este arquivo em tempo de execução.
  outputFileTracingIncludes: { "/rota/[slug]": ["./painel.html"] },
};

export default nextConfig;
