<template>
  <div class="callback-redirect">Redirecting...</div>
</template>

<script setup>
const route = useRoute();
const target = route.fullPath.replace(/^\/auth\/callback/, '/callback');
await navigateTo(target, { replace: true });
</script>
