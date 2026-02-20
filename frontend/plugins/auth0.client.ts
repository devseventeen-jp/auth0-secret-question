import { createAuth0 } from '@auth0/auth0-vue';

export default defineNuxtPlugin((nuxtApp) => {
  const config = useRuntimeConfig();
  const domain = config.public.auth0Domain;
  const clientId = config.public.auth0ClientId;

  if (!domain || !clientId) {
    console.error('[Auth0] Missing configuration. Set NUXT_PUBLIC_AUTH0_DOMAIN / NUXT_PUBLIC_AUTH0_CLIENT_ID (or AUTH0_DOMAIN / AUTH0_CLIENT_ID).', {
      domain,
      clientId,
    });
    return;
  }

  const rawRedirectPath = config.public.auth0RedirectPath || '/callback';
  const redirectPath = rawRedirectPath.startsWith('/') ? rawRedirectPath : `/${rawRedirectPath}`;
  const redirectUri = `${window.location.origin}${redirectPath}`;

  nuxtApp.vueApp.use(
    createAuth0({
      domain,
      clientId,
      authorizationParams: {
        redirect_uri: redirectUri,
        audience: config.public.auth0Audience,
      },
      cacheLocation: "localstorage"
    })
  );
//    if (process.client) {
//        const auth0 = createAuth0({
//            domain: config.public.auth0Domain,
//            clientId: config.public.auth0ClientId,
//            authorizationParams: {
//                redirect_uri: window.location.origin + '/callback',
//                audience: config.public.auth0Audience
//            },
//            cacheLocation: "localstorage", 
//        });
//        nuxtApp.vueApp.use(auth0);
//    }
});
