// auth-config.js

const createAuthenticatedApi = () => {
    const api = axios.create({
        baseURL: 'http://localhost:8080',  // Change this line to match backend CORS config
        headers: {
            'Content-Type': 'application/json'
        }
    });
    
    // Add token to requests if authenticated
    api.interceptors.request.use(config => {
        const token = localStorage.getItem('token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    });

    // Add response interceptor to handle 401 errors
    // api.interceptors.response.use(
    //     response => response,
    //     error => {
    //         if (error.response && error.response.status === 401) {
    //             // Clear token and redirect to login
    //             localStorage.removeItem('token');
    //             window.location.href = '/'; // Adjust path as needed
    //         }
    //         return Promise.reject(error);
    //     }
    // );
    
    return api;
};

// const checkApplicationDataBaseState = async () => {
//     // Checking application status
//     // Mainly checking for database connection issues 
//     const status = await api.get('/status');
//     return status.data;
// }

// Shared auth state management
const authState = {
    checkAuth() {
        return !!localStorage.getItem('token');
    },
    
    getToken() {
        return localStorage.getItem('token');
    },
    
    setToken(token) {
        if (token) {
            localStorage.setItem('token', token);
            localStorage.setItem('isAuthenticated', true)
        } else {
            localStorage.removeItem('token');
        }
    },

    getState(){
        if(localStorage.getItem('isAuthenticated')){
            return true

        } else {
            return false
        }
    },

    setPage(id) {

        if (id) {

            localStorage.setItem('pageId', id);
        } else {
            localStorage.removeItem('pageId');
        }
    },

    getPage() {

        return localStorage.getItem('pageId')
    },
    
    logout() {
        localStorage.removeItem('token');
        window.location.href = '/'; // Adjust path as needed
    }
};