<template>
  <div class="dashboard-container">
    <nav class="navbar">
      <div class="brand">Secret Question Authentication App</div>
      <div class="user-menu" v-if="user">
        <span class="user-name">{{ user.name }}</span>
        <button @click="logout" class="btn-logout">Logout</button>
      </div>
    </nav>

    <main class="content">
      <div class="welcome-card">
        <h1>Welcome, {{ backendUser?.username || user?.nickname }}!</h1>
        <p>Your account is fully activated and secured by Secret Question.</p>
        
        <div class="status-badge" v-if="backendUser?.is_approved">
          <span class="dot"></span>
          Account Verified
        </div>
      </div>

      <div class="info-grid">
        
        <div class="info-card">
          <h3>Last Login</h3>
          <p class="value">{{ currentTime }}</p>
          <p class="sub">Device: Browser ({{ browserInfo }})</p>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { useAuth0 } from '@auth0/auth0-vue';

const { user, logout: auth0Logout, getAccessTokenSilently } = useAuth0();
const config = useRuntimeConfig();
const backendUser = ref(null);

const currentTime = new Date().toLocaleString();
const browserInfo = navigator.userAgent.split(' ')[0];

const logout = () => {
    auth0Logout({ logoutParams: { returnTo: window.location.origin } });
};

onMounted(async () => {
    try {
        const token = await getAccessTokenSilently();
        backendUser.value = await $fetch(`${config.public.apiBaseUrl}/api/auth/me`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        // Redirect if not approved
        if (!backendUser.value.is_approved) {
            router.push('/secret-question');
        }
    } catch (e) {
        console.error("Dashboard profile fetch failed:", e);
    }
});
</script>

<style scoped>
.dashboard-container {
  min-height: 100vh;
  background: #f8fafc;
  color: #1e293b;
  font-family: 'Inter', sans-serif;
}

.navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 2rem;
  background: #fff;
  border-bottom: 1px solid #e2e8f0;
}

.brand { font-weight: 800; font-size: 1.25rem; color: #3b82f6; }
.user-menu { display: flex; align-items: center; gap: 15px; }
.user-name { font-weight: 500; font-size: 0.9rem; }
.btn-logout { 
  background: none; border: 1px solid #e2e8f0; padding: 6px 12px; 
  border-radius: 6px; cursor: pointer; transition: 0.2s;
}
.btn-logout:hover { background: #f1f5f9; }

.content { max-width: 1000px; margin: 40px auto; padding: 0 20px; }

.welcome-card {
  background: white; padding: 40px; border-radius: 20px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  margin-bottom: 30px;
  text-align: center;
}
.welcome-card h1 { font-size: 2.25rem; margin-bottom: 10px; }
.welcome-card p { color: #64748b; margin-bottom: 25px; }

.status-badge {
  display: inline-flex; align-items: center; gap: 8px;
  background: #ecfdf5; color: #059669; font-weight: 600;
  padding: 8px 16px; border-radius: 9999px; font-size: 0.875rem;
}
.dot { width: 8px; height: 8px; background: #10b981; border-radius: 50%; }

.info-grid { display: grid; grid-template-columns: 1fr; gap: 20px; }
.info-card {
  background: white; padding: 25px; border-radius: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}
.info-card h3 { font-size: 0.875rem; text-transform: uppercase; color: #64748b; margin-bottom: 15px; }
.info-card .value { font-size: 1.25rem; font-weight: 700; margin-bottom: 5px; }
.info-card .sub { font-size: 0.75rem; color: #94a3b8; }
</style>
