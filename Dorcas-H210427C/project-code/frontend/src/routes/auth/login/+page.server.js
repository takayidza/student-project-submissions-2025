import { fail, redirect } from "@sveltejs/kit";

export const actions = {
    login: async ({ request, cookies }) => {
        const formData = await request.formData();
        const { username, password } = Object.fromEntries(formData);
        const apiUrl = import.meta.env.VITE_PUBLIC_API_URL;

        if (!username || !password) {
            return fail(400, { message: 'All fields are required' });
        }

        const response = await fetch(`${apiUrl}/users/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();

        if (data.error) {
            return fail(400, { error: data.error });
        }

        console.log(data)
        cookies.set('session', data.id, {
            path: '/',
            httpOnly: true,
            sameSite: 'strict',
            secure: true,
            maxAge: 60 * 60 * 24 * 7 // 1 week
        });
        throw redirect(303, '/?tokenid=' + btoa(data.id.toString()));
    }
};