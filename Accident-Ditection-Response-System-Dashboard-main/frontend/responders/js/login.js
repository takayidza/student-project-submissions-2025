const { createApp, ref } = Vue;
const api = createAuthenticatedApi();
createApp({
    setup() {
        // State variables
        const loginForm = ref({
            email: '',
            password: '',
            rememberMe: false
        }); 
        const showPassword = ref(false);
        const isLoading = ref(false);
        const error = ref(null);

        // Methods
        const togglePasswordVisibility = () => {
            showPassword.value = !showPassword.value;
        };

        const handleLogin = async () => {
            isLoading.value = true;
            error.value = null;

            try {
                // Simulate API call
                const response = await api.post("/api/v1/login", loginForm.value)

                if (response.data.token) {
                    authState.setToken(response.data.token);                
                    window.location.href = '/responders';
                } else {
                    error.value = 'Invalid credentials';
                    return 
                }
            } catch (e) {
                error.value = e.message || 'Login failed';
            } finally {
                isLoading.value = false;
            }
        };

        const handleRegister = async () => {

            window.location.href = '/responders/provider-reg.html';
        }

        // Return reactive variables and methods
        return {
            loginForm,
            showPassword,
            isLoading,
            error,
            togglePasswordVisibility,
            handleLogin,
            handleRegister
        };
    }
}).mount('#app');