from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import statistics
from typing import List, Optional
import os

app = FastAPI()

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)

# Load the latency data directly in the code
latency_data = [
    {"region": "apac", "service": "payments", "latency_ms": 189.85, "uptime_pct": 98.48, "timestamp": 20250301},
    {"region": "apac", "service": "support", "latency_ms": 117.01, "uptime_pct": 98.231, "timestamp": 20250302},
    {"region": "apac", "service": "analytics", "latency_ms": 120.56, "uptime_pct": 98.459, "timestamp": 20250303},
    {"region": "apac", "service": "recommendations", "latency_ms": 145.37, "uptime_pct": 97.19, "timestamp": 20250304},
    {"region": "apac", "service": "catalog", "latency_ms": 155.63, "uptime_pct": 98.442, "timestamp": 20250305},
    {"region": "apac", "service": "recommendations", "latency_ms": 228.24, "uptime_pct": 97.805, "timestamp": 20250306},
    {"region": "apac", "service": "analytics", "latency_ms": 114.3, "uptime_pct": 97.446, "timestamp": 20250307},
    {"region": "apac", "service": "analytics", "latency_ms": 146.54, "uptime_pct": 98.762, "timestamp": 20250308},
    {"region": "apac", "service": "checkout", "latency_ms": 199.88, "uptime_pct": 97.374, "timestamp": 20250309},
    {"region": "apac", "service": "checkout", "latency_ms": 125.43, "uptime_pct": 99.156, "timestamp": 20250310},
    {"region": "apac", "service": "recommendations", "latency_ms": 176.31, "uptime_pct": 97.866, "timestamp": 20250311},
    {"region": "apac", "service": "checkout", "latency_ms": 195.77, "uptime_pct": 98.647, "timestamp": 20250312},
    {"region": "emea", "service": "recommendations", "latency_ms": 162.42, "uptime_pct": 97.938, "timestamp": 20250301},
    {"region": "emea", "service": "payments", "latency_ms": 117.31, "uptime_pct": 98.841, "timestamp": 20250302},
    {"region": "emea", "service": "support", "latency_ms": 134.21, "uptime_pct": 97.999, "timestamp": 20250303},
    {"region": "emea", "service": "support", "latency_ms": 196.43, "uptime_pct": 97.755, "timestamp": 20250304},
    {"region": "emea", "service": "support", "latency_ms": 203.47, "uptime_pct": 97.19, "timestamp": 20250305},
    {"region": "emea", "service": "support", "latency_ms": 198, "uptime_pct": 98.136, "timestamp": 20250306},
    {"region": "emea", "service": "support", "latency_ms": 173.69, "uptime_pct": 99.192, "timestamp": 20250307},
    {"region": "emea", "service": "recommendations", "latency_ms": 192.12, "uptime_pct": 99.021, "timestamp": 20250308},
    {"region": "emea", "service": "analytics", "latency_ms": 224.93, "uptime_pct": 97.957, "timestamp": 20250309},
    {"region": "emea", "service": "support", "latency_ms": 133.04, "uptime_pct": 98.545, "timestamp": 20250310},
    {"region": "emea", "service": "catalog", "latency_ms": 196.7, "uptime_pct": 98.59, "timestamp": 20250311},
    {"region": "emea", "service": "payments", "latency_ms": 134.58, "uptime_pct": 97.803, "timestamp": 20250312},
    {"region": "amer", "service": "support", "latency_ms": 209.32, "uptime_pct": 97.293, "timestamp": 20250301},
    {"region": "amer", "service": "catalog", "latency_ms": 173.12, "uptime_pct": 98.23, "timestamp": 20250302},
    {"region": "amer", "service": "checkout", "latency_ms": 170.38, "uptime_pct": 98.811, "timestamp": 20250303},
    {"region": "amer", "service": "catalog", "latency_ms": 131.58, "uptime_pct": 97.289, "timestamp": 20250304},
    {"region": "amer", "service": "payments", "latency_ms": 226.62, "uptime_pct": 98.727, "timestamp": 20250305},
    {"region": "amer", "service": "catalog", "latency_ms": 174.34, "uptime_pct": 98.796, "timestamp": 20250306},
    {"region": "amer", "service": "payments", "latency_ms": 156.72, "uptime_pct": 99.117, "timestamp": 20250307},
    {"region": "amer", "service": "analytics", "latency_ms": 145.67, "uptime_pct": 97.761, "timestamp": 20250308},
    {"region": "amer", "service": "analytics", "latency_ms": 151.42, "uptime_pct": 98.986, "timestamp": 20250309},
    {"region": "amer", "service": "analytics", "latency_ms": 174.97, "uptime_pct": 99.076, "timestamp": 20250310},
    {"region": "amer", "service": "checkout", "latency_ms": 123.63, "uptime_pct": 98.078, "timestamp": 20250311},
    {"region": "amer", "service": "payments", "latency_ms": 110.13, "uptime_pct": 98.57, "timestamp": 20250312}
]

class RegionRequest(BaseModel):
    regions: List[str]
    threshold_ms: float

def calculate_percentile(data, percentile):
    """Calculate the specified percentile of a dataset"""
    if not data:
        return 0
    
    sorted_data = sorted(data)
    index = (percentile / 100) * (len(sorted_data) - 1)
    
    if index.is_integer():
        return sorted_data[int(index)]
    else:
        lower_index = int(index)
        upper_index = lower_index + 1
        weight = index - lower_index
        return sorted_data[lower_index] * (1 - weight) + sorted_data[upper_index] * weight

@app.post("/analyze-latency")
async def analyze_latency(request: RegionRequest):
    try:
        results = []
        
        for region in request.regions:
            # Filter data for the current region
            region_data = [item for item in latency_data if item['region'] == region]
            
            if not region_data:
                results.append({
                    "region": region,
                    "avg_latency": 0,
                    "p95_latency": 0,
                    "avg_uptime": 0,
                    "breaches": 0
                })
                continue
            
            # Extract latencies and uptimes
            latencies = [item['latency_ms'] for item in region_data]
            uptimes = [item['uptime_pct'] for item in region_data]
            
            # Calculate metrics
            avg_latency = statistics.mean(latencies)
            p95_latency = calculate_percentile(latencies, 95)
            avg_uptime = statistics.mean(uptimes)
            breaches = sum(1 for latency in latencies if latency > request.threshold_ms)
            
            results.append({
                "region": region,
                "avg_latency": round(avg_latency, 2),
                "p95_latency": round(p95_latency, 2),
                "avg_uptime": round(avg_uptime, 3),
                "breaches": breaches
            })
        
        return results
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/analyze-latency/")
async def analyze_latency_with_trailing_slash(request: RegionRequest):
    """Alternative endpoint with trailing slash"""
    return await analyze_latency(request)

@app.get("/")
async def root():
    return {"message": "Latency Analysis API is running", "endpoint": "POST /analyze-latency"}

# Handler for Vercel
async def app(request):
    return app
