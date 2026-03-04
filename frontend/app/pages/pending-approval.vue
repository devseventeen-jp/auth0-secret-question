<template>
  <div class="pending-container">
    <div class="pending-card">
      <h1>Approval Pending</h1>
      <p>Your secret answer is submitted and waiting for administrator approval.</p>
      <NuxtLink to="/secret-question" class="btn">Review Submission</NuxtLink>
    </div>
  </div>
</template>

<style scoped>
.pending-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #0f172a;
  color: #f8fafc;
}

.pending-card {
  width: min(560px, 92vw);
  background: rgba(15, 23, 42, 0.85);
  border: 1px solid rgba(148, 163, 184, 0.25);
  border-radius: 16px;
  padding: 28px;
  text-align: center;
}

h1 {
  margin: 0 0 10px;
  font-size: 1.8rem;
}

p {
  margin: 0 0 20px;
  color: #cbd5e1;
}

.btn {
  display: inline-block;
  padding: 10px 16px;
  border-radius: 8px;
  text-decoration: none;
  color: #0f172a;
  background: #22d3ee;
  font-weight: 600;
}
</style>
