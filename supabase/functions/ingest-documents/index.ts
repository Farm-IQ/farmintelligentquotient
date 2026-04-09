import "jsr:@supabase/functions-js/edge-runtime.d.ts"
import { createClient } from "jsr:@supabase/supabase-js@2"

interface ErrorResponse {
  success: false;
  error: string;
  code?: string;
}

interface SuccessResponse {
  success: true;
  data?: any;
  message?: string;
}

function getCORSHeaders() {
  return {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
    "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
    "Content-Type": "application/json",
  };
}

Deno.serve(async (req) => {
  // Handle CORS
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: getCORSHeaders() });
  }

  try {
    const supabaseUrl = Deno.env.get("SUPABASE_URL") || "";
    const supabaseKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") || "";

    if (!supabaseUrl || !supabaseKey) {
      return new Response(
        JSON.stringify({ success: false, error: "Missing Supabase credentials" } as ErrorResponse),
        { status: 500, headers: getCORSHeaders() }
      );
    }

    const supabase = createClient(supabaseUrl, supabaseKey);

    const { method } = req;

    if (method === "POST") {
      // Ingest new document
      const {
        fileName,
        filePath,
        fileSize,
        fileType,
        sourceType,
        uploadSource,
        extractedText,
        pageCount,
        metadata,
      } = await req.json();

      const { data, error } = await supabase
        .from("documents")
        .insert([
          {
            file_name: fileName,
            file_path: filePath,
            file_size: fileSize,
            file_type: fileType,
            source_type: sourceType || "pdf",
            upload_source: uploadSource || "direct",
            extracted_text: extractedText,
            page_count: pageCount,
            metadata: metadata || {},
            processing_status: "completed",
            is_indexed: false,
          },
        ])
        .select();

      if (error) {
        return new Response(
          JSON.stringify({ success: false, error: error.message } as ErrorResponse),
          { status: 400, headers: getCORSHeaders() }
        );
      }

      return new Response(
        JSON.stringify({
          success: true,
          data: data,
          message: "Document ingested successfully",
        } as SuccessResponse),
        { status: 201, headers: getCORSHeaders() }
      );
    } else if (method === "GET") {
      // Get documents
      const { data, error } = await supabase
        .from("documents")
        .select("*")
        .order("created_at", { ascending: false });

      if (error) {
        return new Response(
          JSON.stringify({ success: false, error: error.message } as ErrorResponse),
          { status: 400, headers: getCORSHeaders() }
        );
      }

      return new Response(
        JSON.stringify({ success: true, data, message: "Documents retrieved" } as SuccessResponse),
        { status: 200, headers: getCORSHeaders() }
      );
    }

    return new Response(
      JSON.stringify({ success: false, error: "Method not allowed" } as ErrorResponse),
      { status: 405, headers: getCORSHeaders() }
    );
  } catch (error) {
    console.error("Function error:", error);
    return new Response(
      JSON.stringify({
        success: false,
        error: error instanceof Error ? error.message : "Unknown error",
      } as ErrorResponse),
      { status: 500, headers: getCORSHeaders() }
    );
  }
});
