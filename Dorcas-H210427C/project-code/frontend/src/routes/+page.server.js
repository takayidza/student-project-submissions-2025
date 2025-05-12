// src/routes/+page.server.js
import { redirect } from "@sveltejs/kit";

export const load = async ({ locals, url, cookies }) => {
    // Check for tokenid in URL
    const tokenId = url.searchParams.get('tokenid');
    
    // If we have a token ID in the URL but no user in locals,
    // try to use the token as a session
    if (tokenId && !locals.user) {
        try {
            // Set as temporary session and reload
            cookies.set('session', tokenId, { 
                path: '/',
                httpOnly: true,
                sameSite: 'strict',
                secure: process.env.NODE_ENV === 'production',
                maxAge: 60 * 60 * 24 // 1 day
            });
            
            // No need to redirect, we'll just pass the token to the client
        } catch (error) {
            console.error("Error setting token as session:", error);
        }
    }
    
    // If no user is logged in and no token, redirect to login
    if (!locals.user && !tokenId) {
        throw redirect(301, '/auth/login');
    }
    
    // Check if already verified
    const faceVerified = cookies.get('face_verified');
    if (faceVerified === 'true' && locals.user) {
        // User is verified, redirect to dashboard
        throw redirect(302, '/dashboard');
    }
    
    // Return user data and token for the component
    return {
        user: locals.user,
        tokenId: tokenId || (locals.user ? locals.user.id : null)
    };
};

export const actions = {
    setVerified: async ({ cookies, request }) => {
      try {
        console.log("Setting face_verified cookie");
        
        // Set the face verification cookie
        cookies.set('face_verified', 'true', {
          path: '/',
          httpOnly: true,
          sameSite: 'strict',
          secure: process.env.NODE_ENV === 'production',
          maxAge: 60 * 60 * 24 // 24 hours in seconds
        });
        
        // Verify the cookie was set
        const cookieValue = cookies.get('face_verified');
        console.log("Verification cookie set:", cookieValue);
        
        return { 
          success: true,
          message: "Face verification successful",
          data: JSON.stringify([cookieValue, true])
        };
      } catch (error) {
        console.error('Error setting verification cookie:', error);
        return { 
          success: false, 
          error: 'Failed to set verification',
          data: JSON.stringify([null, error.message])
        };
      }
    }
};