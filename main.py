from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import httpx

# ── App Initialization ──────────────────────────────────────────────────────

app = FastAPI()

# CORS Shield: allows the frontend to query this server from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Pydantic Models ─────────────────────────────────────────────────────────

class OrderItem(BaseModel):
    estimated_cost: float = Field(alias="Estimated Cost")
    item_name: str       = Field(alias="Item_Name")
    stock: float         = Field(alias="Stock")
    supplier: str        = Field(alias="Supplier")
    units_to_order: int  = Field(alias="Units to Order")

    model_config = {"populate_by_name": True}


class AIAdvisorResponse(BaseModel):
    active_trend: str
    ai_advice: str
    items_to_order: list[OrderItem]
    live_weather: str
    status: str
    total_cost_rupees: float

# ── Routes ──────────────────────────────────────────────────────────────────

@app.post("/")
def home():
    return {"status": "Impact Engine Backend is Live"}


AI_ADVISOR_URL = "http://10.124.126.153:5000/api/ai-advisor"

@app.post("/api/inventory-advisor", response_model=AIAdvisorResponse)
async def inventory_advisor(file: UploadFile = File(...)):
    """Accept a CSV upload, forward to AI engine, validate response, and return it."""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(AI_ADVISOR_URL)
            response.raise_for_status()
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail="Cannot reach AI advisor server — connection refused.",
        )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="AI advisor server timed out.",
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"AI advisor server returned an error: {e.response.text}",
        )

    return AIAdvisorResponse(**response.json())
