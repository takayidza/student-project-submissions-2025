<script>
    import Container from "$lib/components/Container.svelte";
    import { enhance } from "$app/forms";
    import * as Card from "$lib/components/ui/card/index";
    import * as Form from "$lib/components/ui/form/index";
    import { Button } from "$lib/components/ui/button/index";
    import { Input } from "$lib/components/ui/input/index";
    import { Label } from "$lib/components/ui/label/index";
    
    let username = $state("");
    let password = $state("");
    let isLoading = $state(false);

    function handleLogin({ formElement, action, cancel }) {
        isLoading = true;

        return async ({ result, update }) => {
            isLoading = false;
            await update();
        };
    }
</script>

<svelte:head>
    <title>Login</title>
</svelte:head>

<Container maxWidth="sm" padding="py-20 px-4" style="background: url('/bg.jpg'); background-size: cover; background-repeat: no-repeat;">
    <Card.Root class="w-full max-w-md mx-auto">
        <Card.Header>
            <Card.Title class="text-2xl text-center">Login</Card.Title>
        </Card.Header>
        <Card.Content>
            <form class="space-y-6" method="post" use:enhance={handleLogin} action="?/login">
                <div class="space-y-2">
                    <Label for="username">Username</Label>
                    <Input
                        type="text"
                        id="username"
                        bind:value={username}
                        name="username"
                        placeholder="Enter your username"
                        required
                        disabled={isLoading}
                    />
                </div>
                <div class="space-y-2">
                    <Label for="password">Password</Label>
                    <Input
                        type="password"
                        id="password"
                        bind:value={password}
                        name="password"
                        placeholder="Enter your password"
                        required
                        disabled={isLoading}
                    />
                </div>
                <Button type="submit" class="w-full" disabled={isLoading}>
                    {#if isLoading}
                        <svg
                            class="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                            xmlns="http://www.w3.org/2000/svg"
                            fill="none"
                            viewBox="0 0 24 24"
                        >
                            <circle
                                class="opacity-25"
                                cx="12"
                                cy="12"
                                r="10"
                                stroke="currentColor"
                                stroke-width="4"
                            ></circle>
                            <path
                                class="opacity-75"
                                fill="currentColor"
                                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                            ></path>
                        </svg>
                        Logging in...
                    {:else}
                        Login
                    {/if}
                </Button>
                <div class="text-center text-sm text-muted-foreground space-x-2">
                    <a
                        href="/forgot-password"
                        class="hover:text-primary underline-offset-4 hover:underline"
                    >
                        Forgot password?
                    </a>
                    <span>|</span>
                    <a
                        href="/auth/register"
                        class="hover:text-primary underline-offset-4 hover:underline"
                    >
                        Register
                    </a>
                </div>
            </form>
        </Card.Content>
    </Card.Root>
</Container>