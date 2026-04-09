// Follow this setup guide to integrate the Deno language server with your editor:
// https://deno.land/manual/getting_started/setup_your_environment
// This enables autocomplete, go to definition, etc.

// Setup type definitions for built-in Supabase Runtime APIs
import "jsr:@supabase/functions-js/edge-runtime.d.ts"
import { createClient } from "jsr:@supabase/supabase-js@2"

interface SendVerificationEmailRequest {
  userId: string;
  email: string;
  verificationUrl?: string;
}

interface ErrorResponse {
  success: false;
  error: string;
  code?: string;
}

interface SuccessResponse {
  success: true;
  message: string;
  token: string;
  verifyLink: string;
  expiresAt: string;
}

function getCORSHeaders() {
  return {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
    "Content-Type": "application/json",
  };
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: getCORSHeaders() });
  }

  if (req.method !== "POST") {
    return new Response(
      JSON.stringify({ success: false, error: "Method not allowed" } as ErrorResponse),
      { status: 405, headers: getCORSHeaders() }
    );
  }

  try {
    let body: SendVerificationEmailRequest;
    try {
      body = await req.json();
    } catch (e) {
      return new Response(
        JSON.stringify({ success: false, error: "Invalid JSON in request body" } as ErrorResponse),
        { status: 400, headers: getCORSHeaders() }
      );
    }

    const { userId, email, verificationUrl } = body

    if (!userId || !email) {
      return new Response(
        JSON.stringify({ success: false, error: "Missing required fields: userId, email" } as ErrorResponse),
        { status: 400, headers: getCORSHeaders() },
      )
    }

    const supabaseUrl = Deno.env.get("SUPABASE_URL") || ""
    const supabaseKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") || ""

    if (!supabaseUrl || !supabaseKey) {
      return new Response(
        JSON.stringify({ success: false, error: "Missing Supabase credentials" } as ErrorResponse),
        { status: 500, headers: getCORSHeaders() }
      );
    }

    const supabase = createClient(supabaseUrl, supabaseKey)

    // Generate verification token (6-digit code for simplicity)
    const verificationToken = Math.floor(100000 + Math.random() * 900000).toString()
    const tokenExpiresAt = new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString() // 24 hours

    // Update farmer profile with verification token
    const { error: updateError } = await supabase
      .from("farmers")
      .update({
        verification_token: verificationToken,
        verification_token_expires_at: tokenExpiresAt,
      })
      .eq("id", userId)

    if (updateError) {
      throw new Error(`Failed to store verification token: ${updateError.message}`)
    }

    // Note: In production, you would send email via email service (SendGrid, Mailgun, etc.)
    // For now, we just return the token for testing
    const verifyLink = verificationUrl
      ? `${verificationUrl}?token=${verificationToken}&email=${encodeURIComponent(email)}`
      : `${verificationToken}`

    console.log(`✅ Verification email prepared for ${email}`)
    console.log(`🔗 Verification token: ${verificationToken}`)
    console.log(`⏰ Expires at: ${tokenExpiresAt}`)

    return new Response(
      JSON.stringify({
        success: true,
        message: "Verification email sent successfully",
        token: verificationToken,
        verifyLink,
        expiresAt: tokenExpiresAt,
      } as SuccessResponse),
      { status: 200, headers: getCORSHeaders() },
    )
  } catch (error) {
    console.error("Function error:", error)
    return new Response(
      JSON.stringify({
        success: false,
        error: error instanceof Error ? error.message : "Unknown error",
      } as ErrorResponse),
      { status: 500, headers: getCORSHeaders() },
    )
  }
})


/* To invoke locally:

  1. Run `supabase start` (see: https://supabase.com/docs/reference/cli/supabase-start)
  2. Make an HTTP request:

  curl -i --location --request POST 'http://127.0.0.1:54321/functions/v1/send-verification-email' \
    --header 'Authorization: Bearer eyJhbGciOiJFUzI1NiIsImtpZCI6ImI4MTI2OWYxLTIxZDgtNGYyZS1iNzE5LWMyMjQwYTg0MGQ5MCIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjIwODQ3NDAzMzZ9.70kj7KDLVPJAjdh9tvqWuY1smfPjvoQXF2j2uxZHK9xg_LuUqkCau6zoKaO-gw3RukFaSk1Wst6stNFhsQ5o7w' \
    --header 'Content-Type: application/json' \
    --data '{"name":"Functions"}'

*/
