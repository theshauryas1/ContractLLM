from __future__ import annotations

from pathlib import Path

import yaml

from backend.schemas import ContractDefinition


class ContractEngine:
    def load_contracts(self, contract_path: str | Path) -> list[ContractDefinition]:
        path = Path(contract_path)
        with path.open("r", encoding="utf-8") as handle:
            raw = yaml.safe_load(handle) or {}
        return [ContractDefinition(**contract) for contract in raw.get("contracts", [])]

    def append_contract(self, contract_path: Path, contract: ContractDefinition) -> None:
        if contract_path.exists():
            with contract_path.open("r", encoding="utf-8") as handle:
                raw = yaml.safe_load(handle) or {}
        else:
            raw = {}
        raw.setdefault("contracts", []).append(contract.model_dump(mode="json"))
        with contract_path.open("w", encoding="utf-8") as handle:
            yaml.safe_dump(raw, handle, sort_keys=False)
