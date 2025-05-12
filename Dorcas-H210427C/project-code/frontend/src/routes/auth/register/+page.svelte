<script>
    import Container from "$lib/components/Container.svelte";
    import { enhance } from "$app/forms";
    import * as Card from "$lib/components/ui/card";
    import { Button } from "$lib/components/ui/button";
    import { Input } from "$lib/components/ui/input";
    import { Label } from "$lib/components/ui/label";
    import { Alert, AlertDescription } from "$lib/components/ui/alert";
    
    let username = $state("");
    let password = $state("");
    let confirmPassword = $state("");
    let phone = $state("");
    let error = $state(null);
    let isLoading = $state(false);

    $effect(() => {
        if (password && confirmPassword && password !== confirmPassword) {
            error = "Passwords do not match";
        } else {
            error = null;
        }
    });

    function handleRegister({ formElement, action, cancel }) {
        isLoading = true;
        return async ({ result, update }) => {
            isLoading = false;
            await update();
        };
    }
</script>

<svelte:head>
    <title>Register</title>
</svelte:head>

<Container maxWidth="sm" padding="py-20 px-4" style="background: url('/bg2.jpg'); background-size: cover; background-repeat: no-repeat;">
    <Card.Root class="w-full max-w-md mx-auto">
        <Card.Header>
            <Card.Title class="text-2xl text-center">Register</Card.Title>
        </Card.Header>
        <Card.Content>
            <form class="space-y-6" method="post" use:enhance={handleRegister} action="?/register">
                {#if error}
                    <Alert variant="destructive">
                        <AlertDescription>{error}</AlertDescription>
                    </Alert>
                {/if}
                <div class="space-y-2">
                    <Label for="username">Username</Label>
                    <Input type="text" id="username" bind:value={username} name="username" placeholder="Enter your username" required disabled={isLoading} />
                </div>
                
                <div class="space-y-2">
                    <Label for="phone">Phone</Label>
                    <Input type="text" id="phone" bind:value={phone} name="phone" placeholder="Enter your phone number" required disabled={isLoading} />
                </div>
                
                <div class="space-y-2">
                    <Label for="password">Password</Label>
                    <Input type="password" id="password" bind:value={password} name="password" placeholder="Enter your password" required disabled={isLoading} />
                </div>
                
                <div class="space-y-2">
                    <Label for="confirmPassword">Confirm Password</Label>
                    <Input type="password" id="confirmPassword" bind:value={confirmPassword} name="confirmPassword" placeholder="Confirm your password" required disabled={isLoading} />
                </div>
                
                <Button type="submit" class="w-full" disabled={error || isLoading}>
                    {#if isLoading}
                        <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Registering...
                    {:else}
                        Register
                    {/if}
                </Button>
                
                <div class="text-center text-sm text-muted-foreground space-x-2">
                    <a href="/forgot-password" class="hover:text-primary underline-offset-4 hover:underline">Forgot password?</a>
                    <span>|</span>
                    <a href="/auth/login" class="hover:text-primary underline-offset-4 hover:underline">Login</a>
                </div>
            </form>
        </Card.Content>
    </Card.Root>
</Container>
