import { createAuth0 } from '@auth0/auth0-vue';

export default defineNuxtPlugin((nuxtApp) => {
    const config = useRuntimeConfig();

  nuxtApp.vueApp.use(
    createAuth0({
      domain: config.public.auth0Domain,
      clientId: config.public.auth0ClientId,
      authorizationParams: {
        redirect_uri: window.location.origin + '/callback',
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
