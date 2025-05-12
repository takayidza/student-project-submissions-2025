import { redirect } from "@sveltejs/kit";

export const actions = {
    default: async ({ cookies, fetch }) => {
        // Clear both session and face verification cookies
        cookies.delete('session', { 
            path: '/',
            httpOnly: true,
            sameSite: 'strict',
            secure: process.env.NODE_ENV === 'production'
        });

        cookies.delete('face_verified', { 
            path: '/',
            httpOnly: true,
            sameSite: 'strict',
            secure: process.env.NODE_ENV === 'production'
        });

        // Redirect to login page
        throw redirect(303, '/auth/login');
    }
};