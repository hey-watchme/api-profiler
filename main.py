from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import json
import re
from datetime import datetime
from typing import Dict, Any
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables
load_dotenv()

# Import Supabase client
from supabase_client import SupabaseClient

# Import LLM provider
from llm_providers import get_current_llm, CURRENT_PROVIDER, CURRENT_MODEL

app = FastAPI(title="Profiler API", version="1.0.0")

# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lazy initialization of Supabase client
supabase_client = None

def get_supabase_client():
    """Lazy initialize and get Supabase client"""
    global supabase_client
    if supabase_client is None:
        try:
            supabase_client = SupabaseClient()
            print("✅ Supabase client initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize Supabase client: {e}")
            raise e
    return supabase_client


class SpotProfilerRequest(BaseModel):
    """Spot profiler analysis request"""
    device_id: str
    recorded_at: str  # UTC timestamp (ISO 8601 format)


def extract_json_from_response(raw_response: str) -> Dict[str, Any]:
    """Extract JSON from LLM response"""
    content = raw_response.strip()

    try:
        # Pattern 1: Response is already JSON
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # Pattern 2: ```json ... ``` format
        json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', content, re.DOTALL)
        if json_match:
            json_content = json_match.group(1).strip()
            return json.loads(json_content)

        # Pattern 3: Extract first {...} block
        json_block_match = re.search(r'({.*})', content, re.DOTALL)
        if json_block_match:
            json_content = json_block_match.group(1).strip()
            return json.loads(json_content)

        # No pattern matched
        raise ValueError("Failed to extract JSON data")

    except (json.JSONDecodeError, ValueError) as e:
        # Fallback on JSON parsing failure
        return {
            "processing_error": f"JSON parsing error: {str(e)}",
            "raw_response": raw_response,
            "extracted_content": content[:500] + "..." if len(content) > 500 else content
        }


async def call_llm_with_retry(prompt: str) -> Dict[str, Any]:
    """Call LLM with retry functionality (provider abstraction)"""
    try:
        # Get current LLM provider
        llm = get_current_llm()

        # LLM call (retry functionality is applied by each provider)
        raw_response = llm.generate(prompt)

        # Extract JSON
        extracted_data = extract_json_from_response(raw_response)

        return extracted_data

    except Exception as e:
        print(f"LLM API call error: {e}")
        raise


@app.get("/")
async def root():
    return {"message": "Profiler API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "llm_provider": CURRENT_PROVIDER,
        "llm_model": CURRENT_MODEL
    }


@app.post("/spot-profiler")
async def spot_profiler(request: SpotProfilerRequest):
    """
    Spot profiler: Analyze a single recording and save to spot_results table

    Flow:
    1. Fetch prompt from spot_aggregators table
    2. Execute LLM analysis
    3. Save result to spot_results table
    """
    try:
        print(f"\n🔍 Spot profiler analysis started")
        print(f"  - Device ID: {request.device_id}")
        print(f"  - Recorded At: {request.recorded_at}")

        # Get Supabase client
        supabase = get_supabase_client()

        # Fetch prompt from spot_aggregators table
        print("📥 Fetching prompt from spot_aggregators table...")
        try:
            result = supabase.client.table('spot_aggregators').select('prompt').eq('device_id', request.device_id).eq('recorded_at', request.recorded_at).execute()

            if not result.data or len(result.data) == 0:
                raise HTTPException(
                    status_code=404,
                    detail=f"No data found in spot_aggregators: device_id={request.device_id}, recorded_at={request.recorded_at}"
                )

            prompt = result.data[0].get('prompt')
            if not prompt:
                raise HTTPException(
                    status_code=404,
                    detail=f"prompt field is empty: device_id={request.device_id}, recorded_at={request.recorded_at}"
                )

            print(f"  ✅ Prompt fetched successfully: {len(prompt)} chars")
        except HTTPException:
            raise
        except Exception as e:
            print(f"❌ Failed to fetch prompt: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Prompt fetch error: {str(e)}"
            )

        # LLM processing (provider abstraction)
        print(f"📤 Sending to LLM... ({CURRENT_PROVIDER}/{CURRENT_MODEL})")
        analysis_result = await call_llm_with_retry(prompt)
        print(f"✅ LLM processing completed")

        # Display result in terminal
        print("\n" + "="*60)
        print("📊 Analysis result:")
        print("="*60)
        print(json.dumps(analysis_result, ensure_ascii=False, indent=2))
        print("="*60 + "\n")

        # Prepare data for spot_results table
        spot_results_data = {
            'device_id': request.device_id,
            'recorded_at': request.recorded_at,
            'vibe_score': analysis_result.get('vibe_score'),
            'profile_result': analysis_result,  # Save full analysis as JSONB
            'summary': analysis_result.get('summary'),  # Dashboard summary (Japanese)
            'behavior': analysis_result.get('behavior'),  # Detected behaviors (comma-separated)
            'llm_model': f"{CURRENT_PROVIDER}/{CURRENT_MODEL}"
        }

        # Save to spot_results table (UPSERT)
        print("💾 Saving to spot_results table...")
        try:
            result = supabase.client.table('spot_results').upsert(spot_results_data).execute()
            print(f"✅ Successfully saved to spot_results table")
            save_success = True
        except Exception as e:
            print(f"❌ Failed to save to spot_results table: {e}")
            save_success = False
            # Return response even if save fails

        return {
            "status": "success" if save_success else "partial_success",
            "message": "Spot profiler analysis completed" + (" (DB save successful)" if save_success else " (DB save failed)"),
            "device_id": request.device_id,
            "recorded_at": request.recorded_at,
            "analysis_result": analysis_result,
            "database_save": save_success,
            "processed_at": datetime.now().isoformat(),
            "model_used": f"{CURRENT_PROVIDER}/{CURRENT_MODEL}"
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_details = {
            "error_type": type(e).__name__,
            "error_message": str(e),
            "traceback": traceback.format_exc()
        }

        print(f"❌ ERROR in spot_profiler: {error_details}")

        raise HTTPException(
            status_code=500,
            detail={
                "message": "Error occurred during spot profiler analysis",
                "error_details": error_details
            }
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8051)
