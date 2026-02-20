<template>
  <div class="callback-container">
    <div class="status-card">
      <div class="spinner" v-if="!error"></div>
      <h2>{{ status }}</h2>
      <p class="sub-message">{{ subMessage }}</p>

      <div v-if="error" class="error-box">
        <p>{{ error }}</p>
        <button @click="goHome" class="btn btn-error">Back to Login</button>
      </div>
    </div>
  </div>
</template>

<script setup>
const { isAuthenticated, isLoading, idTokenClaims, error: auth0Error } = useSafeAuth0();
const config = useRuntimeConfig();
const router = useRouter();

const status = ref('Processing Authentication...');
const subMessage = ref('Securing your connection with Auth0...');
const error = ref(null);

const goHome = () => router.push('/secret-question');

watch([isLoading, isAuthenticated], async ([newLoading, newAuth]) => {
  if (newLoading) return;

  if (auth0Error.value) {
    status.value = 'Authentication Failed';
    error.value = auth0Error.value.message || 'Auth0 Error';
    return;
  }

  if (!newAuth) {
    router.push('/');
    return;
  }

  try {
    status.value = 'Verifying with Backend...';
    subMessage.value = 'Registering your profile in our secure database...';

    const token = idTokenClaims.value?.__raw;
    if (!token) throw new Error('No ID Token found. Please try again.');

    const response = await $fetch(`${config.public.apiBaseUrl}/api/auth/authorize`, {
      method: 'POST',
      body: { id_token: token },
      headers: { Authorization: `Bearer ${token}` }
    });

    if (response.status === 'needs_secret' || response.status === 'needs_approval') {
      status.value = 'Security Verification Required';
      subMessage.value = 'Redirecting to verification page...';
      setTimeout(() => router.push('/secret-question'), 1000);
      return;
    }

    status.value = 'Access Granted!';
    subMessage.value = 'Welcome back! Redirecting...';
    setTimeout(() => {
      const redirectUrl = config.public.approvalRedirectUrl;
      if (!redirectUrl) {
        router.push('/dashboard');
        return;
      }

      if (redirectUrl.startsWith('http')) {
        window.location.href = redirectUrl;
        return;
      }

      const normalizedPath = redirectUrl.startsWith('/') ? redirectUrl : `/${redirectUrl}`;
      router.push(normalizedPath);
    }, 1000);
  } catch (e) {
    status.value = 'Verification Failed';
    error.value = e.data?.message || e.message;
  }
}, { immediate: true });
</script>

<style scoped>
.callback-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: #1a1a2e;
  font-family: 'Inter', sans-serif;
  color: #fff;
}

.status-card {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  padding: 50px;
  border-radius: 24px;
  text-align: center;
  max-width: 450px;
  width: 90%;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.spinner {
  width: 50px;
  height: 50px;
  border: 4px solid rgba(79, 172, 254, 0.1);
  border-left-color: #4facfe;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}

h2 { margin-bottom: 10px; font-weight: 600; }
.sub-message { color: #a0a0a0; font-size: 0.9rem; }

.error-box {
  margin-top: 30px;
  padding: 20px;
  background: rgba(255, 87, 87, 0.1);
  border: 1px solid rgba(255, 87, 87, 0.3);
  border-radius: 12px;
  color: #ff5757;
}

.btn {
  margin-top: 15px;
  border: none;
  border-radius: 8px;
  padding: 10px 20px;
  cursor: pointer;
  transition: 0.3s;
}

.btn-error { background: #ff5757; color: #fff; }

@keyframes spin { to { transform: rotate(360deg); } }
</style>
