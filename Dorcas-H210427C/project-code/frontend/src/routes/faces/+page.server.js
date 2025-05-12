import { redirect } from '@sveltejs/kit';


export const load = async ({ url }) => {
    const queryParams = url.searchParams;

    const page = queryParams.get('tokenid');
    if (!page) {
        throw redirect(301, '/auth/login');
    }
} 