// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  ssr: false, // SPA mode often easier for Auth0 integration in simple apps unless we need SEO
  runtimeConfig: {
    public: {
      auth0Domain: process.env.NUXT_PUBLIC_AUTH0_DOMAIN || process.env.AUTH0_DOMAIN,
      auth0ClientId: process.env.NUXT_PUBLIC_AUTH0_CLIENT_ID || process.env.AUTH0_CLIENT_ID,
      auth0Audience: process.env.NUXT_PUBLIC_AUTH0_AUDIENCE || process.env.AUTH0_AUDIENCE,
      auth0RedirectPath: process.env.NUXT_PUBLIC_AUTH0_REDIRECT_PATH || '/callback',
      apiBaseUrl: process.env.NUXT_PUBLIC_API_BASE_URL,
      approvalRedirectUrl: process.env.NUXT_PUBLIC_APPROVAL_REDIRECT_URL
    }
  }
})
