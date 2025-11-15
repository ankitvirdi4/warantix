from __future__ import annotations

import json
import logging
from typing import List

from openai import OpenAI
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import Settings
from ..models import Claim, Cluster

LOGGER = logging.getLogger(__name__)

MAX_SAMPLE_CLAIMS = 20


def _get_openai_client(settings: Settings) -> OpenAI | None:
    if not settings.openai_api_key:
        LOGGER.warning("OPENAI_API_KEY not configured; skipping AI reasoning")
        return None
    return OpenAI(api_key=settings.openai_api_key)


def _build_prompt(cluster: Cluster, sample_claims: List[Claim]) -> str:
    models = {claim.model for claim in sample_claims if claim.model}
    regions = {claim.region for claim in sample_claims if claim.region}
    dtcs = []
    components = []
    for claim in sample_claims:
        if claim.dtc_codes:
            dtcs.extend([code.strip() for code in claim.dtc_codes.split(",") if code.strip()])
        if claim.component:
            components.append(claim.component)

    dtcs = list(dict.fromkeys(dtcs))  # preserve order
    components = list(dict.fromkeys(components))

    symptom_lines = "\n".join(
        f"  * \"{claim.symptom_text}\"" for claim in sample_claims if claim.symptom_text
    )

    prompt = f"""
You are an automotive quality engineer. You receive warranty claim data for a single failure cluster.
Based on the patterns, you must:

1. Describe the likely root cause in one or two sentences.
2. Suggest 2–3 recommended next actions for engineering, supplier quality, or service teams.

Here is the cluster data:

* Number of claims: {cluster.num_claims}
* Total cost: {cluster.total_cost_usd}
* Models: {', '.join(sorted(models)) or 'Unknown'}
* Regions: {', '.join(sorted(regions)) or 'Unknown'}
* Sample DTC codes: {cluster.sample_dtc_codes or ', '.join(dtcs) or 'None'}
* Sample components: {cluster.sample_components or ', '.join(components) or 'None'}
* Sample claim texts:
{symptom_lines or '  * No sample texts available'}

Respond in valid JSON with the following structure:
{{
  "root_cause_hypothesis": "...",
  "recommended_actions": ["...", "..."]
}}
"""
    return prompt.strip()


def _call_model(client: OpenAI, settings: Settings, prompt: str) -> dict | None:
    try:
        response = client.chat.completions.create(
            model=settings.openai_completion_model,
            messages=[
                {"role": "system", "content": "You are a helpful automotive quality engineer."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
    except Exception as exc:  # pragma: no cover - network errors
        LOGGER.exception("Failed to generate AI explanation: %s", exc)
        return None

    content = response.choices[0].message.content if response.choices else None
    if not content:
        LOGGER.error("OpenAI response missing content")
        return None

    try:
        data = json.loads(content)
        if not isinstance(data, dict):
            raise ValueError("Response is not a JSON object")
        return data
    except json.JSONDecodeError as exc:
        LOGGER.error("Failed to parse JSON from OpenAI response: %s", exc)
        LOGGER.debug("Raw content: %s", content)
    except ValueError as exc:
        LOGGER.error("Invalid response format: %s", exc)

    return None


def update_ai_explanations_for_all_clusters(db: Session, settings: Settings) -> int:
    client = _get_openai_client(settings)
    if client is None:
        return 0

    clusters = (
        db.execute(
            select(Cluster).order_by(Cluster.num_claims.desc())
        ).scalars().all()
    )

    updated = 0
    for cluster in clusters:
        if cluster.num_claims == 0:
            continue
        if cluster.root_cause_hypothesis and cluster.recommended_actions:
            continue

        sample_claims = (
            db.execute(
                select(Claim)
                .where(Claim.cluster_id == cluster.id)
                .limit(MAX_SAMPLE_CLAIMS)
            )
            .scalars()
            .all()
        )
        if not sample_claims:
            continue

        prompt = _build_prompt(cluster, sample_claims)
        result = _call_model(client, settings, prompt)
        if not result:
            continue

        cluster.root_cause_hypothesis = result.get("root_cause_hypothesis")
        actions = result.get("recommended_actions")
        if isinstance(actions, list):
            cluster.recommended_actions = "\n".join(str(action) for action in actions)
        elif isinstance(actions, str):
            cluster.recommended_actions = actions
        db.add(cluster)
        updated += 1

    if updated:
        db.commit()

    return updated
