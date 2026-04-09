import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from "https://esm.sh/@supabase/supabase-js@2.38.0"

// Types
interface ErrorResponse {
  success: false
  error: string
  code?: string
}

interface CreditScoreRequest {
  user_id: string
  farmer_id?: string
  recalculate?: boolean
}

interface FarmIQScore {
  id: string
  fiq_score: number
  fiq_percentile?: number
  credit_risk_level: "very_low" | "low" | "medium" | "high" | "very_high"
  default_probability: number
  recommended_credit_limit_kes: number
  recommended_loan_term_months: number
  recommended_interest_rate: number
  feature_importance: Record<string, number>
  shap_values: Record<string, number>
  key_strengths: string[]
  key_weaknesses: string[]
  improvement_recommendations: string[]
  model_version: string
  approval_status: string
  score_expires_at: string
}

interface CreditScoreResponse {
  success: true
  score_result: FarmIQScore
  message: string
  calculation_time_ms: number
}

function getCORSHeaders() {
  return {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
    "Content-Type": "application/json",
  }
}

async function calculateCreditScore(
  supabase: any,
  request: CreditScoreRequest,
  userId: string
): Promise<FarmIQScore> {
  const { user_id, farmer_id, recalculate = false } = request

  console.log(`Calculating credit score for user: ${user_id}`)

  // Check for existing non-expired score
  if (!recalculate) {
    const { data: existingScore } = await supabase
      .from("farmiq_credit_profiles")
      .select("*")
      .eq("user_id", user_id)
      .gt("score_expires_at", new Date().toISOString())
      .limit(1)
      .single()

    if (existingScore) {
      console.log("Using cached credit score")
      return existingScore as FarmIQScore
    }
  }

  // Get farmer profile
  const { data: farmerProfile } = await supabase
    .from("farmer_profiles")
    .select("*")
    .eq("user_id", user_id)
    .limit(1)
    .single()

  if (!farmerProfile) {
    throw new Error("Farmer profile not found")
  }

  // Get latest training data for this farmer
  const { data: trainingData } = await supabase
    .from("farmiq_training_data")
    .select("*")
    .eq("farmer_id", farmerProfile.id)
    .order("created_at", { ascending: false })
    .limit(1)
    .single()

  // Calculate score components (simplified - in production call ML model)
  let baseScore = 50

  // Adjust based on available features
  if (trainingData) {
    if (trainingData.years_farming_experience) {
      baseScore += Math.min(trainingData.years_farming_experience * 2, 15)
    }
    if (trainingData.has_irrigation) {
      baseScore += 10
    }
    if (trainingData.in_cooperative) {
      baseScore += 8
    }
    if (trainingData.keeps_farm_records) {
      baseScore += 10
    }
    if (trainingData.previous_loans_repaid > 0) {
      baseScore += Math.min(trainingData.previous_loans_repaid * 3, 10)
    }
    if (trainingData.previous_default_count > 0) {
      baseScore -= trainingData.previous_default_count * 5
    }
  }

  baseScore = Math.max(0, Math.min(100, baseScore))

  // Calculate risk level based on score
  let riskLevel: "very_low" | "low" | "medium" | "high" | "very_high"
  let defaultProbability: number

  if (baseScore >= 85) {
    riskLevel = "very_low"
    defaultProbability = 0.05
  } else if (baseScore >= 70) {
    riskLevel = "low"
    defaultProbability = 0.12
  } else if (baseScore >= 55) {
    riskLevel = "medium"
    defaultProbability = 0.25
  } else if (baseScore >= 40) {
    riskLevel = "high"
    defaultProbability = 0.40
  } else {
    riskLevel = "very_high"
    defaultProbability = 0.60
  }

  // Calculate recommended loan amount (adjusted by risk)
  const baseCreditLimit = 50000 // KES
  const creditLimit = Math.floor(
    baseCreditLimit * (baseScore / 100) * (1 - defaultProbability)
  )

  // Determine term and interest rate
  let term = 12
  let interestRate = 8.0

  if (baseScore >= 80) {
    term = 36
    interestRate = 6.0
  } else if (baseScore >= 65) {
    term = 24
    interestRate = 7.0
  } else if (baseScore >= 50) {
    term = 12
    interestRate = 9.0
  } else {
    term = 6
    interestRate = 12.0
  }

  // Generate recommendations
  const keyStrengths: string[] = []
  const keyWeaknesses: string[] = []
  const improvements: string[] = []

  if (trainingData) {
    if (trainingData.years_farming_experience > 10) {
      keyStrengths.push("Strong farming experience")
    }
    if (trainingData.in_cooperative) {
      keyStrengths.push("Cooperative membership demonstrates commitment")
    }
    if (!trainingData.keeps_farm_records) {
      keyWeaknesses.push("Farm record-keeping needed")
      improvements.push("Start maintaining detailed farm records")
    }
    if (!trainingData.has_irrigation) {
      keyWeaknesses.push("Limited water management")
      improvements.push("Consider small-scale irrigation investment")
    }
  }

  // Prepare feature importance (dummy values for now)
  const featureImportance = {
    farming_experience: 0.25,
    land_size: 0.15,
    water_access: 0.20,
    cooperative_status: 0.15,
    record_keeping: 0.12,
    repayment_history: 0.13,
  }

  // Score expires in 90 days
  const expiresAt = new Date()
  expiresAt.setDate(expiresAt.getDate() + 90)

  // Store in database
  const { data: scoreData, error: scoreError } = await supabase
    .from("farmiq_credit_profiles")
    .upsert(
      [
        {
          user_id: user_id,
          farmer_id: farmerProfile.id,
          fiq_score: baseScore,
          credit_risk_level: riskLevel,
          default_probability: defaultProbability,
          recommended_credit_limit_kes: creditLimit,
          recommended_loan_term_months: term,
          recommended_interest_rate: interestRate,
          feature_importance: featureImportance,
          shap_values: featureImportance, // Simplified
          key_strengths: keyStrengths,
          key_weaknesses: keyWeaknesses,
          improvement_recommendations: improvements,
          model_version: "v1.0-basic",
          approval_status: "pending",
          score_expires_at: expiresAt.toISOString(),
        },
      ],
      { onConflict: "user_id" }
    )
    .select()

  if (scoreError) {
    console.error("Failed to store score:", scoreError)
  }

  return {
    id: scoreData?.[0]?.id || crypto.randomUUID(),
    fiq_score: baseScore,
    credit_risk_level: riskLevel,
    default_probability: defaultProbability,
    recommended_credit_limit_kes: creditLimit,
    recommended_loan_term_months: term,
    recommended_interest_rate: interestRate,
    feature_importance: featureImportance,
    shap_values: featureImportance,
    key_strengths: keyStrengths,
    key_weaknesses: keyWeaknesses,
    improvement_recommendations: improvements,
    model_version: "v1.0-basic",
    approval_status: "pending",
    score_expires_at: expiresAt.toISOString(),
  }
}

serve(async (req) => {
  const startTime = performance.now()

  // Handle CORS
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: getCORSHeaders() })
  }

  if (req.method !== "POST") {
    return new Response(
      JSON.stringify({
        success: false,
        error: "Method not allowed",
      } as ErrorResponse),
      { status: 405, headers: getCORSHeaders() }
    )
  }

  try {
    // Initialize Supabase
    const supabaseUrl = Deno.env.get("SUPABASE_URL") || ""
    const supabaseKey = Deno.env.get("SUPABASE_ANON_KEY") || ""

    if (!supabaseUrl || !supabaseKey) {
      return new Response(
        JSON.stringify({
          success: false,
          error: "Missing Supabase credentials",
          code: "MISSING_CREDENTIALS",
        } as ErrorResponse),
        { status: 500, headers: getCORSHeaders() }
      )
    }

    const supabase = createClient(supabaseUrl, supabaseKey)

    // Get user from auth header
    const authHeader = req.headers.get("authorization") || ""
    const token = authHeader.replace("Bearer ", "")

    if (!token) {
      return new Response(
        JSON.stringify({
          success: false,
          error: "Missing authorization token",
          code: "UNAUTHORIZED",
        } as ErrorResponse),
        { status: 401, headers: getCORSHeaders() }
      )
    }

    const {
      data: { user },
    } = await supabase.auth.getUser(token)

    if (!user) {
      return new Response(
        JSON.stringify({
          success: false,
          error: "Unauthorized",
          code: "INVALID_TOKEN",
        } as ErrorResponse),
        { status: 401, headers: getCORSHeaders() }
      )
    }

    // Parse request
    let body: CreditScoreRequest
    try {
      body = await req.json()
    } catch (e) {
      return new Response(
        JSON.stringify({
          success: false,
          error: "Invalid JSON",
          code: "INVALID_JSON",
        } as ErrorResponse),
        { status: 400, headers: getCORSHeaders() }
      )
    }

    // Calculate score
    const scoreResult = await calculateCreditScore(supabase, body, user.id)

    const processingTime = Math.round(performance.now() - startTime)

    const response: CreditScoreResponse = {
      success: true,
      score_result: scoreResult,
      message: `FarmIQ credit score calculated: ${scoreResult.fiq_score}/100 (${scoreResult.credit_risk_level} risk)`,
      calculation_time_ms: processingTime,
    }

    return new Response(JSON.stringify(response), {
      status: 200,
      headers: getCORSHeaders(),
    })
  } catch (error) {
    console.error("Credit Score Error:", error)

    const errorMessage = error instanceof Error ? error.message : "Unknown error"

    return new Response(
      JSON.stringify({
        success: false,
        error: errorMessage,
        code: "INTERNAL_ERROR",
      } as ErrorResponse),
      { status: 500, headers: getCORSHeaders() }
    )
  }
})
