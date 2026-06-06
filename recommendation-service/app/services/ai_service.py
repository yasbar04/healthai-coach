import json
import re
import anthropic
from app.config import settings
from app.schemas.recommendation import WorkoutSession, FitnessLevelEnum, GoalEnum

COACHING_SYSTEM_PROMPT = """Tu es un coach sportif expert certifié. Tu fournis des conseils personnalisés, motivants et scientifiquement fondés.
Réponds TOUJOURS en JSON valide."""


class RecommendationAIService:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = "claude-opus-4-5"

    def _parse_json(self, text: str) -> dict:
        text = text.strip()
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if match:
            text = match.group(1)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            start, end = text.find("{"), text.rfind("}") + 1
            if start != -1 and end > start:
                return json.loads(text[start:end])
            raise ValueError("Impossible de parser la réponse IA")

    async def get_ai_coaching_tips(
        self,
        workout: WorkoutSession,
        user_stats: dict,
        nutrition_score: float | None,
    ) -> dict:
        exercise_names = [e.name for e in workout.exercises]
        nutrition_context = f"Score nutritionnel récent: {nutrition_score:.0f}/100." if nutrition_score else ""

        prompt = f"""Coaching personnalisé pour:
- Objectif: {workout.goal.value}
- Niveau: {workout.fitness_level.value}
- Séance: {workout.name}
- Exercices: {', '.join(exercise_names)}
- Durée: {workout.total_duration_minutes} min
- Calories estimées: {workout.estimated_calories} kcal
{nutrition_context}
- Historique: {user_stats.get('total_sessions', 0)} séances, {user_stats.get('total_duration_minutes', 0)} min total

Fournis en JSON:
{{
  "tips": ["conseil pratique 1", "conseil pratique 2", "conseil pratique 3"],
  "motivation": "message de motivation personnalisé",
  "next_session": "suggestion pour la prochaine séance",
  "nutrition_sync": "conseil sur la nutrition avant/après cette séance"
}}"""

        try:
            response = self.client.beta.messages.create(
                model=self.model,
                max_tokens=1024,
                betas=["prompt-caching-2024-07-31"],
                system=[{"type": "text", "text": COACHING_SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
                messages=[{"role": "user", "content": prompt}],
            )
            return self._parse_json(response.content[0].text)
        except Exception:
            return {
                "tips": [
                    "Hydratez-vous avant, pendant et après l'effort",
                    f"Pour {workout.goal.value}, maintenez la régularité plutôt que l'intensité",
                    "Écoutez votre corps et adaptez l'effort",
                ],
                "motivation": f"Chaque séance vous rapproche de votre objectif {workout.goal.value}. Continuez !",
                "next_session": "Prévoyez 48h de récupération avant la prochaine séance similaire.",
                "nutrition_sync": "Consommez des glucides 1-2h avant et des protéines dans l'heure suivant l'effort.",
            }


ai_coaching_service = RecommendationAIService()
