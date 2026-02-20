import { ref } from 'vue';
import { useAuth0 } from '@auth0/auth0-vue';

const missingAuth0Message =
  '[Auth0] SDK is not initialized. Check NUXT_PUBLIC_AUTH0_DOMAIN and NUXT_PUBLIC_AUTH0_CLIENT_ID, then restart the frontend container.';

export const useSafeAuth0 = () => {
  const auth0 = useAuth0();

  if (auth0) {
    return auth0;
  }

  const fail = async () => {
    console.error(missingAuth0Message);
    throw new Error(missingAuth0Message);
  };

  return {
    isAuthenticated: ref(false),
    isLoading: ref(false),
    idTokenClaims: ref(null),
    error: ref(null),
    user: ref(null),
    loginWithRedirect: fail,
    getAccessTokenSilently: fail,
    logout: () => {
      console.error(missingAuth0Message);
    },
  };
};
