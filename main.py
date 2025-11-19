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


class DailyProfilerRequest(BaseModel):
    """Daily profiler analysis request"""
    device_id: str
    local_date: str  # YYYY-MM-DD format


class WeeklyProfilerRequest(BaseModel):
    """Weekly profiler analysis request"""
    device_id: str
    week_start_date: str  # YYYY-MM-DD format (Monday)


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

        # Fetch prompt, local_date, and local_time from spot_aggregators table
        print("📥 Fetching prompt from spot_aggregators table...")
        try:
            result = supabase.client.table('spot_aggregators').select('prompt, local_date, local_time').eq('device_id', request.device_id).eq('recorded_at', request.recorded_at).execute()

            if not result.data or len(result.data) == 0:
                raise HTTPException(
                    status_code=404,
                    detail=f"No data found in spot_aggregators: device_id={request.device_id}, recorded_at={request.recorded_at}"
                )

            prompt = result.data[0].get('prompt')
            local_date = result.data[0].get('local_date')
            local_time = result.data[0].get('local_time')

            if not prompt:
                raise HTTPException(
                    status_code=404,
                    detail=f"prompt field is empty: device_id={request.device_id}, recorded_at={request.recorded_at}"
                )

            print(f"  ✅ Prompt fetched successfully: {len(prompt)} chars")
            print(f"  ✅ Local date: {local_date}")
            print(f"  ✅ Local time: {local_time}")
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

        # Add local_date and local_time if available
        if local_date:
            spot_results_data['local_date'] = local_date
        if local_time:
            spot_results_data['local_time'] = local_time

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

        # Update spot_aggregators.profiler_status to 'completed'
        try:
            supabase.client.table('spot_aggregators').update({
                'profiler_status': 'completed',
                'profiler_processed_at': datetime.now().isoformat()
            }).eq('device_id', request.device_id).eq('recorded_at', request.recorded_at).execute()
            print(f"✅ Updated spot_aggregators.profiler_status to 'completed' for {request.device_id}/{request.recorded_at}")
        except Exception as update_error:
            print(f"⚠️ Warning: Failed to update spot_aggregators.profiler_status: {update_error}")
            # Continue execution even if status update fails

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

        # Determine error type for database
        error_type_str = type(e).__name__
        if 'RateLimitError' in error_type_str or 'rate_limit' in str(e).lower():
            profiler_status = 'rate_limited'
            error_type_db = 'rate_limit'
        elif 'TimeoutError' in error_type_str or 'timeout' in str(e).lower():
            profiler_status = 'failed'
            error_type_db = 'timeout'
        else:
            profiler_status = 'failed'
            error_type_db = error_type_str

        # Update spot_aggregators with error information
        try:
            supabase = get_supabase_client()
            supabase.client.table('spot_aggregators').update({
                'profiler_status': profiler_status,
                'profiler_error_type': error_type_db,
                'profiler_error_message': str(e)[:500],  # Limit to 500 chars
                'profiler_processed_at': datetime.now().isoformat()
            }).eq('device_id', request.device_id).eq('recorded_at', request.recorded_at).execute()
            print(f"✅ Updated spot_aggregators with error info: {profiler_status}/{error_type_db}")
        except Exception as update_error:
            print(f"⚠️ Warning: Failed to update spot_aggregators error info: {update_error}")

        raise HTTPException(
            status_code=500,
            detail={
                "message": "Error occurred during spot profiler analysis",
                "error_details": error_details
            }
        )


@app.post("/daily-profiler")
async def daily_profiler(request: DailyProfilerRequest):
    """
    Daily profiler: Analyze daily aggregated data and save to daily_results table

    Flow:
    1. Fetch prompt from daily_aggregators table
    2. Execute LLM analysis
    3. Save result to daily_results table
    """
    try:
        print(f"\n📅 Daily profiler analysis started")
        print(f"  - Device ID: {request.device_id}")
        print(f"  - Local Date: {request.local_date}")

        # Get Supabase client
        supabase = get_supabase_client()

        # Fetch prompt from daily_aggregators table
        print("📥 Fetching prompt from daily_aggregators table...")
        try:
            result = supabase.client.table('daily_aggregators').select('prompt').eq('device_id', request.device_id).eq('local_date', request.local_date).execute()

            if not result.data or len(result.data) == 0:
                raise HTTPException(
                    status_code=404,
                    detail=f"No data found in daily_aggregators: device_id={request.device_id}, local_date={request.local_date}"
                )

            prompt = result.data[0].get('prompt')

            if not prompt:
                raise HTTPException(
                    status_code=404,
                    detail=f"prompt field is empty: device_id={request.device_id}, local_date={request.local_date}"
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
        print("📊 Daily analysis result:")
        print("="*60)
        print(json.dumps(analysis_result, ensure_ascii=False, indent=2))
        print("="*60 + "\n")

        # Fetch spot_results to generate vibe_scores array
        print("📥 Fetching spot_results for vibe_scores array...")
        try:
            spot_results_response = supabase.client.table('spot_results').select(
                'recorded_at, local_time, vibe_score'
            ).eq(
                'device_id', request.device_id
            ).eq(
                'local_date', request.local_date
            ).order('recorded_at').execute()

            vibe_scores_array = []
            vibe_scores_for_avg = []
            if spot_results_response.data:
                for spot in spot_results_response.data:
                    local_time = spot.get('local_time')
                    vibe_score = spot.get('vibe_score')

                    if local_time and vibe_score is not None:
                        # Extract HH:MM from local_time (YYYY-MM-DD HH:MM:SS)
                        time_str = local_time.split(' ')[1] if ' ' in local_time else local_time
                        time_parts = time_str.split(':')
                        if len(time_parts) >= 2:
                            time_hhmm = f"{time_parts[0]}:{time_parts[1]}"
                            vibe_scores_array.append({
                                "time": time_hhmm,
                                "score": vibe_score
                            })
                            vibe_scores_for_avg.append(vibe_score)

                print(f"  ✅ Generated vibe_scores array with {len(vibe_scores_array)} data points")
            else:
                print(f"  ⚠️ No spot_results found for vibe_scores generation")
        except Exception as e:
            print(f"❌ Failed to fetch spot_results: {e}")
            vibe_scores_array = []
            vibe_scores_for_avg = []

        # Calculate average vibe score
        avg_vibe = sum(vibe_scores_for_avg) / len(vibe_scores_for_avg) if vibe_scores_for_avg else 0

        # Prepare data for daily_results table
        daily_results_data = {
            'device_id': request.device_id,
            'local_date': request.local_date,
            'vibe_score': avg_vibe,  # Calculated average
            'summary': analysis_result.get('summary'),  # LLM output (Japanese)
            'burst_events': analysis_result.get('burst_events', []),  # LLM output
            'vibe_scores': vibe_scores_array,  # Time-based vibe scores array from spot_results
            'processed_count': len(vibe_scores_array),  # Number of processed recordings
            'llm_model': f"{CURRENT_PROVIDER}/{CURRENT_MODEL}"
        }

        # Save to daily_results table (UPSERT)
        print("💾 Saving to daily_results table...")
        try:
            result = supabase.client.table('daily_results').upsert(daily_results_data).execute()
            print(f"✅ Successfully saved to daily_results table")
            save_success = True
        except Exception as e:
            print(f"❌ Failed to save to daily_results table: {e}")
            save_success = False
            # Return response even if save fails

        return {
            "status": "success" if save_success else "partial_success",
            "message": "Daily profiler analysis completed" + (" (DB save successful)" if save_success else " (DB save failed)"),
            "device_id": request.device_id,
            "local_date": request.local_date,
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

        print(f"❌ ERROR in daily_profiler: {error_details}")

        raise HTTPException(
            status_code=500,
            detail={
                "message": "Error occurred during daily profiler analysis",
                "error_details": error_details
            }
        )


@app.post("/weekly-profiler")
async def weekly_profiler(request: WeeklyProfilerRequest):
    """
    Weekly profiler: Analyze weekly aggregated data and save to weekly_results table

    Flow:
    1. Fetch prompt from weekly_aggregators table
    2. Execute LLM analysis
    3. Save result to weekly_results table
    """
    try:
        print(f"\n📅 Weekly profiler analysis started")
        print(f"  - Device ID: {request.device_id}")
        print(f"  - Week Start Date: {request.week_start_date}")

        # Get Supabase client
        supabase = get_supabase_client()

        # Fetch prompt from weekly_aggregators table
        print("📥 Fetching prompt from weekly_aggregators table...")
        try:
            result = supabase.client.table('weekly_aggregators').select('prompt, context_data').eq('device_id', request.device_id).eq('week_start_date', request.week_start_date).execute()

            if not result.data or len(result.data) == 0:
                raise HTTPException(
                    status_code=404,
                    detail=f"No data found in weekly_aggregators: device_id={request.device_id}, week_start_date={request.week_start_date}"
                )

            prompt = result.data[0].get('prompt')
            context_data = result.data[0].get('context_data', {})

            if not prompt:
                raise HTTPException(
                    status_code=404,
                    detail=f"prompt field is empty: device_id={request.device_id}, week_start_date={request.week_start_date}"
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
        print("📊 Weekly analysis result:")
        print("="*60)
        print(json.dumps(analysis_result, ensure_ascii=False, indent=2))
        print("="*60 + "\n")

        # Extract memorable events and summary from LLM result
        memorable_events = analysis_result.get('memorable_events', [])
        week_summary = analysis_result.get('week_summary', '')

        # Prepare data for weekly_results table
        weekly_results_data = {
            'device_id': request.device_id,
            'week_start_date': request.week_start_date,
            'summary': week_summary,  # LLM output (Japanese)
            'memorable_events': memorable_events,  # Top 5 memorable events (JSONB array)
            'profile_result': analysis_result,  # Full LLM output (memorable_events included)
            'processed_count': context_data.get('spot_count', 0),  # Number of recordings processed
            'llm_model': f"{CURRENT_PROVIDER}/{CURRENT_MODEL}"
        }

        # Save to weekly_results table (UPSERT)
        print("💾 Saving to weekly_results table...")
        try:
            result = supabase.client.table('weekly_results').upsert(weekly_results_data).execute()
            print(f"✅ Successfully saved to weekly_results table")
            save_success = True
        except Exception as e:
            print(f"❌ Failed to save to weekly_results table: {e}")
            save_success = False
            # Return response even if save fails

        return {
            "status": "success" if save_success else "partial_success",
            "message": "Weekly profiler analysis completed" + (" (DB save successful)" if save_success else " (DB save failed)"),
            "device_id": request.device_id,
            "week_start_date": request.week_start_date,
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

        print(f"❌ ERROR in weekly_profiler: {error_details}")

        raise HTTPException(
            status_code=500,
            detail={
                "message": "Error occurred during weekly profiler analysis",
                "error_details": error_details
            }
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8051)
