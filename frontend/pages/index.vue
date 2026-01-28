<template>
  <div class="container">
    <div class="glass-card">
      <h1 class="title">Secure Auth System</h1>
      <p class="subtitle">Next-gen authentication with Secret Question</p>
      
      <div v-if="isLoading" class="loader-container">
        <div class="loader"></div>
      </div>
      
      <div v-else class="content">
        <div v-if="isAuthenticated" class="user-welcome">
          <p>Welcome back, <strong>{{ user?.name }}</strong></p>
          <button @click="logout" class="btn btn-secondary">Logout</button>
          <br>
          <NuxtLink to="/dashboard" class="btn btn-primary">Go to Dashboard</NuxtLink>
        </div>
        <div v-else class="login-action">
          <button @click="login" class="btn btn-primary btn-large">Log In</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useAuth0 } from '@auth0/auth0-vue';

const { loginWithRedirect, logout: auth0Logout, user, isAuthenticated, isLoading } = useAuth0();

const login = () => {
    const config = useRuntimeConfig();
    loginWithRedirect({
        authorizationParams: {
            audience: config.public.auth0Audience
        }
    });
};

const logout = () => {
    auth0Logout({ logoutParams: { returnTo: window.location.origin } });
};
</script>

<style scoped>
.container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  color: #fff;
  font-family: 'Inter', sans-serif;
}

.glass-card {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  padding: 40px;
  text-align: center;
  width: 100%;
  max-width: 400px;
  box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
  animation: fadeIn 0.8s ease-out;
}

.title {
  font-size: 2.5rem;
  margin-bottom: 10px;
  background: linear-gradient(to right, #4facfe 0%, #00f2fe 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.subtitle {
  color: #a0a0a0;
  margin-bottom: 30px;
}

.btn {
  border: none;
  border-radius: 8px;
  padding: 12px 24px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: inline-block;
  text-decoration: none;
  margin: 5px;
}

.btn-primary {
  background: #4facfe;
  color: #fff;
}

.btn-primary:hover {
  background: #00f2fe;
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(79, 172, 254, 0.4);
}

.btn-large {
  width: 100%;
  padding: 15px;
  font-size: 1.1rem;
}

.btn-secondary {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.2);
}

.loader {
  border: 4px solid rgba(255, 255, 255, 0.1);
  border-left-color: #4facfe;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  display: inline-block;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
