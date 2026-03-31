from backend.schemas import EvaluationResult, RepairSuggestion, TracePayload


class RepairEngine:
    def suggest_repairs(self, trace: TracePayload, results: list[EvaluationResult]) -> list[RepairSuggestion]:
        suggestions: list[RepairSuggestion] = []
        for result in results:
            if result.status != "fail":
                continue
            if result.contract == "context_faithfulness":
                suggestions.append(
                    RepairSuggestion(
                        contract=result.contract,
                        strategy="add_context",
                        prompt_patch="Cite only facts grounded in the provided context and state uncertainty explicitly.",
                    )
                )
            elif result.contract == "response_format":
                suggestions.append(
                    RepairSuggestion(
                        contract=result.contract,
                        strategy="inject_constraints",
                        prompt_patch="Return valid JSON matching the required schema with no prose outside the object.",
                    )
                )
            else:
                suggestions.append(
                    RepairSuggestion(
                        contract=result.contract,
                        strategy="adjust_system_prompt",
                        prompt_patch=f"Reinforce contract `{result.contract}` for trace `{trace.trace_id}` before retrying.",
                    )
                )
        return suggestions
