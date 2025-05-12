// src/routes/dashboard/+layout.server.js
import { redirect } from '@sveltejs/kit';

export async function load({ locals, cookies, url }) {
    // Get user info from locals (populated by hooks.server.js)
    const user = locals?.user;
    
    // Ensure verification status
    const faceVerified = cookies.get('face_verified');
    
    // If no user data is available, redirect to login
    if (!user) {
        console.warn('No user found in dashboard layout. Redirecting to login.');
        throw redirect(302, '/auth/login');
    }
    
    // If user is not face verified, redirect to verification
    if (faceVerified !== 'true') {
        console.warn('User not face verified. Redirecting to verification.');
        const sessionToken = cookies.get('session');
        throw redirect(302, `/?tokenid=${sessionToken}`);
    }
    
    // Log successful dashboard access
    console.log(`User ${user.username} accessing ${url.pathname}`);
    
    // Return user data for all dashboard routes
    return {
        userId: user.id,
        user: {
            id: user.id,
            username: user.username,
            phone: user.phone
        }
    };
}