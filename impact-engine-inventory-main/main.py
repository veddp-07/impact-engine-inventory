from fastapi import FastAPI, HTTPException, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
import httpx

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class OrderItem(BaseModel):
    estimated_cost: float = Field(alias="Estimated Cost")
    item_name: str       = Field(alias="Item_Name")
    stock: float         = Field(alias="Stock")
    supplier: str        = Field(alias="Supplier")
    units_to_order: int  = Field(alias="Units to Order")
    model_config = {"populate_by_name": True}

# 🛠️ FIX: Making these fields Optional stops Validation Errors from crashing the server
class AIAdvisorResponse(BaseModel):
    status: Optional[str] = "Unknown"
    ai_advice: Optional[str] = "No advice generated."
    active_trend: Optional[str] = None
    items_to_order: Optional[List[OrderItem]] = []
    live_weather: Optional[str] = None
    total_cost_rupees: Optional[float] = 0.0

AI_ADVISOR_URL = "http://127.0.0.1:5000/api/ai-advisor"

@app.post("/api/ai-advisor", response_model=AIAdvisorResponse)
async def inventory_advisor(
    file: Optional[UploadFile] = File(None),
    trend: str = Query("General Daily Sales")
):
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(f"{AI_ADVISOR_URL}?trend={trend}")
            response.raise_for_status()
            
            data = response.json()
            
            # If Flask returned an error internally, catch it and tell the frontend
            if "error" in data:
                raise HTTPException(status_code=500, detail=data["error"])
                
            return AIAdvisorResponse(**data)
            
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Cannot reach Flask server. Is it running on port 5000?")