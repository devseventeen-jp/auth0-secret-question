<template>
  <div class="container">
    <!-- Modal -->
    <div v-if="modal.show" class="modal-overlay">
      <div class="modal-card">
        <h3>{{ modal.title }}</h3>
        <p>{{ modal.message }}</p>
        <button @click="closeModal">OK</button>
      </div>
    </div>

    <!-- loading -->
    <div v-if="loading" class="loading-state">
      <div class="loader"></div>
      <p>Loading secret question...</p>
    </div>

    <!-- approved -->
    <div v-else-if="isApproved" class="approved-box">
      <div class="icon">✅</div>
      <p>Your account is approved! Redirecting...</p>
    </div>

    <!-- answered / pending / rejected -->
    <div v-else-if="hasAnswered && !isRetrying">
      <div v-if="rejectionReason" class="rejection-box">
        <h3>Verification Rejected</h3>
        <p v-if="prevRealName" class="prev-answer">Submitted Real Name: <textarea readonly>{{ prevRealName }}</textarea></p>
        <p class="prev-answer">Submitted Answer: <textarea readonly>{{ prevAnswer }}</textarea></p>
        <div class="reason-container">
          <strong>Reason:</strong>
          <p class="reason-text">{{ rejectionReason }}</p>
        </div>
        <button @click="startRetry" class="btn-retry">Try Again</button>
      </div>
      <div v-else class="pending-box">
        <div class="icon">⏳</div>
        <h3>Approval Pending</h3>
        <p>Your answer has been submitted and is waiting for administrator approval.</p>
        <div class="prev-answer-container">
          <strong v-if="prevRealName">Submitted Real Name:</strong>
          <textarea v-if="prevRealName" readonly>{{ prevRealName }}</textarea>
          <strong>Current Answer:</strong>
          <textarea readonly>{{ prevAnswer }}</textarea>
        </div>
        <button @click="startRetry" class="btn-secondary">Change Answer</button>
      </div>
    </div>

    <!-- form -->
    <div v-else class="form-card">
      <h2>Security Question</h2>
      <p class="question-text">{{ question }}</p>
      <div class="input-group">
        <input
          v-model="realName"
          type="text"
          :placeholder="realNameRequired ? 'Enter your real name (required)' : 'Enter your real name (optional)'"
        />
      </div>
      <div class="input-group">
        <textarea
          v-model="answer"
          placeholder="Type your answer here..."
          @keydown.enter.ctrl="submitAnswer"
          rows="5"
        ></textarea>
        <p class="hint">Press Ctrl+Enter to submit</p>
      </div>
      <div class="actions">
        <button @click="submitAnswer" :disabled="!canSubmit" class="btn-primary">Submit Verification</button>
        <button v-if="hasAnswered" @click="cancelRetry" class="btn-secondary">Cancel</button>
      </div>
    </div>
  </div>
</template>

<script setup>
const { isAuthenticated, isLoading, idTokenClaims } = useSafeAuth0();
const config = useRuntimeConfig();
const router = useRouter();

const loading = ref(true);
const question = ref("");
const hasAnswered = ref(false);
const prevAnswer = ref("");
const isApproved = ref(false);
const rejectionReason = ref("");
const answer = ref("");
const realName = ref("");
const prevRealName = ref("");
const realNameRequired = ref(false);
const isRetrying = ref(false);

const modal = reactive({
  show: false,
  title: "",
  message: "",
  onClose: null
});

const showModal = (title, message, onClose = null) => {
  modal.title = title;
  modal.message = message;
  modal.onClose = onClose;
  modal.show = true;
};

const closeModal = () => {
  modal.show = false;
  if (modal.onClose) modal.onClose();
};

// Update sessionStorage when isRetrying changes
watch(isRetrying, (val) => {
  if (process.client) {
    sessionStorage.setItem("retry_mode", val ? "true" : "false");
  }
});

const fetchData = async () => {
  // Initialize isRetrying from sessionStorage
  if (process.client) {
    isRetrying.value = sessionStorage.getItem("retry_mode") === "true";
  }

  const token = idTokenClaims.value?.__raw;
  if (!token) return;

  try {
    const res = await fetch(`${config.public.apiBaseUrl}/api/auth/secret-question`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!res.ok) {
      console.error("Failed to fetch secret question", res.status);
      return;
    }

    const data = await res.json();
    question.value = data.question;
    hasAnswered.value = data.has_answered;
    prevAnswer.value = data.secret_answer;
    prevRealName.value = data.real_name || "";
    realName.value = data.real_name || "";
    realNameRequired.value = Boolean(data.real_name_required);
    isApproved.value = data.is_approved;
    rejectionReason.value = data.rejection_reason;

    // If already approved, handle redirect
    if (data.is_approved) {
      isRetrying.value = false;
      if (process.client) sessionStorage.removeItem("retry_mode");

      const redirectUrl = config.public.approvalRedirectUrl;
      if (redirectUrl) {
        if (redirectUrl.startsWith("http")) {
          // Absolute URL: Show confirmation before leaving
          if (confirm(`You have been approved! Proceed to external site: ${redirectUrl}?`)) {
             window.location.href = redirectUrl;
          }
        } else {
          // Relative path: Redirect via router
          router.push(redirectUrl);
        }
      } else {
        // Fallback or default redirect
        setTimeout(() => {
          router.push("/");
        }, 1500);
      }
    }
  } catch (e) {
    console.error("Fetch Error:", e);
  } finally {
    loading.value = false;
  }
};

const submitAnswer = async () => {
  if (!canSubmit.value) return;
  
  const token = idTokenClaims.value?.__raw;
  if (!token) {
    showModal("Authentication Error", "Session expired. Please log in again.", () => {
       window.location.href = "/";
    });
    return;
  }

  try {
    const res = await fetch(`${config.public.apiBaseUrl}/api/auth/secret-question`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ answer: answer.value, real_name: realName.value }),
    });

    const data = await res.json();

    if (res.status === 400 && data.detail === "Already approved") {
      showModal("Already Approved", "Your account has already been approved.", () => {
         isApproved.value = true;
         isRetrying.value = false;
         if (process.client) sessionStorage.removeItem("retry_mode");
         router.push("/");
      });
      return;
    }

    if (!res.ok) {
      showModal("Submission Error", data.detail || "Failed to submit answer.");
      return;
    }

    showModal("Submission Successful", "Your answer has been submitted for review.", () => {
      hasAnswered.value = true;
      isRetrying.value = false;
      if (process.client) {
        sessionStorage.removeItem("retry_mode");
      }
      rejectionReason.value = ""; 
      fetchData(); 
    });
  } catch (e) {
    console.error("Submit Error:", e);
    showModal("Error", "A network error occurred. Please try again.");
  }
};

const startRetry = async () => {
  loading.value = true;
  await fetchData();
  
  if (isApproved.value) {
    showModal("Already Approved", "Your account is already approved.", () => {
       router.push("/");
    });
    return;
  }
  isRetrying.value = true;
};

const cancelRetry = () => {
  isRetrying.value = false;
};

const canSubmit = computed(() => {
  if (!answer.value) return false;
  if (realNameRequired.value && !realName.value.trim()) return false;
  return true;
});

// watch for Auth0 state changes
watch([isLoading, isAuthenticated, idTokenClaims], ([newLoading, newAuth, newToken]) => {
  if (newLoading) return;

  if (!newAuth) {
    router.push("/");
    return;
  }

  if (newToken) {
    fetchData();
  }
}, { immediate: true });
</script>

<style scoped>
.container {
  min-height: 100vh;
  background: #f1f5f9;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
  font-family: 'Inter', sans-serif;
  color: #1e293b;
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(4px);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-card {
  background: white;
  padding: 30px;
  border-radius: 20px;
  max-width: 400px;
  width: 90%;
  text-align: center;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
  animation: modalIn 0.3s ease-out;
}

.modal-card h3 { margin-bottom: 15px; font-size: 1.25rem; }
.modal-card p { color: #64748b; margin-bottom: 25px; line-height: 1.5; }
.modal-card button { 
  width: 100%; background: #3b82f6; color: white; border: none; 
  padding: 12px; border-radius: 10px; font-weight: 600; cursor: pointer;
}

@keyframes modalIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Common Boxes */
.form-card, .rejection-box, .pending-box, .approved-box {
  background: white;
  padding: 40px;
  border-radius: 24px;
  width: 100%;
  max-width: 550px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
}

.icon { font-size: 3rem; margin-bottom: 20px; text-align: center; }

/* Rejection */
.rejection-box { border-top: 4px solid #ef4444; }
.rejection-box h3 { color: #ef4444; margin-bottom: 20px; }
.reason-container, .prev-answer-container {
  background: #f8fafc; padding: 15px; border-radius: 12px; margin-bottom: 20px;
  border: 1px solid #e2e8f0;
}
.reason-text { margin-top: 8px; color: #b91c1c; white-space: pre-wrap; }

/* Pending */
.pending-box { border-top: 4px solid #3b82f6; text-align: center; }
.pending-box h3 { color: #3b82f6; margin-bottom: 15px; }

/* Approved */
.approved-box { text-align: center; }

/* Readonly Textarea for Answer Display */
textarea[readonly] {
  width: 100%;
  background: #f1f5f9;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  padding: 12px;
  font-family: inherit;
  font-size: 0.95rem;
  resize: none;
  margin-top: 8px;
  color: #475569;
  display: block;
}

/* Form Styles */
.form-card h2 { margin-bottom: 30px; font-weight: 800; }
.question-text { font-size: 1.1rem; color: #475569; margin-bottom: 20px; line-height: 1.6; }

.input-group textarea {
  width: 100%;
  padding: 16px;
  border: 2px solid #e2e8f0;
  border-radius: 16px;
  font-size: 1rem;
  font-family: inherit;
  resize: vertical;
  transition: border-color 0.2s;
  box-sizing: border-box;
}
.input-group input {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  font-size: 1rem;
  font-family: inherit;
  transition: border-color 0.2s;
  box-sizing: border-box;
  margin-bottom: 12px;
}
.input-group input:focus { outline: none; border-color: #3b82f6; }
.input-group textarea:focus { outline: none; border-color: #3b82f6; }

.hint { font-size: 0.8rem; color: #94a3b8; margin-top: 8px; margin-bottom: 25px; }

/* Buttons */
.actions { display: flex; gap: 12px; }
button { 
  border: none; border-radius: 12px; padding: 14px 24px; font-weight: 600; 
  cursor: pointer; transition: all 0.2s;
}
.btn-primary { background: #3b82f6; color: white; flex: 1; }
.btn-primary:hover:not(:disabled) { background: #2563eb; transform: translateY(-1px); }
.btn-primary:disabled { background: #94a3b8; cursor: not-allowed; }

.btn-retry { width: 100%; background: #ef4444; color: white; }
.btn-retry:hover { background: #dc2626; }

.btn-secondary { background: #64748b; color: white; }
.btn-secondary:hover { background: #475569; }

/* Loader */
.loading-state { text-align: center; }
.loader {
  width: 40px; height: 40px; border: 3px solid #e2e8f0; border-top-color: #3b82f6;
  border-radius: 50%; animation: spin 0.8s linear infinite; margin: 0 auto 15px;
}
@keyframes spin { to { transform: rotate(360deg); } }

</style>
