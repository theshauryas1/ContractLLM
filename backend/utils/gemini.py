import httpx
import logging
from backend.utils.config import get_settings

logger = logging.getLogger(__name__)

def generate_with_gemini(prompt: str, system_instruction: str = None) -> str:
    """
    Main generative entry point with a multi-provider fallback chain:
    1. Gemini API (attempts multiple model versions: gemini-flash-latest, gemini-2.0-flash, gemini-3.1-flash-lite)
    2. NVIDIA NIM (secondary with 60s timeout)
    3. xAI Grok (tertiary with 60s timeout)
    """
    settings = get_settings()
    errors = []

    # ----------------------------------------------------
    # Step 1: Try Gemini models in sequence
    # ----------------------------------------------------
    if settings.gemini_api_key:
        gemini_models = [settings.gemini_model, "gemini-2.0-flash", "gemini-3.1-flash-lite"]
        # Ensure model names are unique
        unique_gemini_models = []
        for m in gemini_models:
            if m not in unique_gemini_models:
                unique_gemini_models.append(m)

        for model in unique_gemini_models:
            url = f"{settings.gemini_base_url}/models/{model}:generateContent?key={settings.gemini_api_key}"
            system_part = f"{system_instruction}\n\n" if system_instruction else ""
            full_prompt = f"{system_part}{prompt}"
            try:
                logger.info(f"Attempting query with Gemini model: {model}")
                response = httpx.post(
                    url,
                    headers={"Content-Type": "application/json"},
                    json={
                        "contents": [
                            {
                                "parts": [
                                    {"text": full_prompt}
                                ]
                            }
                        ],
                        "generationConfig": {
                            "temperature": 0.2,
                            "maxOutputTokens": 2048,
                        }
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                res_json = response.json()
                return res_json["candidates"][0]["content"]["parts"][0]["text"]
            except Exception as e:
                err_msg = f"Gemini failed ({model}): {str(e)}"
                logger.warning(err_msg)
                errors.append(err_msg)

    # ----------------------------------------------------
    # Step 2: Try NVIDIA NIM Fallback (with 60s timeout)
    # ----------------------------------------------------
    if settings.nvidia_api_key:
        url = f"{settings.nvidia_base_url}/chat/completions"
        try:
            logger.info(f"Gemini failed or unconfigured. Falling back to NVIDIA NIM: {settings.nvidia_model}")
            messages = []
            if system_instruction:
                messages.append({"role": "system", "content": system_instruction})
            messages.append({"role": "user", "content": prompt})

            response = httpx.post(
                url,
                headers={
                    "Authorization": f"Bearer {settings.nvidia_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": settings.nvidia_model,
                    "messages": messages,
                    "temperature": 0.2,
                    "max_tokens": 2048
                },
                timeout=60.0
            )
            response.raise_for_status()
            res_json = response.json()
            return res_json["choices"][0]["message"]["content"]
        except Exception as e:
            err_msg = f"NVIDIA NIM failed ({settings.nvidia_model}): {str(e)}"
            logger.warning(err_msg)
            errors.append(err_msg)

    # ----------------------------------------------------
    # Step 3: Try xAI Grok Fallback (with 60s timeout)
    # ----------------------------------------------------
    if settings.xai_api_key:
        url = f"{settings.xai_base_url}/chat/completions"
        model_name = settings.llm_model if "grok" in settings.llm_model.lower() else "grok-beta"
        try:
            logger.info(f"NVIDIA NIM failed or unconfigured. Falling back to xAI Grok: {model_name}")
            messages = []
            if system_instruction:
                messages.append({"role": "system", "content": system_instruction})
            messages.append({"role": "user", "content": prompt})

            response = httpx.post(
                url,
                headers={
                    "Authorization": f"Bearer {settings.xai_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model_name,
                    "messages": messages,
                    "temperature": 0.2,
                    "max_tokens": 2048
                },
                timeout=60.0
            )
            response.raise_for_status()
            res_json = response.json()
            return res_json["choices"][0]["message"]["content"]
        except Exception as e:
            err_msg = f"xAI Grok failed ({model_name}): {str(e)}"
            logger.warning(err_msg)
            errors.append(err_msg)

    # All providers exhausted
    all_errors = " | ".join(errors)
    return f"Error: All configured legal models failed. Details: {all_errors or 'No providers configured'}"
