const { createApp, ref } = Vue;
const api = createAuthenticatedApi()
createApp({
    setup() {
        // State variables using ref

        const regForm = ref({
            serviceType: '',
            serviceName: '',
            incidentType: '',
            city: '',
            address: '',
            province: '',
            contactNumber: '',
            password: '',
            email: ''
        });
        const showPassword = ref(false);

        // Methods
        const handleRegistration = async () => {
            try {
                // Log form data
                const response = await api.post("/api/v1/add/responder", regForm.value)
                print(response.data)
                if(response.data.status){
                    alert('Emergency service registered successfully!');
                    window.location.href = "login.html"
                } else {
                    alert("Faild to add responder")
                    return
                }
            } catch (error) {
                console.error('Registration failed:', error);
                alert('Registration failed. Please try again:',error.message);
            }
        };

        const backToLogin = () => {
            window.location.href = "login.html";
        };

        const togglePassword = () => {
            showPassword.value = !showPassword.value;
        };

        // Return reactive variables and methods
        return {
            regForm,
            showPassword,
            handleRegistration,
            togglePassword,
            backToLogin
        };
    }
}).mount('#app');