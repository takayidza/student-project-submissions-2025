import { fail, redirect } from "@sveltejs/kit";


export const actions = {
    register: async ({ request }) => {
        const apiUrl = import.meta.env.VITE_PUBLIC_API_URL;
        const formData = await request.formData();
        const { username, password, confirmPassword, phone } = Object.fromEntries(formData);

        // Validate form data
        if (!username || !password || !confirmPassword || !phone) {
            return fail(400, { message: 'All fields are required' });
        }

        if (password !== confirmPassword) {
            return fail(400, { message: 'Passwords do not matchs' });
        }

        const response = await fetch(`${apiUrl}/users/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password, phone })
        });

        if (response.ok) {
            const data = await response.json();
            const { user_id } = data;

            // Encode the user ID using URL-safe Base64
            const id = btoa(user_id.toString());

            // Redirect to the faces page
            throw redirect(302, `/faces/?tokenid=${id}`);
        } else {
            const errorData = await response.json();
            return fail(response.status, {
                message: errorData.error || 'Failed to register user'
            });
        }
    }
};
