from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from backend.core.contract_engine import ContractEngine
from backend.schemas import ContractCreateRequest, ContractListResponse
from backend.utils.security import require_api_key


router = APIRouter(tags=["contracts"])
engine = ContractEngine()


@router.get("/contracts", response_model=ContractListResponse)
def list_contracts(contract_path: str = "contracts/default.yaml") -> ContractListResponse:
    contracts = engine.load_contracts(contract_path)
    return ContractListResponse(contracts=contracts)


@router.post("/contracts", response_model=dict[str, str])
def create_contract(payload: ContractCreateRequest, _: None = Depends(require_api_key)) -> dict[str, str]:
    path = Path(payload.contract_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Contract file not found")
    engine.append_contract(path, payload.contract)
    return {"status": "created", "contract_id": payload.contract.id}
