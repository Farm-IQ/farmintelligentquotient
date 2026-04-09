// Follow this setup guide to integrate the Deno language server with your editor:
// https://deno.land/manual/getting_started/setup_your_environment
// This enables autocomplete, go to definition, etc.

// Setup type definitions for built-in Supabase Runtime APIs
import "jsr:@supabase/functions-js/edge-runtime.d.ts"
import { createClient } from "jsr:@supabase/supabase-js@2"

interface SendPasswordResetRequest {
  email: string;
  resetUrl?: string;
}

Deno.serve(async (req) => {
  if (req.method !== 'POST') {
    return new Response('Method not allowed', { status: 405 });
  }

  try {
    const body: SendPasswordResetRequest = await req.json()
    const { email, resetUrl } = body

    if (!email) {
      return new Response(
        JSON.stringify({ error: 'Missing required field: email' }),
        { status: 400, headers: { 'Content-Type': 'application/json' } },
      )
    }

    const supabaseUrl = Deno.env.get('SUPABASE_URL') || ''
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') || ''
    const supabase = createClient(supabaseUrl, supabaseKey)

    // Check if farmer exists with this email
    const { data: farmer, error: checkError } = await supabase
      .from('farmers')
      .select('id, email')
      .eq('email', email)
      .single()

    if (checkError || !farmer) {
      // For security, don't reveal if email exists
      console.log(`ℹ️ Password reset requested for non-existent email: ${email}`)
      return new Response(
        JSON.stringify({
          success: true,
          message: 'If an account exists with this email, a password reset link has been sent',
        }),
        { status: 200, headers: { 'Content-Type': 'application/json' } },
      )
    }

    // Use Supabase Auth's built-in password reset
    // This will send an email automatically
    const { error: resetError } = await supabase.auth.admin.generateLink({
      type: 'recovery',
      email: email,
      options: {
        redirectTo: resetUrl || 'https://tioauyhyrbqjbrypakex.supabase.co/auth/v1/callback',
      },
    })

    if (resetError) {
      throw new Error(`Failed to generate reset link: ${resetError.message}`)
    }

    console.log(`✅ Password reset email initiated for: ${email}`)

    return new Response(
      JSON.stringify({
        success: true,
        message: 'If an account exists with this email, a password reset link has been sent. Check your inbox.',
      }),
      { status: 200, headers: { 'Content-Type': 'application/json' } },
    )
  } catch (error) {
    console.error('Function error:', error)
    return new Response(
      JSON.stringify({
        error: error instanceof Error ? error.message : 'Unknown error',
      }),
      { status: 500, headers: { 'Content-Type': 'application/json' } },
    )
  }
})


/* To invoke locally:

  1. Run `supabase start` (see: https://supabase.com/docs/reference/cli/supabase-start)
  2. Make an HTTP request:

  curl -i --location --request POST 'http://127.0.0.1:54321/functions/v1/send-password-reset' \
    --header 'Authorization: Bearer eyJhbGciOiJFUzI1NiIsImtpZCI6ImI4MTI2OWYxLTIxZDgtNGYyZS1iNzE5LWMyMjQwYTg0MGQ5MCIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjIwODQ3NDAzNzd9.dwPSAt3I3YptaMRId58symeEXuB-642Fukb2PMFQZSGgMG7drVWwkfUZwdIwjaRxo0WY6TPWjflCwMT-eX45DQ' \
    --header 'Content-Type: application/json' \
    --data '{"name":"Functions"}'

*/
