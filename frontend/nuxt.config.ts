// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  srcDir: 'app/',
  ssr: false, // SPA mode often easier for Auth0 integration in simple apps unless we need SEO
  runtimeConfig: {
    public: {
      auth0Domain: process.env.NUXT_PUBLIC_AUTH0_DOMAIN || process.env.AUTH0_DOMAIN,
      auth0ClientId: process.env.NUXT_PUBLIC_AUTH0_CLIENT_ID || process.env.AUTH0_CLIENT_ID,
      auth0Audience: process.env.NUXT_PUBLIC_AUTH0_AUDIENCE || process.env.AUTH0_AUDIENCE,
      auth0Scope: process.env.NUXT_PUBLIC_AUTH0_SCOPE || 'openid profile email',
      auth0RedirectPath: process.env.NUXT_PUBLIC_AUTH0_REDIRECT_PATH || '/callback',
      apiBaseUrl: process.env.NUXT_PUBLIC_API_BASE_URL,
      approvalRedirectUrl: process.env.NUXT_PUBLIC_APPROVAL_REDIRECT_URL,
      authSessionGuardEnabled: process.env.NUXT_PUBLIC_AUTH_SESSION_GUARD_ENABLED || 'false',
      authSessionValidateUrl: process.env.NUXT_PUBLIC_AUTH_SESSION_VALIDATE_URL,
      authLoginUrl: process.env.NUXT_PUBLIC_AUTH_LOGIN_URL,
      authLoginRedirectParam: process.env.NUXT_PUBLIC_AUTH_LOGIN_REDIRECT_PARAM || 'return_to',
      authPublicPaths: process.env.NUXT_PUBLIC_AUTH_PUBLIC_PATHS || '/,/callback,/auth/callback'
    }
  }
})
