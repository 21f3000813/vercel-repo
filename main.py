from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import statistics
from typing import List, Optional

app = FastAPI()

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

# Load the latency data
with open('q-vercel-latency.json', 'r') as f:
    latency_data = json.load(f)

class RegionRequest(BaseModel):
    regions: List[str]
    threshold_ms: float

class RegionMetrics(BaseModel):
    region: str
    avg_latency: float
    p95_latency: float
    avg_uptime: float
    breaches: int

@app.post("/analyze-latency")
async def analyze_latency(request: RegionRequest):
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

@app.get("/")
async def root():
    return {"message": "Latency Analysis API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)