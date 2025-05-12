// src/hooks.server.js
export async function handle({ event, resolve }) {
    const { cookies, url } = event;
    const sessionToken = cookies.get('session');
    const faceVerified = cookies.get('face_verified');
    
    // Define route protection rules
    const isAuthRoute = url.pathname.startsWith('/auth');
    const isFacesRoute = url.pathname.startsWith('/faces');
    const isDashboardRoute = url.pathname.startsWith('/dashboard');
    const isRootRoute = url.pathname === '/';
    
    // Configure which routes need protection
    const protectedRoute = !isAuthRoute && !isFacesRoute;
    
    // Set initial user state to null
    event.locals.user = null;
    
    // Process authentication
    if (sessionToken) {
        try {
            // Fetch user data from API using session token
            const apiUrl = import.meta.env.VITE_PUBLIC_API_URL;
            const response = await fetch(`${apiUrl}/users/me`, {
                headers: {
                    Authorization: `Bearer ${sessionToken}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                // Parse user data and store in locals
                const userData = await response.json();
                event.locals.user = {
                    id: userData.id,
                    username: userData.username,
                    phone: userData.phone
                };
                
                // Handle redirects based on authentication state
                if (isRootRoute && faceVerified === 'true') {
                    // If at root and already verified, go to dashboard
                    console.log('User verified, redirecting to dashboard');
                    return Response.redirect(`${url.origin}/dashboard`);
                }
                
                if (isDashboardRoute && faceVerified !== 'true') {
                    // If trying to access dashboard but not verified,
                    // redirect to face verification with token
                    console.log('User not verified, redirecting to verification');
                    return Response.redirect(`${url.origin}/?tokenid=${sessionToken}`);
                }
            } else {
                // Invalid session, clear cookies and redirect if needed
                console.error('Invalid session status:', response.status);
                cookies.delete('session', { path: '/' });
                cookies.delete('face_verified', { path: '/' });
                
                if (protectedRoute) {
                    return Response.redirect(`${url.origin}/auth/login`);
                }
            }
        } catch (error) {
            // Handle errors in session validation
            console.error('Session validation error:', error);
            cookies.delete('session', { path: '/' });
            cookies.delete('face_verified', { path: '/' });
            
            if (protectedRoute) {
                return Response.redirect(`${url.origin}/auth/login`);
            }
        }
    } else if (protectedRoute) {
        // No session token and trying to access protected route
        console.log('No session, redirecting to login from', url.pathname);
        return Response.redirect(`${url.origin}/auth/login`);
    }
    
    // Process the request and return response
    return await resolve(event);
}