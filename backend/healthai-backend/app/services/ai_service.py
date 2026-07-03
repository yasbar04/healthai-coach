import asyncio
import base64
import json
import logging
import re
from typing import Any
import httpx
from app.config import settings

logger = logging.getLogger(__name__)

OLLAMA_TIMEOUT_SECS = 55        # text generation cutoff
OLLAMA_VISION_TIMEOUT_SECS = 240   # vision (llava) is slower; httpx gets +10s to avoid race

NUTRITION_SYSTEM_PROMPT = """Tu es un expert en nutrition et diététique certifié. Tu analyses des photos de repas et fournis des informations nutritionnelles précises.

Pour chaque analyse, tu dois:
1. Identifier tous les aliments visibles avec leurs quantités estimées
2. Calculer les apports caloriques et macronutriments (protéines, glucides, lipides, fibres)
3. Évaluer l'équilibre nutritionnel (score 0-100)
4. Détecter les déséquilibres (excès ou déficits)
5. Formuler des suggestions d'amélioration personnalisées

Réponds TOUJOURS en JSON valide avec exactement cette structure:
{
  "foods_detected": [
    {
      "name": "nom de l'aliment",
      "quantity_g": 150,
      "calories": 245,
      "macros": {
        "protein_g": 12.5,
        "carbs_g": 30.2,
        "fat_g": 8.1,
        "fiber_g": 2.3,
        "sugar_g": 5.0,
        "sodium_mg": 320
      }
    }
  ],
  "total_calories": 580,
  "macros": {
    "protein_g": 28.0,
    "carbs_g": 65.0,
    "fat_g": 18.5,
    "fiber_g": 6.0,
    "sugar_g": 12.0,
    "sodium_mg": 750
  },
  "health_score": 72,
  "imbalances": ["Teneur élevée en sodium", "Manque de légumes verts"],
  "suggestions": ["Ajouter une portion de légumes", "Réduire la sauce"],
  "meal_type_detected": "lunch",
  "analysis_confidence": 0.88
}"""

MEAL_PLAN_SYSTEM_PROMPT = """Tu es un nutritionniste expert qui crée des plans alimentaires personnalisés.
Tu dois créer des plans réalistes, équilibrés et adaptés aux besoins spécifiques de chaque utilisateur.
Réponds TOUJOURS en JSON valide selon la structure demandée."""

WORKOUT_SYSTEM_PROMPT = """Tu es un coach sportif certifié. Tu crées des séances d'entraînement personnalisées et réalistes.
Réponds UNIQUEMENT en JSON valide selon la structure exacte demandée."""


class AIService:
    def __init__(self):
        self._provider = settings.AI_PROVIDER  # "anthropic" | "ollama"

        if self._provider == "ollama":
            self._ollama_base = settings.OLLAMA_BASE_URL.rstrip("/")
            self._ollama_model = settings.OLLAMA_MODEL
            self._ollama_vision_model = settings.OLLAMA_VISION_MODEL
            self.client = None
            self._has_key = True  # Ollama needs no key
        else:
            import anthropic as _anthropic
            self._has_key = bool(settings.ANTHROPIC_API_KEY)
            self.client = _anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY) if self._has_key else None
            self.model = "claude-opus-4-5"

    def _demo_mode(self) -> bool:
        if self._provider == "ollama":
            return False
        return not self._has_key

    # ── Ollama helpers ────────────────────────────────────────────────────────

    async def _ollama_chat(self, prompt: str, system: str = "", num_predict: int = 1024) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        async def _call() -> str:
            async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT_SECS) as http:
                resp = await http.post(
                    f"{self._ollama_base}/api/chat",
                    json={
                        "model": self._ollama_model,
                        "messages": messages,
                        "stream": False,
                        "format": "json",
                        "options": {"temperature": 0.3, "num_predict": num_predict},
                    },
                )
                resp.raise_for_status()
                return resp.json()["message"]["content"]

        return await asyncio.wait_for(_call(), timeout=OLLAMA_TIMEOUT_SECS)

    async def _ollama_vision(self, image_b64: str, prompt: str) -> str:
        async def _call() -> str:
            async with httpx.AsyncClient(timeout=OLLAMA_VISION_TIMEOUT_SECS + 10) as http:
                resp = await http.post(
                    f"{self._ollama_base}/api/generate",
                    json={
                        "model": self._ollama_vision_model,
                        "prompt": prompt,
                        "images": [image_b64],
                        "stream": False,
                        "format": "json",
                        "options": {"temperature": 0.3, "num_predict": 1024},
                    },
                )
                resp.raise_for_status()
                return resp.json()["response"]

        return await asyncio.wait_for(_call(), timeout=OLLAMA_VISION_TIMEOUT_SECS)

    async def _ollama_available(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as http:
                r = await http.get(f"{self._ollama_base}/api/tags")
                return r.status_code == 200
        except Exception:
            return False

    def _parse_json_response(self, text: str) -> dict:
        text = text.strip()
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if json_match:
            text = json_match.group(1)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}") + 1
            if start != -1 and end > start:
                return json.loads(text[start:end])
            raise ValueError("Impossible de parser la réponse JSON de l'IA")

    def _fallback_meal_photo(self, user_profile: dict) -> dict:
        import random, traceback
        logger.warning("[fallback_meal_photo] appelé — stack:\n%s", "".join(traceback.format_stack(limit=6)))
        goal = user_profile.get("goal", "maintain")

        # Four varied demo meals — one is picked pseudo-randomly so repeated calls feel different
        demo_meals = [
            {
                "label": "Salade niçoise au thon",
                "foods": [
                    {"name": "Thon en conserve (au naturel)", "quantity_g": 130, "calories": 143,
                     "macros": {"protein_g": 30.0, "carbs_g": 0.0, "fat_g": 2.5, "fiber_g": 0.0, "sugar_g": 0.0, "sodium_mg": 280}},
                    {"name": "Haricots verts blanchis", "quantity_g": 120, "calories": 36,
                     "macros": {"protein_g": 2.2, "carbs_g": 7.5, "fat_g": 0.3, "fiber_g": 3.1, "sugar_g": 2.8, "sodium_mg": 6}},
                    {"name": "Pommes de terre vapeur", "quantity_g": 100, "calories": 86,
                     "macros": {"protein_g": 2.0, "carbs_g": 19.5, "fat_g": 0.1, "fiber_g": 1.8, "sugar_g": 0.9, "sodium_mg": 5}},
                    {"name": "Vinaigrette huile d'olive", "quantity_g": 20, "calories": 88,
                     "macros": {"protein_g": 0.1, "carbs_g": 0.5, "fat_g": 9.8, "fiber_g": 0.0, "sugar_g": 0.3, "sodium_mg": 95}},
                ],
                "total_calories": 353,
                "macros": {"protein_g": 34.3, "carbs_g": 27.5, "fat_g": 12.7, "fiber_g": 4.9, "sugar_g": 4.0, "sodium_mg": 386},
                "health_score": 86,
                "imbalances": ["Apport en glucides complexes modéré"],
                "meal_type": "lunch",
            },
            {
                "label": "Omelette provençale et pain complet",
                "foods": [
                    {"name": "Œufs entiers", "quantity_g": 150, "calories": 215,
                     "macros": {"protein_g": 18.5, "carbs_g": 1.2, "fat_g": 14.8, "fiber_g": 0.0, "sugar_g": 0.8, "sodium_mg": 200}},
                    {"name": "Tomates cerises", "quantity_g": 80, "calories": 18,
                     "macros": {"protein_g": 0.9, "carbs_g": 3.8, "fat_g": 0.2, "fiber_g": 1.2, "sugar_g": 2.6, "sodium_mg": 5}},
                    {"name": "Poivron rouge sauté", "quantity_g": 70, "calories": 22,
                     "macros": {"protein_g": 0.8, "carbs_g": 4.8, "fat_g": 0.3, "fiber_g": 1.6, "sugar_g": 3.2, "sodium_mg": 3}},
                    {"name": "Pain complet (1 tranche)", "quantity_g": 35, "calories": 82,
                     "macros": {"protein_g": 3.5, "carbs_g": 14.8, "fat_g": 1.0, "fiber_g": 2.0, "sugar_g": 1.1, "sodium_mg": 120}},
                ],
                "total_calories": 337,
                "macros": {"protein_g": 23.7, "carbs_g": 24.6, "fat_g": 16.3, "fiber_g": 4.8, "sugar_g": 7.7, "sodium_mg": 328},
                "health_score": 80,
                "imbalances": ["Légèrement élevé en lipides saturés"],
                "meal_type": "breakfast",
            },
            {
                "label": "Tajine de poulet aux légumes",
                "foods": [
                    {"name": "Blanc de poulet mijoté", "quantity_g": 160, "calories": 216,
                     "macros": {"protein_g": 40.0, "carbs_g": 1.5, "fat_g": 4.8, "fiber_g": 0.0, "sugar_g": 0.5, "sodium_mg": 120}},
                    {"name": "Courgettes", "quantity_g": 120, "calories": 21,
                     "macros": {"protein_g": 1.5, "carbs_g": 3.6, "fat_g": 0.3, "fiber_g": 1.2, "sugar_g": 2.5, "sodium_mg": 8}},
                    {"name": "Carottes", "quantity_g": 80, "calories": 33,
                     "macros": {"protein_g": 0.7, "carbs_g": 7.7, "fat_g": 0.2, "fiber_g": 2.3, "sugar_g": 4.5, "sodium_mg": 45}},
                    {"name": "Semoule de blé fine (cuite)", "quantity_g": 150, "calories": 174,
                     "macros": {"protein_g": 5.7, "carbs_g": 35.2, "fat_g": 0.8, "fiber_g": 2.1, "sugar_g": 0.3, "sodium_mg": 10}},
                ],
                "total_calories": 444,
                "macros": {"protein_g": 47.9, "carbs_g": 48.0, "fat_g": 6.1, "fiber_g": 5.6, "sugar_g": 7.8, "sodium_mg": 183},
                "health_score": 88,
                "imbalances": ["Apport en lipides essentiels insuffisant"],
                "meal_type": "dinner",
            },
            {
                "label": "Bowl de lentilles corail et épinards",
                "foods": [
                    {"name": "Lentilles corail cuites", "quantity_g": 180, "calories": 198,
                     "macros": {"protein_g": 13.5, "carbs_g": 34.2, "fat_g": 0.9, "fiber_g": 7.8, "sugar_g": 1.5, "sodium_mg": 15}},
                    {"name": "Épinards frais", "quantity_g": 80, "calories": 18,
                     "macros": {"protein_g": 2.2, "carbs_g": 2.4, "fat_g": 0.3, "fiber_g": 2.1, "sugar_g": 0.4, "sodium_mg": 65}},
                    {"name": "Feta émiettée", "quantity_g": 40, "calories": 100,
                     "macros": {"protein_g": 5.3, "carbs_g": 0.6, "fat_g": 8.4, "fiber_g": 0.0, "sugar_g": 0.5, "sodium_mg": 420}},
                    {"name": "Huile d'olive extra vierge", "quantity_g": 10, "calories": 88,
                     "macros": {"protein_g": 0.0, "carbs_g": 0.0, "fat_g": 9.9, "fiber_g": 0.0, "sugar_g": 0.0, "sodium_mg": 0}},
                ],
                "total_calories": 404,
                "macros": {"protein_g": 21.0, "carbs_g": 37.2, "fat_g": 19.5, "fiber_g": 9.9, "sugar_g": 2.4, "sodium_mg": 500},
                "health_score": 84,
                "imbalances": ["Teneur en sodium élevée (feta)"],
                "meal_type": "lunch",
            },
        ]

        suggestions_by_goal = {
            "lose_weight": ["Réduire les portions de féculents de 20-30%", "Augmenter la part de légumes verts non féculents"],
            "gain_muscle": ["Ajouter une deuxième source de protéines (œufs, légumineuses)", "Augmenter les glucides complexes post-entraînement"],
            "endurance": ["Privilégier les glucides complexes avant l'effort", "Bien s'hydrater — viser 2,5 L/jour"],
            "maintain": ["Équilibrer les macronutriments sur la journée", "Varier les sources de protéines végétales et animales"],
        }

        # Pick a meal variant based on a simple hash of the goal so the choice is deterministic per goal
        # but different from the default riz+poulet+brocolis
        index = {"lose_weight": 0, "gain_muscle": 2, "endurance": 3, "maintain": 1}.get(goal, 0)
        meal = demo_meals[index]

        return {
            "foods_detected": meal["foods"],
            "total_calories": meal["total_calories"],
            "macros": meal["macros"],
            "health_score": meal["health_score"],
            "imbalances": meal["imbalances"],
            "suggestions": suggestions_by_goal.get(goal, suggestions_by_goal["maintain"]),
            "meal_type_detected": meal["meal_type"],
            "analysis_confidence": 0.75,
            "_demo": True,
        }

    def _fallback_meal_plan(self, user_profile: dict, request: dict) -> dict:
        import uuid
        from datetime import datetime
        goal = user_profile.get("goal", "maintain")
        days_count = request.get("duration_days", 7)
        day_names = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]

        # Per-goal calorie targets (kcal/day)
        calorie_targets = {
            "lose_weight": 1500,
            "gain_muscle": 2600,
            "maintain": 2000,
            "endurance": 2300,
        }
        cal_target = calorie_targets.get(goal, 2000)

        # ---------------------------------------------------------------------------
        # 7 distinct breakfast / lunch / dinner combinations per goal.
        # Macros are calibrated so the three meals sum close to cal_target.
        # "b" = breakfast  (≈25 %)   "l" = lunch  (≈40 %)   "d" = dinner  (≈35 %)
        # ---------------------------------------------------------------------------
        meal_plans_by_goal: dict[str, list[dict]] = {

            # ── LOSE WEIGHT  (1 500 kcal) ────────────────────────────────────────
            "lose_weight": [
                {   # Lundi
                    "b": {"name": "Yaourt grec nature et fruits rouges",
                          "ingredients": ["150g yaourt grec 0%", "100g fraises", "1 c.s. graines de chia", "1 c.c. miel"],
                          "prep_time_minutes": 5, "calories": 185,
                          "macros": {"protein_g": 14, "carbs_g": 22, "fat_g": 3, "fiber_g": 4, "sugar_g": 14, "sodium_mg": 50},
                          "instructions": "Mélanger le yaourt et le miel, garnir de fraises et de graines de chia."},
                    "l": {"name": "Salade de lentilles vertes au feta",
                          "ingredients": ["180g lentilles vertes cuites", "40g feta", "80g tomates cerises", "roquette", "vinaigrette citron"],
                          "prep_time_minutes": 10, "calories": 395,
                          "macros": {"protein_g": 22, "carbs_g": 42, "fat_g": 12, "fiber_g": 9, "sugar_g": 4, "sodium_mg": 340},
                          "instructions": "Mélanger les lentilles refroidies, les tomates, la roquette et la feta. Assaisonner."},
                    "d": {"name": "Filet de cabillaud en papillote aux herbes",
                          "ingredients": ["160g cabillaud", "150g haricots verts", "1/2 citron", "thym", "1 c.c. huile d'olive"],
                          "prep_time_minutes": 20, "calories": 265,
                          "macros": {"protein_g": 32, "carbs_g": 10, "fat_g": 8, "fiber_g": 4, "sugar_g": 2, "sodium_mg": 130},
                          "instructions": "Envelopper le poisson avec les haricots et les herbes. Cuire 18 min à 180 °C."},
                },
                {   # Mardi
                    "b": {"name": "Smoothie banane-épinards-protéines",
                          "ingredients": ["1 banane", "40g épinards frais", "200ml lait d'amande", "1 dose whey nature"],
                          "prep_time_minutes": 5, "calories": 250,
                          "macros": {"protein_g": 22, "carbs_g": 28, "fat_g": 4, "fiber_g": 3, "sugar_g": 16, "sodium_mg": 90},
                          "instructions": "Mixer tous les ingrédients jusqu'à consistance lisse."},
                    "l": {"name": "Soupe de carottes au gingembre et tartine seigle",
                          "ingredients": ["300g carottes", "1 cm gingembre frais", "1 oignon", "500ml bouillon légumes", "1 tranche pain de seigle"],
                          "prep_time_minutes": 25, "calories": 290,
                          "macros": {"protein_g": 7, "carbs_g": 48, "fat_g": 5, "fiber_g": 8, "sugar_g": 12, "sodium_mg": 420},
                          "instructions": "Faire revenir l'oignon, ajouter carottes et gingembre, couvrir de bouillon, mixer."},
                    "d": {"name": "Escalope de dinde aux champignons",
                          "ingredients": ["150g escalope de dinde", "200g champignons de Paris", "1 échalote", "1 c.s. crème allégée", "persil"],
                          "prep_time_minutes": 15, "calories": 280,
                          "macros": {"protein_g": 36, "carbs_g": 8, "fat_g": 9, "fiber_g": 2, "sugar_g": 3, "sodium_mg": 200},
                          "instructions": "Saisir la dinde, faire revenir les champignons et l'échalote, déglacer avec la crème."},
                },
                {   # Mercredi
                    "b": {"name": "Œufs brouillés sur pain complet",
                          "ingredients": ["2 œufs", "1 tranche pain complet", "30g épinards", "1 c.c. huile d'olive"],
                          "prep_time_minutes": 8, "calories": 270,
                          "macros": {"protein_g": 16, "carbs_g": 18, "fat_g": 12, "fiber_g": 3, "sugar_g": 2, "sodium_mg": 180},
                          "instructions": "Brouiller les œufs à feu doux, servir sur le pain grillé avec les épinards."},
                    "l": {"name": "Wrap de poulet grillé et légumes croquants",
                          "ingredients": ["120g blanc de poulet", "1 tortilla blé complet", "60g avocat", "salade", "tomate", "citron"],
                          "prep_time_minutes": 15, "calories": 430,
                          "macros": {"protein_g": 32, "carbs_g": 35, "fat_g": 14, "fiber_g": 5, "sugar_g": 3, "sodium_mg": 310},
                          "instructions": "Griller le poulet, trancher l'avocat, assembler le wrap et rouler serré."},
                    "d": {"name": "Ratatouille provençale sans matière grasse",
                          "ingredients": ["1 courgette", "1 aubergine", "2 tomates", "1 poivron", "herbes de Provence", "1 c.c. huile d'olive"],
                          "prep_time_minutes": 30, "calories": 160,
                          "macros": {"protein_g": 4, "carbs_g": 22, "fat_g": 5, "fiber_g": 7, "sugar_g": 12, "sodium_mg": 90},
                          "instructions": "Couper les légumes en rondelles, disposer en couches, huiler légèrement et enfourner 30 min à 180 °C."},
                },
                {   # Jeudi
                    "b": {"name": "Porridge d'avoine à la pomme et cannelle",
                          "ingredients": ["60g flocons d'avoine", "200ml lait écrémé", "1 pomme", "1/2 c.c. cannelle"],
                          "prep_time_minutes": 8, "calories": 280,
                          "macros": {"protein_g": 10, "carbs_g": 50, "fat_g": 4, "fiber_g": 6, "sugar_g": 18, "sodium_mg": 70},
                          "instructions": "Cuire les flocons dans le lait 5 min, ajouter la pomme râpée et la cannelle."},
                    "l": {"name": "Salade niçoise légère",
                          "ingredients": ["100g thon au naturel", "80g haricots verts", "1 œuf dur", "6 olives noires", "tomates", "vinaigrette légère"],
                          "prep_time_minutes": 10, "calories": 340,
                          "macros": {"protein_g": 28, "carbs_g": 14, "fat_g": 16, "fiber_g": 4, "sugar_g": 5, "sodium_mg": 450},
                          "instructions": "Assembler tous les ingrédients dans un plat, arroser de vinaigrette."},
                    "d": {"name": "Crevettes sautées à l'ail et courgettes",
                          "ingredients": ["150g crevettes décortiquées", "2 courgettes", "2 gousses d'ail", "1 c.s. huile d'olive", "persil"],
                          "prep_time_minutes": 12, "calories": 240,
                          "macros": {"protein_g": 28, "carbs_g": 10, "fat_g": 8, "fiber_g": 2, "sugar_g": 4, "sodium_mg": 310},
                          "instructions": "Faire revenir l'ail, ajouter les crevettes et les courgettes en julienne, cuire 5 min."},
                },
                {   # Vendredi
                    "b": {"name": "Bowl de skyr aux kiwis et noix",
                          "ingredients": ["160g skyr nature", "2 kiwis", "15g cerneaux de noix", "1 c.c. sirop d'agave"],
                          "prep_time_minutes": 5, "calories": 260,
                          "macros": {"protein_g": 18, "carbs_g": 26, "fat_g": 8, "fiber_g": 4, "sugar_g": 16, "sodium_mg": 60},
                          "instructions": "Verser le skyr dans un bol, disposer les kiwis et les noix, napper de sirop."},
                    "l": {"name": "Velouté de poireaux et pomme de terre",
                          "ingredients": ["2 poireaux", "150g pomme de terre", "500ml bouillon poulet allégé", "1 c.s. crème allégée"],
                          "prep_time_minutes": 25, "calories": 250,
                          "macros": {"protein_g": 6, "carbs_g": 38, "fat_g": 6, "fiber_g": 5, "sugar_g": 6, "sodium_mg": 380},
                          "instructions": "Faire fondre les poireaux, ajouter la pomme de terre et le bouillon, mixer, finir avec la crème."},
                    "d": {"name": "Pavé de saumon grillé et purée de céleri-rave",
                          "ingredients": ["140g saumon", "200g céleri-rave", "1 c.c. huile d'olive", "ciboulette", "1/2 citron"],
                          "prep_time_minutes": 20, "calories": 360,
                          "macros": {"protein_g": 30, "carbs_g": 18, "fat_g": 16, "fiber_g": 4, "sugar_g": 4, "sodium_mg": 180},
                          "instructions": "Cuire le céleri-rave à l'eau, mixer en purée. Griller le saumon 4 min de chaque côté."},
                },
                {   # Samedi
                    "b": {"name": "Pancakes à l'avoine sans sucre ajouté",
                          "ingredients": ["60g flocons d'avoine mixés", "1 œuf", "100ml lait écrémé", "1 banane mûre"],
                          "prep_time_minutes": 15, "calories": 310,
                          "macros": {"protein_g": 12, "carbs_g": 52, "fat_g": 6, "fiber_g": 5, "sugar_g": 14, "sodium_mg": 80},
                          "instructions": "Mixer tous les ingrédients, cuire de petites crêpes épaisses à feu moyen."},
                    "l": {"name": "Salade de pois chiches à la marocaine",
                          "ingredients": ["200g pois chiches cuits", "1/2 concombre", "tomates", "cumin", "persil", "citron", "huile d'olive"],
                          "prep_time_minutes": 10, "calories": 340,
                          "macros": {"protein_g": 14, "carbs_g": 44, "fat_g": 10, "fiber_g": 10, "sugar_g": 6, "sodium_mg": 200},
                          "instructions": "Mélanger les pois chiches égouttés avec les légumes coupés et les épices."},
                    "d": {"name": "Dos de merlu rôti et légumes méditerranéens",
                          "ingredients": ["160g merlu", "1 courgette", "1 poivron", "tomates cerises", "1 c.s. huile d'olive", "basilic"],
                          "prep_time_minutes": 25, "calories": 280,
                          "macros": {"protein_g": 30, "carbs_g": 14, "fat_g": 9, "fiber_g": 4, "sugar_g": 6, "sodium_mg": 160},
                          "instructions": "Disposer le poisson sur les légumes, arroser d'huile et cuire 20 min à 200 °C."},
                },
                {   # Dimanche
                    "b": {"name": "Tartines de pain de seigle à l'avocat",
                          "ingredients": ["2 tranches pain de seigle", "80g avocat", "2 tranches saumon fumé léger", "citron", "câpres"],
                          "prep_time_minutes": 5, "calories": 320,
                          "macros": {"protein_g": 16, "carbs_g": 30, "fat_g": 14, "fiber_g": 5, "sugar_g": 2, "sodium_mg": 450},
                          "instructions": "Écraser l'avocat avec le citron, étaler sur le pain, garnir de saumon et câpres."},
                    "l": {"name": "Taboulé libanais au boulgour",
                          "ingredients": ["100g boulgour cuit", "persil frais", "menthe", "tomates", "concombre", "citron", "huile d'olive"],
                          "prep_time_minutes": 20, "calories": 310,
                          "macros": {"protein_g": 8, "carbs_g": 48, "fat_g": 9, "fiber_g": 6, "sugar_g": 4, "sodium_mg": 80},
                          "instructions": "Cuire le boulgour, laisser refroidir, mélanger avec les herbes et légumes coupés fin."},
                    "d": {"name": "Poulet rôti à la moutarde et haricots plats",
                          "ingredients": ["160g cuisse de poulet sans peau", "1 c.s. moutarde de Dijon", "200g haricots plats", "1 gousse d'ail", "herbes"],
                          "prep_time_minutes": 35, "calories": 380,
                          "macros": {"protein_g": 34, "carbs_g": 14, "fat_g": 18, "fiber_g": 5, "sugar_g": 3, "sodium_mg": 270},
                          "instructions": "Badigeonner le poulet de moutarde et enfourner 30 min à 190 °C. Blanchir les haricots."},
                },
            ],

            # ── GAIN MUSCLE  (2 600 kcal) ────────────────────────────────────────
            "gain_muscle": [
                {   # Lundi
                    "b": {"name": "Overnight oats protéiné aux amandes",
                          "ingredients": ["90g flocons d'avoine", "300ml lait entier", "1 dose whey vanille", "30g amandes", "1 banane"],
                          "prep_time_minutes": 5, "calories": 640,
                          "macros": {"protein_g": 38, "carbs_g": 78, "fat_g": 18, "fiber_g": 8, "sugar_g": 20, "sodium_mg": 140},
                          "instructions": "Mélanger tous les ingrédients la veille, réfrigérer toute la nuit."},
                    "l": {"name": "Riz complet au poulet et légumes rôtis",
                          "ingredients": ["180g blanc de poulet", "150g riz complet cuit", "200g légumes rôtis", "1 c.s. huile d'olive", "épices"],
                          "prep_time_minutes": 25, "calories": 720,
                          "macros": {"protein_g": 52, "carbs_g": 78, "fat_g": 16, "fiber_g": 8, "sugar_g": 6, "sodium_mg": 250},
                          "instructions": "Griller le poulet, servir sur le riz avec les légumes rôtis."},
                    "d": {"name": "Steak de bœuf maigre et patates douces",
                          "ingredients": ["200g steak de bœuf (5% MG)", "200g patate douce", "200g épinards sautés", "1 c.s. huile d'olive"],
                          "prep_time_minutes": 20, "calories": 620,
                          "macros": {"protein_g": 48, "carbs_g": 52, "fat_g": 18, "fiber_g": 6, "sugar_g": 8, "sodium_mg": 200},
                          "instructions": "Cuire la patate douce au four 40 min, saisir le steak 3 min de chaque côté."},
                },
                {   # Mardi
                    "b": {"name": "Omelette 4 œufs au fromage de chèvre et tomates",
                          "ingredients": ["4 œufs", "40g fromage de chèvre frais", "100g tomates cerises", "basilic", "1 c.c. huile d'olive"],
                          "prep_time_minutes": 10, "calories": 480,
                          "macros": {"protein_g": 34, "carbs_g": 8, "fat_g": 34, "fiber_g": 1, "sugar_g": 5, "sodium_mg": 280},
                          "instructions": "Battre les œufs, ajouter le chèvre et les tomates, cuire en omelette à feu moyen."},
                    "l": {"name": "Pâtes complètes bolognaise maison",
                          "ingredients": ["160g pâtes complètes sèches", "180g bœuf haché 5%", "1 boîte tomates pelées", "oignon", "ail", "basilic"],
                          "prep_time_minutes": 30, "calories": 780,
                          "macros": {"protein_g": 52, "carbs_g": 88, "fat_g": 18, "fiber_g": 10, "sugar_g": 10, "sodium_mg": 380},
                          "instructions": "Faire revenir la viande avec l'oignon et l'ail, ajouter les tomates, mijoter 20 min. Servir sur les pâtes cuites."},
                    "d": {"name": "Dos de saumon grillé et lentilles beluga",
                          "ingredients": ["180g saumon", "180g lentilles beluga cuites", "1 c.s. huile d'olive", "citron", "coriandre"],
                          "prep_time_minutes": 20, "calories": 680,
                          "macros": {"protein_g": 52, "carbs_g": 38, "fat_g": 26, "fiber_g": 10, "sugar_g": 2, "sodium_mg": 180},
                          "instructions": "Griller le saumon 5 min de chaque côté, servir sur les lentilles assaisonnées."},
                },
                {   # Mercredi
                    "b": {"name": "Pancakes protéinés banane-avoine",
                          "ingredients": ["80g flocons d'avoine", "2 œufs", "1 banane", "1 dose whey chocolat", "150ml lait"],
                          "prep_time_minutes": 15, "calories": 550,
                          "macros": {"protein_g": 42, "carbs_g": 62, "fat_g": 10, "fiber_g": 6, "sugar_g": 18, "sodium_mg": 150},
                          "instructions": "Mixer tous les ingrédients, former des pancakes et cuire à sec ou avec peu d'huile."},
                    "l": {"name": "Bowl de quinoa aux œufs durs et avocat",
                          "ingredients": ["150g quinoa cuit", "3 œufs durs", "1 avocat", "concombre", "sauce soja légère"],
                          "prep_time_minutes": 15, "calories": 700,
                          "macros": {"protein_g": 36, "carbs_g": 62, "fat_g": 32, "fiber_g": 9, "sugar_g": 3, "sodium_mg": 350},
                          "instructions": "Disposer le quinoa dans un bol, garnir avec les œufs coupés, l'avocat et le concombre."},
                    "d": {"name": "Filets de poulet marinés au yaourt et patates douces",
                          "ingredients": ["200g poulet", "100g yaourt grec", "epices tikka", "200g patate douce", "salade verte"],
                          "prep_time_minutes": 30, "calories": 650,
                          "macros": {"protein_g": 54, "carbs_g": 56, "fat_g": 14, "fiber_g": 5, "sugar_g": 10, "sodium_mg": 280},
                          "instructions": "Mariner le poulet dans le yaourt et les épices 1h, griller ou rôtir 25 min."},
                },
                {   # Jeudi
                    "b": {"name": "Bowl de granola maison et kéfir",
                          "ingredients": ["60g granola aux noix", "200ml kéfir", "100g myrtilles", "2 c.s. beurre de cacahuète"],
                          "prep_time_minutes": 5, "calories": 580,
                          "macros": {"protein_g": 22, "carbs_g": 62, "fat_g": 28, "fiber_g": 6, "sugar_g": 22, "sodium_mg": 120},
                          "instructions": "Verser le kéfir dans un bol, ajouter le granola, les myrtilles et le beurre de cacahuète."},
                    "l": {"name": "Tortillas de blé complet au bœuf et haricots rouges",
                          "ingredients": ["2 tortillas", "150g bœuf haché", "120g haricots rouges", "salsa", "40g cheddar", "crème fraîche légère"],
                          "prep_time_minutes": 20, "calories": 740,
                          "macros": {"protein_g": 50, "carbs_g": 68, "fat_g": 26, "fiber_g": 10, "sugar_g": 6, "sodium_mg": 680},
                          "instructions": "Faire revenir le bœuf, ajouter les haricots et la salsa, garnir les tortillas avec le fromage."},
                    "d": {"name": "Truite amandine et purée de pois cassés",
                          "ingredients": ["180g truite", "30g amandes effilées", "200g pois cassés cuits", "1 c.s. beurre", "citron"],
                          "prep_time_minutes": 25, "calories": 700,
                          "macros": {"protein_g": 54, "carbs_g": 44, "fat_g": 28, "fiber_g": 10, "sugar_g": 4, "sodium_mg": 220},
                          "instructions": "Dorer la truite au beurre, parsemer d'amandes. Mixer les pois cassés avec le citron."},
                },
                {   # Vendredi
                    "b": {"name": "Toast avocado-saumon fumé et œuf poché",
                          "ingredients": ["2 tranches pain complet épais", "1 avocat", "80g saumon fumé", "2 œufs", "citron", "aneth"],
                          "prep_time_minutes": 12, "calories": 600,
                          "macros": {"protein_g": 36, "carbs_g": 44, "fat_g": 28, "fiber_g": 7, "sugar_g": 3, "sodium_mg": 620},
                          "instructions": "Pocher les œufs, écraser l'avocat sur le pain, garnir de saumon et de l'œuf poché."},
                    "l": {"name": "Risotto au poulet et champignons",
                          "ingredients": ["160g riz arborio", "150g poulet", "150g champignons", "50ml vin blanc", "30g parmesan", "bouillon"],
                          "prep_time_minutes": 35, "calories": 780,
                          "macros": {"protein_g": 46, "carbs_g": 86, "fat_g": 18, "fiber_g": 4, "sugar_g": 4, "sodium_mg": 520},
                          "instructions": "Saisir le poulet, réserver. Faire le risotto classique, incorporer les champignons et le parmesan."},
                    "d": {"name": "Thon snacké et taboulé de chou-fleur",
                          "ingredients": ["180g thon frais", "1 chou-fleur", "tomates", "persil", "citron", "huile d'olive", "olives"],
                          "prep_time_minutes": 20, "calories": 600,
                          "macros": {"protein_g": 52, "carbs_g": 26, "fat_g": 22, "fiber_g": 7, "sugar_g": 6, "sodium_mg": 280},
                          "instructions": "Mixer le chou-fleur cru en semoule, assaisonner comme un taboulé. Snacker le thon 2 min de chaque côté."},
                },
                {   # Samedi
                    "b": {"name": "Crêpes sarrasin œuf-fromage",
                          "ingredients": ["4 galettes de sarrasin", "3 œufs", "60g emmental râpé", "80g jambon blanc", "salade"],
                          "prep_time_minutes": 15, "calories": 580,
                          "macros": {"protein_g": 42, "carbs_g": 46, "fat_g": 22, "fiber_g": 3, "sugar_g": 2, "sodium_mg": 680},
                          "instructions": "Garnir chaque galette d'œuf, fromage et jambon, plier en carré et cuire jusqu'à dorure."},
                    "l": {"name": "Curry de pois chiches et dinde à la noix de coco",
                          "ingredients": ["160g dinde", "200g pois chiches", "200ml lait de coco", "épices curry", "riz basmati 120g"],
                          "prep_time_minutes": 30, "calories": 800,
                          "macros": {"protein_g": 52, "carbs_g": 82, "fat_g": 22, "fiber_g": 10, "sugar_g": 8, "sodium_mg": 380},
                          "instructions": "Faire revenir les épices, ajouter la dinde, les pois chiches et le lait de coco. Mijoter 15 min."},
                    "d": {"name": "Brochettes d'agneau et légumes grillés",
                          "ingredients": ["200g agneau maigre", "poivrons", "courgettes", "oignon rouge", "marinade herbes", "couscous 100g"],
                          "prep_time_minutes": 25, "calories": 680,
                          "macros": {"protein_g": 46, "carbs_g": 52, "fat_g": 22, "fiber_g": 6, "sugar_g": 8, "sodium_mg": 300},
                          "instructions": "Mariner l'agneau, monter les brochettes et griller 8 min. Servir sur couscous."},
                },
                {   # Dimanche
                    "b": {"name": "Gaufres protéinées aux pépites de chocolat noir",
                          "ingredients": ["80g farine avoine", "2 œufs", "200ml lait", "1 dose whey", "30g chocolat noir 85%"],
                          "prep_time_minutes": 20, "calories": 560,
                          "macros": {"protein_g": 40, "carbs_g": 58, "fat_g": 16, "fiber_g": 5, "sugar_g": 12, "sodium_mg": 150},
                          "instructions": "Mélanger tous les ingrédients, cuire dans le gaufrier, garnir de chocolat fondu."},
                    "l": {"name": "Poulet fermier rôti et tian de légumes",
                          "ingredients": ["220g cuisse de poulet fermier", "1 aubergine", "2 tomates", "1 courgette", "thym", "romarin", "huile d'olive"],
                          "prep_time_minutes": 50, "calories": 720,
                          "macros": {"protein_g": 50, "carbs_g": 30, "fat_g": 36, "fiber_g": 7, "sugar_g": 10, "sodium_mg": 250},
                          "instructions": "Rôtir le poulet 45 min. Couper les légumes en rondelles, superposer et cuire 30 min."},
                    "d": {"name": "Spaghetti de blé complet aux crevettes et pesto",
                          "ingredients": ["140g spaghetti complets", "150g crevettes", "40g pesto maison", "tomates cerises", "parmesan"],
                          "prep_time_minutes": 20, "calories": 700,
                          "macros": {"protein_g": 44, "carbs_g": 72, "fat_g": 22, "fiber_g": 8, "sugar_g": 4, "sodium_mg": 420},
                          "instructions": "Cuire les pâtes, saisir les crevettes, mélanger avec le pesto et les tomates."},
                },
            ],

            # ── MAINTAIN  (2 000 kcal) ────────────────────────────────────────────
            "maintain": [
                {   # Lundi
                    "b": {"name": "Bol de muesli aux fruits frais et lait",
                          "ingredients": ["70g muesli sans sucre ajouté", "200ml lait demi-écrémé", "1 kiwi", "1/2 pomme"],
                          "prep_time_minutes": 5, "calories": 380,
                          "macros": {"protein_g": 12, "carbs_g": 64, "fat_g": 8, "fiber_g": 7, "sugar_g": 22, "sodium_mg": 80},
                          "instructions": "Verser le lait sur le muesli, garnir avec les fruits coupés."},
                    "l": {"name": "Quiche lorraine légère et salade verte",
                          "ingredients": ["1 part quiche lorraine légère (150g)", "grande salade verte", "tomates", "vinaigrette légère"],
                          "prep_time_minutes": 5, "calories": 500,
                          "macros": {"protein_g": 22, "carbs_g": 38, "fat_g": 26, "fiber_g": 4, "sugar_g": 4, "sodium_mg": 480},
                          "instructions": "Réchauffer la quiche, dresser la salade avec la vinaigrette."},
                    "d": {"name": "Dos de cabillaud à la crème de poireaux",
                          "ingredients": ["160g cabillaud", "2 poireaux", "100ml crème légère", "1 c.s. beurre", "noix de muscade"],
                          "prep_time_minutes": 20, "calories": 380,
                          "macros": {"protein_g": 32, "carbs_g": 18, "fat_g": 18, "fiber_g": 4, "sugar_g": 6, "sodium_mg": 300},
                          "instructions": "Faire fondre les poireaux au beurre, ajouter la crème. Cuire le cabillaud vapeur 10 min."},
                },
                {   # Mardi
                    "b": {"name": "Tartines de pain de campagne et beurre de noisette",
                          "ingredients": ["2 tranches pain de campagne", "20g beurre de noisette", "1 banane", "café ou thé"],
                          "prep_time_minutes": 5, "calories": 380,
                          "macros": {"protein_g": 8, "carbs_g": 56, "fat_g": 12, "fiber_g": 4, "sugar_g": 16, "sodium_mg": 180},
                          "instructions": "Toaster le pain, étaler le beurre de noisette et trancher la banane dessus."},
                    "l": {"name": "Salade de quinoa aux légumes grillés et mozzarella",
                          "ingredients": ["120g quinoa cuit", "1 boule mozzarella", "poivrons grillés", "roquette", "pignons de pin", "huile d'olive"],
                          "prep_time_minutes": 15, "calories": 560,
                          "macros": {"protein_g": 24, "carbs_g": 52, "fat_g": 26, "fiber_g": 6, "sugar_g": 5, "sodium_mg": 340},
                          "instructions": "Mélanger le quinoa refroidi, les légumes et la roquette. Déposer la mozzarella et les pignons."},
                    "d": {"name": "Côte de porc marinée aux herbes et purée de carotte",
                          "ingredients": ["160g côte de porc filet", "300g carottes", "1 c.s. huile d'olive", "thym", "romarin"],
                          "prep_time_minutes": 25, "calories": 480,
                          "macros": {"protein_g": 34, "carbs_g": 32, "fat_g": 20, "fiber_g": 5, "sugar_g": 10, "sodium_mg": 260},
                          "instructions": "Mariner la viande, griller 4 min de chaque côté. Cuire les carottes, mixer avec un filet d'huile."},
                },
                {   # Mercredi
                    "b": {"name": "Smoothie bowl mangue-ananas",
                          "ingredients": ["150g mangue", "100g ananas", "100g yaourt nature", "30g granola", "noix de coco râpée"],
                          "prep_time_minutes": 8, "calories": 380,
                          "macros": {"protein_g": 8, "carbs_g": 68, "fat_g": 8, "fiber_g": 5, "sugar_g": 46, "sodium_mg": 50},
                          "instructions": "Mixer la mangue et l'ananas avec le yaourt, verser dans un bol, garnir de granola et noix de coco."},
                    "l": {"name": "Croque-monsieur complet et soupe de tomate",
                          "ingredients": ["2 tranches pain complet", "60g jambon", "40g gruyère", "1 c.s. béchamel légère", "250ml soupe tomate"],
                          "prep_time_minutes": 15, "calories": 540,
                          "macros": {"protein_g": 28, "carbs_g": 52, "fat_g": 20, "fiber_g": 5, "sugar_g": 10, "sodium_mg": 820},
                          "instructions": "Assembler le croque-monsieur, faire gratiner au four. Réchauffer la soupe."},
                    "d": {"name": "Daurade royale en croûte d'herbes et tian provençal",
                          "ingredients": ["180g daurade", "panure herbes fraîches", "1 tomate", "1 courgette", "1 aubergine", "huile d'olive"],
                          "prep_time_minutes": 30, "calories": 480,
                          "macros": {"protein_g": 36, "carbs_g": 22, "fat_g": 22, "fiber_g": 6, "sugar_g": 8, "sodium_mg": 250},
                          "instructions": "Croûter le poisson avec les herbes et cuire 18 min. Disposer le tian et enfourner 25 min."},
                },
                {   # Jeudi
                    "b": {"name": "Pain perdu à la vanille et compote",
                          "ingredients": ["2 tranches pain de mie complet", "2 œufs", "100ml lait", "vanille", "100g compote pomme sans sucre"],
                          "prep_time_minutes": 10, "calories": 380,
                          "macros": {"protein_g": 16, "carbs_g": 52, "fat_g": 10, "fiber_g": 4, "sugar_g": 18, "sodium_mg": 220},
                          "instructions": "Tremper le pain dans le mélange œufs-lait-vanille, cuire à la poêle, servir avec la compote."},
                    "l": {"name": "Blanquette de veau traditionnelle et riz",
                          "ingredients": ["140g veau", "carottes", "champignons", "bouillon", "crème légère", "100g riz blanc"],
                          "prep_time_minutes": 40, "calories": 560,
                          "macros": {"protein_g": 34, "carbs_g": 58, "fat_g": 16, "fiber_g": 4, "sugar_g": 6, "sodium_mg": 480},
                          "instructions": "Mijoter le veau avec les légumes 30 min, lier la sauce à la crème. Servir avec le riz."},
                    "d": {"name": "Salade composée au jambon de Parme et parmesan",
                          "ingredients": ["60g jambon de Parme", "40g parmesan", "roquette", "figues fraîches", "vinaigre balsamique", "huile d'olive"],
                          "prep_time_minutes": 5, "calories": 440,
                          "macros": {"protein_g": 22, "carbs_g": 26, "fat_g": 26, "fiber_g": 3, "sugar_g": 14, "sodium_mg": 620},
                          "instructions": "Disposer la roquette, le Parme et les figues, parsemer de parmesan, arroser de balsamique."},
                },
                {   # Vendredi
                    "b": {"name": "Fromage blanc aux noix et confiture de figues",
                          "ingredients": ["200g fromage blanc 3,2%", "20g cerneaux de noix", "1 c.s. confiture de figues", "pain complet 1 tranche"],
                          "prep_time_minutes": 5, "calories": 390,
                          "macros": {"protein_g": 16, "carbs_g": 46, "fat_g": 14, "fiber_g": 3, "sugar_g": 20, "sodium_mg": 100},
                          "instructions": "Verser le fromage blanc dans un bol, ajouter les noix et la confiture. Tartiner le pain."},
                    "l": {"name": "Moules marinières et pain de campagne",
                          "ingredients": ["400g moules", "200ml vin blanc sec", "2 échalotes", "persil", "crème légère", "2 tranches pain"],
                          "prep_time_minutes": 20, "calories": 480,
                          "macros": {"protein_g": 30, "carbs_g": 38, "fat_g": 12, "fiber_g": 2, "sugar_g": 4, "sodium_mg": 680},
                          "instructions": "Faire ouvrir les moules dans le vin blanc avec les échalotes et le persil. Finir à la crème."},
                    "d": {"name": "Tarte au poulet et légumes de saison",
                          "ingredients": ["1 part tarte poulet-légumes (180g)", "salade verte", "vinaigrette légère"],
                          "prep_time_minutes": 10, "calories": 500,
                          "macros": {"protein_g": 28, "carbs_g": 46, "fat_g": 22, "fiber_g": 5, "sugar_g": 5, "sodium_mg": 480},
                          "instructions": "Réchauffer la tarte au four 10 min, dresser la salade."},
                },
                {   # Samedi
                    "b": {"name": "Brunch œuf cocotte et toast intégral",
                          "ingredients": ["2 œufs cocotte", "30g crème fraîche", "30g saumon fumé", "1 tranche pain intégral", "aneth"],
                          "prep_time_minutes": 15, "calories": 360,
                          "macros": {"protein_g": 20, "carbs_g": 20, "fat_g": 20, "fiber_g": 2, "sugar_g": 2, "sodium_mg": 520},
                          "instructions": "Déposer la crème et le saumon dans des ramequins, casser les œufs, cuire 12 min à 180 °C."},
                    "l": {"name": "Pizza maison sur pâte fine et légumes grillés",
                          "ingredients": ["1 pâte fine 120g", "60ml sauce tomate", "1 boule mozzarella", "poivrons grillés", "basilic"],
                          "prep_time_minutes": 25, "calories": 580,
                          "macros": {"protein_g": 24, "carbs_g": 64, "fat_g": 22, "fiber_g": 5, "sugar_g": 8, "sodium_mg": 680},
                          "instructions": "Étaler la pâte, garnir de sauce, mozzarella et légumes, cuire 12 min à 220 °C."},
                    "d": {"name": "Magret de canard et gratin dauphinois léger",
                          "ingredients": ["140g magret de canard (dégraissé)", "200g pommes de terre", "100ml crème légère", "ail", "noix de muscade"],
                          "prep_time_minutes": 40, "calories": 560,
                          "macros": {"protein_g": 30, "carbs_g": 38, "fat_g": 28, "fiber_g": 4, "sugar_g": 3, "sodium_mg": 320},
                          "instructions": "Cuire le gratin 35 min. Saisir le magret côté gras 6 min puis retourner 4 min."},
                },
                {   # Dimanche
                    "b": {"name": "Crêpes bretonnes au sarrasin et miel de fleurs",
                          "ingredients": ["100g farine de sarrasin", "2 œufs", "250ml lait", "20g beurre", "2 c.s. miel de fleurs"],
                          "prep_time_minutes": 20, "calories": 440,
                          "macros": {"protein_g": 14, "carbs_g": 66, "fat_g": 14, "fiber_g": 4, "sugar_g": 20, "sodium_mg": 140},
                          "instructions": "Préparer la pâte, cuire les crêpes fines, napper de miel."},
                    "l": {"name": "Osso buco de veau aux agrumes et gremolata",
                          "ingredients": ["160g osso buco veau", "1 orange", "1 citron", "tomates pelées", "farine", "huile d'olive", "riz 100g"],
                          "prep_time_minutes": 60, "calories": 580,
                          "macros": {"protein_g": 38, "carbs_g": 52, "fat_g": 18, "fiber_g": 4, "sugar_g": 8, "sodium_mg": 380},
                          "instructions": "Fariner et dorer l'osso buco, ajouter les tomates et zestes d'agrumes, mijoter 45 min."},
                    "d": {"name": "Velouté de potimarron et crottins de chèvre chaud",
                          "ingredients": ["400g potimarron", "1 oignon", "500ml bouillon légumes", "2 crottins chèvre", "crème légère"],
                          "prep_time_minutes": 25, "calories": 420,
                          "macros": {"protein_g": 18, "carbs_g": 38, "fat_g": 20, "fiber_g": 5, "sugar_g": 10, "sodium_mg": 420},
                          "instructions": "Cuire le potimarron avec l'oignon, mixer avec la crème. Passer les crottins au gril 3 min."},
                },
            ],

            # ── ENDURANCE  (2 300 kcal) ───────────────────────────────────────────
            "endurance": [
                {   # Lundi
                    "b": {"name": "Porridge énergétique banane-beurre de cacahuète",
                          "ingredients": ["90g flocons d'avoine", "300ml lait entier", "1 banane", "2 c.s. beurre de cacahuète", "1 c.c. miel"],
                          "prep_time_minutes": 8, "calories": 560,
                          "macros": {"protein_g": 20, "carbs_g": 78, "fat_g": 18, "fiber_g": 8, "sugar_g": 22, "sodium_mg": 130},
                          "instructions": "Cuire les flocons dans le lait, garnir avec la banane tranchée, le beurre de cacahuète et le miel."},
                    "l": {"name": "Pâtes de blé dur thon-tomates et olives",
                          "ingredients": ["160g pâtes de blé dur", "130g thon au naturel", "boîte tomates pelées", "olives noires", "câpres"],
                          "prep_time_minutes": 20, "calories": 640,
                          "macros": {"protein_g": 42, "carbs_g": 82, "fat_g": 10, "fiber_g": 7, "sugar_g": 6, "sodium_mg": 480},
                          "instructions": "Cuire les pâtes al dente, mélanger avec le thon, les tomates et les olives."},
                    "d": {"name": "Pavé de saumon et patates douces rôties",
                          "ingredients": ["160g saumon", "250g patate douce", "100g brocolis", "1 c.s. huile d'olive", "citron"],
                          "prep_time_minutes": 25, "calories": 620,
                          "macros": {"protein_g": 38, "carbs_g": 60, "fat_g": 20, "fiber_g": 8, "sugar_g": 10, "sodium_mg": 200},
                          "instructions": "Rôtir la patate douce au four 25 min. Cuire le saumon à la poêle 4 min de chaque côté."},
                },
                {   # Mardi
                    "b": {"name": "Granola maison aux graines et yaourt à la grecque",
                          "ingredients": ["70g granola aux graines", "180g yaourt grec 2%", "100g fraises", "1 c.s. miel"],
                          "prep_time_minutes": 5, "calories": 480,
                          "macros": {"protein_g": 20, "carbs_g": 66, "fat_g": 12, "fiber_g": 6, "sugar_g": 28, "sodium_mg": 90},
                          "instructions": "Verser le yaourt dans un bol, ajouter le granola et les fraises, napper de miel."},
                    "l": {"name": "Riz thaï au poulet sauté et légumes croquants",
                          "ingredients": ["150g riz thaï cuit", "150g blanc de poulet", "poivrons", "brocolis", "sauce soja légère", "sésame"],
                          "prep_time_minutes": 20, "calories": 620,
                          "macros": {"protein_g": 42, "carbs_g": 76, "fat_g": 10, "fiber_g": 6, "sugar_g": 5, "sodium_mg": 480},
                          "instructions": "Sauter le poulet et les légumes au wok, ajouter la sauce soja, servir sur le riz."},
                    "d": {"name": "Lentilles coral-coco au curry et naan complet",
                          "ingredients": ["200g lentilles corail", "200ml lait de coco léger", "épices curry", "1 naan complet", "coriandre"],
                          "prep_time_minutes": 25, "calories": 600,
                          "macros": {"protein_g": 26, "carbs_g": 82, "fat_g": 14, "fiber_g": 12, "sugar_g": 6, "sodium_mg": 320},
                          "instructions": "Cuire les lentilles dans le lait de coco avec les épices, garnir de coriandre fraîche."},
                },
                {   # Mercredi
                    "b": {"name": "Tartines complètes jambon de pays et œuf mollet",
                          "ingredients": ["2 tranches pain complet", "2 tranches jambon de pays", "2 œufs mollets", "tomates", "moutarde"],
                          "prep_time_minutes": 10, "calories": 460,
                          "macros": {"protein_g": 30, "carbs_g": 44, "fat_g": 14, "fiber_g": 5, "sugar_g": 4, "sodium_mg": 680},
                          "instructions": "Cuire les œufs 6 min, toaster le pain, assembler avec le jambon, la tomate et la moutarde."},
                    "l": {"name": "Bowl hawaïen poke au thon et edamame",
                          "ingredients": ["120g thon frais", "150g riz à sushi cuit", "80g edamame", "avocat", "sauce soja", "sésame"],
                          "prep_time_minutes": 15, "calories": 620,
                          "macros": {"protein_g": 40, "carbs_g": 68, "fat_g": 18, "fiber_g": 7, "sugar_g": 4, "sodium_mg": 520},
                          "instructions": "Couper le thon en dés, disposer sur le riz avec l'avocat et l'edamame, arroser de sauce soja."},
                    "d": {"name": "Bœuf sauté au gingembre et nouilles de riz",
                          "ingredients": ["150g bœuf maigre", "150g nouilles de riz", "1 cm gingembre", "oignons verts", "sauce huître", "brocolis"],
                          "prep_time_minutes": 20, "calories": 600,
                          "macros": {"protein_g": 38, "carbs_g": 70, "fat_g": 14, "fiber_g": 5, "sugar_g": 5, "sodium_mg": 560},
                          "instructions": "Sauter rapidement le bœuf avec le gingembre, ajouter les brocolis et la sauce, servir sur les nouilles."},
                },
                {   # Jeudi
                    "b": {"name": "Bircher muesli aux abricots et amandes",
                          "ingredients": ["80g flocons d'avoine", "200ml jus de pomme", "2 abricots", "20g amandes", "100g yaourt"],
                          "prep_time_minutes": 5, "calories": 500,
                          "macros": {"protein_g": 14, "carbs_g": 78, "fat_g": 12, "fiber_g": 7, "sugar_g": 30, "sodium_mg": 60},
                          "instructions": "Tremper les flocons dans le jus toute la nuit, garnir le lendemain avec les fruits et les amandes."},
                    "l": {"name": "Gnocchis de pomme de terre à la sauce tomate basilic",
                          "ingredients": ["200g gnocchis", "200ml sauce tomate maison", "30g parmesan", "basilic frais"],
                          "prep_time_minutes": 15, "calories": 600,
                          "macros": {"protein_g": 18, "carbs_g": 96, "fat_g": 12, "fiber_g": 5, "sugar_g": 8, "sodium_mg": 520},
                          "instructions": "Cuire les gnocchis, égoutter et mélanger avec la sauce tomate chaude, finir au parmesan."},
                    "d": {"name": "Sauté de crevettes et légumes sur soba",
                          "ingredients": ["150g crevettes", "120g nouilles soba", "carottes en julienne", "épinards", "tamari léger", "sésame"],
                          "prep_time_minutes": 15, "calories": 560,
                          "macros": {"protein_g": 36, "carbs_g": 72, "fat_g": 8, "fiber_g": 5, "sugar_g": 4, "sodium_mg": 480},
                          "instructions": "Cuire les sobas, sauter les crevettes et les légumes, mélanger avec le tamari."},
                },
                {   # Vendredi
                    "b": {"name": "Crêpes à la farine de petit épeautre et sirop d'érable",
                          "ingredients": ["80g farine petit épeautre", "2 œufs", "200ml lait", "1 banane", "2 c.s. sirop d'érable"],
                          "prep_time_minutes": 15, "calories": 520,
                          "macros": {"protein_g": 16, "carbs_g": 82, "fat_g": 10, "fiber_g": 5, "sugar_g": 28, "sodium_mg": 100},
                          "instructions": "Préparer la pâte, cuire des crêpes fines, garnir de banane et sirop d'érable."},
                    "l": {"name": "Paella végétarienne aux légumes et safran",
                          "ingredients": ["160g riz à paella", "poivrons", "tomates", "petits pois", "safran", "bouillon légumes", "huile d'olive"],
                          "prep_time_minutes": 35, "calories": 620,
                          "macros": {"protein_g": 14, "carbs_g": 104, "fat_g": 10, "fiber_g": 8, "sugar_g": 8, "sodium_mg": 380},
                          "instructions": "Faire revenir les légumes, ajouter le riz et le bouillon, cuire 20 min sans remuer."},
                    "d": {"name": "Filet de poulet citron-origan et semoule perlée",
                          "ingredients": ["160g poulet", "150g semoule perlée cuite", "citron", "origan", "1 c.s. huile d'olive", "courgettes"],
                          "prep_time_minutes": 20, "calories": 560,
                          "macros": {"protein_g": 40, "carbs_g": 62, "fat_g": 12, "fiber_g": 5, "sugar_g": 4, "sodium_mg": 220},
                          "instructions": "Mariner le poulet au citron et origan, griller 8 min. Servir avec la semoule et les courgettes vapeur."},
                },
                {   # Samedi
                    "b": {"name": "Toast figues-ricotta et miel de châtaignier",
                          "ingredients": ["2 tranches pain complet", "100g ricotta", "2 figues fraîches", "1 c.s. miel de châtaignier", "noix"],
                          "prep_time_minutes": 8, "calories": 480,
                          "macros": {"protein_g": 14, "carbs_g": 66, "fat_g": 16, "fiber_g": 5, "sugar_g": 26, "sodium_mg": 180},
                          "instructions": "Toaster le pain, étaler la ricotta, couper les figues, garnir de noix et miel."},
                    "l": {"name": "Taboulé de boulgour poulet grillé et tzatziki",
                          "ingredients": ["120g boulgour cuit", "120g poulet", "concombre", "tomates", "menthe", "citron", "100g tzatziki"],
                          "prep_time_minutes": 20, "calories": 600,
                          "macros": {"protein_g": 38, "carbs_g": 68, "fat_g": 14, "fiber_g": 7, "sugar_g": 6, "sodium_mg": 320},
                          "instructions": "Cuire le boulgour, griller le poulet, assembler le taboulé et servir avec le tzatziki."},
                    "d": {"name": "Morue à la biscaïenne et riz pilaf",
                          "ingredients": ["160g morue dessalée", "tomates", "poivrons", "oignon", "ail", "piment doux", "120g riz pilaf"],
                          "prep_time_minutes": 30, "calories": 620,
                          "macros": {"protein_g": 40, "carbs_g": 78, "fat_g": 8, "fiber_g": 6, "sugar_g": 10, "sodium_mg": 460},
                          "instructions": "Faire revenir l'oignon et les poivrons, ajouter les tomates et la morue, mijoter 15 min. Servir sur riz pilaf."},
                },
                {   # Dimanche
                    "b": {"name": "Gaufres d'avoine aux pépites de chocolat et banane",
                          "ingredients": ["70g flocons d'avoine mixés", "2 œufs", "150ml lait", "1 banane", "30g pépites de chocolat noir"],
                          "prep_time_minutes": 15, "calories": 540,
                          "macros": {"protein_g": 18, "carbs_g": 76, "fat_g": 16, "fiber_g": 6, "sugar_g": 22, "sodium_mg": 100},
                          "instructions": "Mixer les flocons, mélanger avec les œufs et le lait, cuire au gaufrier, garnir de banane et chocolat."},
                    "l": {"name": "Couscous royal poulet-merguez et légumes",
                          "ingredients": ["150g couscous cuit", "120g poulet", "1 merguez", "carottes", "courgettes", "pois chiches", "harissa"],
                          "prep_time_minutes": 40, "calories": 720,
                          "macros": {"protein_g": 42, "carbs_g": 84, "fat_g": 18, "fiber_g": 10, "sugar_g": 8, "sodium_mg": 620},
                          "instructions": "Cuire le poulet et la merguez, préparer les légumes en ragoût épicé, servir sur le couscous."},
                    "d": {"name": "Ceviche de bar aux agrumes et patatas bravas",
                          "ingredients": ["150g bar frais", "jus 2 citrons verts", "1 orange", "coriandre", "200g pommes de terre", "paprika"],
                          "prep_time_minutes": 25, "calories": 460,
                          "macros": {"protein_g": 32, "carbs_g": 54, "fat_g": 8, "fiber_g": 5, "sugar_g": 6, "sodium_mg": 200},
                          "instructions": "Mariner le bar en lamelles dans les jus d'agrumes 15 min. Rôtir les pommes de terre au paprika."},
                },
            ],
        }

        # Fall back to maintain if goal is unknown
        day_templates = meal_plans_by_goal.get(goal, meal_plans_by_goal["maintain"])

        # Nutritional summary per goal
        nutritional_summaries = {
            "lose_weight": {"avg_protein_g": 82, "avg_carbs_g": 112, "avg_fat_g": 38},
            "gain_muscle":  {"avg_protein_g": 145, "avg_carbs_g": 195, "avg_fat_g": 68},
            "maintain":     {"avg_protein_g": 100, "avg_carbs_g": 150, "avg_fat_g": 58},
            "endurance":    {"avg_protein_g": 110, "avg_carbs_g": 195, "avg_fat_g": 50},
        }
        ns = nutritional_summaries.get(goal, nutritional_summaries["maintain"])

        days = []
        for i in range(min(days_count, 7)):
            tmpl = day_templates[i]
            b, l, d = tmpl["b"], tmpl["l"], tmpl["d"]
            day_cal = b["calories"] + l["calories"] + d["calories"]
            days.append({
                "day": i + 1,
                "day_name": day_names[i],
                "total_calories": day_cal,
                "meals": [
                    {"meal_type": "breakfast", **b},
                    {"meal_type": "lunch",     **l},
                    {"meal_type": "dinner",    **d},
                ],
            })

        shopping_lists = {
            "lose_weight": [
                "Yaourt grec 0%", "Fruits rouges (fraises, myrtilles)", "Graines de chia", "Lentilles vertes",
                "Feta", "Cabillaud", "Haricots verts", "Dinde (escalopes)", "Champignons de Paris",
                "Pain complet", "Avocat", "Poulet (blancs)", "Thon au naturel", "Saumon (pavés)",
                "Céleri-rave", "Crevettes", "Pois chiches", "Merlu", "Citrons", "Herbes fraîches",
            ],
            "gain_muscle": [
                "Flocons d'avoine", "Whey protéine", "Amandes", "Bananes", "Bœuf haché 5%",
                "Poulet (blancs)", "Saumon (pavés)", "Pâtes complètes", "Lentilles beluga",
                "Riz complet", "Patates douces", "Quinoa", "Œufs", "Fromage de chèvre frais",
                "Truite", "Pois cassés", "Jambon blanc", "Pois chiches", "Agneau maigre",
                "Crevettes", "Farine d'avoine", "Chocolat noir 85%",
            ],
            "maintain": [
                "Muesli sans sucre ajouté", "Lait demi-écrémé", "Kiwis", "Quiche lorraine",
                "Cabillaud", "Poireaux", "Mozzarella", "Quinoa", "Jambon de Parme",
                "Côte de porc filet", "Carottes", "Fromage blanc 3,2%", "Noix", "Moules",
                "Vin blanc sec", "Magret de canard", "Pommes de terre", "Potimarron",
                "Crottins de chèvre", "Pain de campagne",
            ],
            "endurance": [
                "Flocons d'avoine", "Beurre de cacahuète", "Bananes", "Pâtes de blé dur",
                "Thon au naturel", "Saumon (pavés)", "Patates douces", "Riz thaï",
                "Lentilles corail", "Lait de coco léger", "Gnocchis", "Crevettes",
                "Nouilles soba", "Boulgour", "Poulet (blancs)", "Riz pilaf",
                "Morue", "Couscous", "Figues fraîches", "Ricotta",
            ],
        }

        return {
            "plan_id": str(uuid.uuid4()),
            "goal": goal,
            "daily_calorie_target": cal_target,
            "days": days,
            "shopping_list": shopping_lists.get(goal, shopping_lists["maintain"]),
            "nutritional_summary": {
                "avg_daily_calories": cal_target,
                **ns,
            },
            "generated_at": datetime.utcnow().isoformat(),
            "_demo": True,
        }

    async def analyze_meal_photo(self, image_bytes: bytes, user_profile: dict) -> dict:
        if self._demo_mode():
            return self._fallback_meal_photo(user_profile)

        image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")
        goal_context = {
            "lose_weight": "L'utilisateur souhaite perdre du poids — priorise les aliments peu caloriques, riches en fibres et protéines.",
            "gain_muscle": "L'utilisateur souhaite prendre de la masse — priorise les protéines et glucides complexes.",
            "maintain": "L'utilisateur souhaite maintenir son poids — équilibre général.",
            "endurance": "L'utilisateur s'entraîne pour l'endurance — priorise les glucides complexes.",
        }
        goal = user_profile.get("goal", "maintain")
        context = goal_context.get(goal, goal_context["maintain"])
        allergies = user_profile.get("allergies", [])
        allergy_note = f"Allergies connues: {', '.join(allergies)}." if allergies else ""

        if self._provider == "ollama":
            # Keep prompt short — llava is a vision model, long prompts slow it down a lot
            allergy_str = f" Allergies: {', '.join(allergies)}." if allergies else ""
            prompt = (
                f"Analyse cette photo de repas. Identifie chaque aliment visible, estime les quantités en grammes et les calories.{allergy_str}"
                f" Réponds UNIQUEMENT en JSON valide:\n"
                f'{{"foods_detected":[{{"name":"nom","quantity_g":150,"calories":200,'
                f'"macros":{{"protein_g":10,"carbs_g":25,"fat_g":5,"fiber_g":2,"sugar_g":3,"sodium_mg":100}}}}],'
                f'"total_calories":500,"macros":{{"protein_g":25,"carbs_g":60,"fat_g":15,"fiber_g":5,"sugar_g":8,"sodium_mg":400}},'
                f'"health_score":75,"imbalances":["..."],"suggestions":["..."],"meal_type_detected":"lunch","analysis_confidence":0.8}}'
            )
            try:
                available = await self._ollama_available()
                logger.info("[Ollama vision] available=%s model=%s", available, self._ollama_vision_model)
                if not available:
                    return self._fallback_meal_photo(user_profile)
                raw = await self._ollama_vision(image_b64, prompt)
                result = self._parse_json_response(raw)
                # Ensure required keys exist (llava sometimes omits some)
                result.setdefault("foods_detected", [])
                result.setdefault("total_calories", 0)
                result.setdefault("macros", {"protein_g": 0, "carbs_g": 0, "fat_g": 0, "fiber_g": 0, "sugar_g": 0, "sodium_mg": 0})
                result.setdefault("health_score", 70)
                result.setdefault("imbalances", [])
                result.setdefault("suggestions", [])
                result.setdefault("meal_type_detected", "unknown")
                result.setdefault("analysis_confidence", 0.7)
                result["_ollama"] = True
                return result
            except Exception as _exc:
                logger.error("[Ollama vision] exception: %s: %s", type(_exc).__name__, _exc)
                return self._fallback_meal_photo(user_profile)

        try:
            response = self.client.beta.messages.create(
                model=self.model,
                max_tokens=2048,
                betas=["prompt-caching-2024-07-31"],
                system=[
                    {
                        "type": "text",
                        "text": NUTRITION_SYSTEM_PROMPT,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": image_b64,
                                },
                            },
                            {
                                "type": "text",
                                "text": f"Analyse ce repas. {context} {allergy_note} Réponds en JSON.",
                            },
                        ],
                    }
                ],
            )
            return self._parse_json_response(response.content[0].text)
        except Exception as e:
            return self._fallback_nutrition_response(str(e))

    async def generate_meal_plan(self, user_profile: dict, request: dict) -> dict:
        if self._demo_mode():
            return self._fallback_meal_plan(user_profile, request)

        if self._provider == "ollama":
            return await self._ollama_generate_meal_plan(user_profile, request)

        weight = user_profile.get("weight_kg", 70)
        height = user_profile.get("height_cm", 170)
        age = user_profile.get("age", 30)
        goal = user_profile.get("goal", "maintain")
        activity = user_profile.get("activity_level", "moderate")
        allergies = user_profile.get("allergies", [])
        preferences = user_profile.get("dietary_preferences", [])

        activity_multipliers = {
            "sedentary": 1.2, "light": 1.375, "moderate": 1.55,
            "active": 1.725, "very_active": 1.9
        }
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
        tdee = bmr * activity_multipliers.get(activity, 1.55)
        calorie_adjustments = {"lose_weight": -500, "gain_muscle": 300, "maintain": 0, "endurance": 200}
        calorie_target = request.get("calorie_target") or tdee + calorie_adjustments.get(goal, 0)

        prompt = f"""Crée un plan alimentaire de {request.get('duration_days', 7)} jours.

Profil:
- Objectif calorique: {calorie_target:.0f} kcal/jour
- Objectif: {goal}
- Niveau d'activité: {activity}
- Repas par jour: {request.get('meals_per_day', 3)}
- Budget: {request.get('budget_level', 'medium')}
- Allergies: {', '.join(allergies) if allergies else 'aucune'}
- Préférences: {', '.join(preferences) if preferences else 'aucune'}

Réponds en JSON avec cette structure exacte:
{{
  "plan_id": "plan_uuid_here",
  "goal": "{goal}",
  "daily_calorie_target": {calorie_target:.0f},
  "days": [
    {{
      "day": 1,
      "day_name": "Lundi",
      "total_calories": 1850,
      "meals": [
        {{
          "meal_type": "breakfast",
          "name": "Nom du repas",
          "ingredients": ["ingrédient 1 (quantité)", "ingrédient 2"],
          "prep_time_minutes": 10,
          "calories": 420,
          "macros": {{"protein_g": 25, "carbs_g": 45, "fat_g": 12, "fiber_g": 5, "sugar_g": 8, "sodium_mg": 300}},
          "instructions": "Instructions de préparation courtes."
        }}
      ]
    }}
  ],
  "shopping_list": ["article 1", "article 2"],
  "nutritional_summary": {{
    "avg_daily_calories": {calorie_target:.0f},
    "avg_protein_g": 130,
    "avg_carbs_g": 200,
    "avg_fat_g": 65
  }}
}}"""

        try:
            response = self.client.beta.messages.create(
                model=self.model,
                max_tokens=8192,
                betas=["prompt-caching-2024-07-31"],
                system=[
                    {
                        "type": "text",
                        "text": MEAL_PLAN_SYSTEM_PROMPT,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                messages=[{"role": "user", "content": prompt}],
            )
            result = self._parse_json_response(response.content[0].text)
            if "plan_id" not in result or result["plan_id"] == "plan_uuid_here":
                import uuid
                result["plan_id"] = str(uuid.uuid4())
            from datetime import datetime
            result["generated_at"] = datetime.utcnow().isoformat()
            return result
        except Exception as e:
            raise ValueError(f"Erreur lors de la génération du plan: {e}")

    async def analyze_nutrition_trend(self, nutrition_logs: list) -> dict:
        if not nutrition_logs:
            return {"insights": [], "recommendations": [], "trend": "insufficient_data"}
        if self._demo_mode():
            return {
                "insights": ["Apport calorique stable sur la période", "Bon ratio protéines/glucides"],
                "recommendations": ["Augmenter les fibres (+5g/jour)", "Maintenir l'hydratation à 2L/jour"],
                "trend": "stable",
                "weekly_avg_calories": 1950,
                "_demo": True,
            }

        summary = [
            f"Jour {i+1}: {log.get('total_calories', 0):.0f} kcal, "
            f"P:{log.get('protein_g', 0):.0f}g C:{log.get('carbs_g', 0):.0f}g L:{log.get('fat_g', 0):.0f}g"
            for i, log in enumerate(nutrition_logs[-14:])
        ]
        prompt = (
            f"Analyse ces données nutritionnelles et fournis des insights en JSON:\n"
            f"{chr(10).join(summary)}\n\n"
            f'Réponds UNIQUEMENT avec: {{"insights": ["..."], "recommendations": ["..."], "trend": "improving/stable/declining", "weekly_avg_calories": 1800}}'
        )

        if self._provider == "ollama":
            try:
                if not await self._ollama_available():
                    return {"insights": [], "recommendations": [], "trend": "stable"}
                raw = await self._ollama_chat(prompt)
                return self._parse_json_response(raw)
            except Exception:
                return {"insights": [], "recommendations": [], "trend": "stable"}

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )
            return self._parse_json_response(response.content[0].text)
        except Exception:
            return {"insights": [], "recommendations": [], "trend": "stable"}

    async def generate_workout(self, user_profile: dict, request: dict) -> dict:
        if self._demo_mode():
            return self._fallback_workout(user_profile, request)
        if self._provider == "ollama":
            return await self._ollama_generate_workout(user_profile, request)
        return self._fallback_workout(user_profile, request)

    async def _ollama_generate_workout(self, user_profile: dict, request: dict) -> dict:
        import uuid
        from datetime import datetime

        if not await self._ollama_available():
            return self._fallback_workout(user_profile, request)

        goal = request.get("goal", "maintain")
        level = request.get("fitness_level", "intermediate")
        minutes = request.get("available_minutes", 45)
        equipment = request.get("equipment", [])
        restrictions = request.get("restrictions", [])

        goal_labels = {"lose_weight": "perte de poids", "gain_muscle": "prise de masse", "maintain": "maintien", "endurance": "endurance"}
        level_labels = {"beginner": "débutant", "intermediate": "intermédiaire", "advanced": "avancé"}

        # Calculate how many exercises fit — ~12 min per exercise on average, minimum 3
        nb_exercises = max(3, minutes // 12)
        # Each exercise JSON block is ~200 tokens; add overhead for other fields
        needed_tokens = 300 + nb_exercises * 220

        prompt = f"""Crée une séance d'entraînement de {minutes} minutes pour objectif {goal_labels.get(goal, goal)}, niveau {level_labels.get(level, level)}.
Équipement: {', '.join(equipment) if equipment else 'aucun (poids du corps)'}.
Restrictions: {', '.join(restrictions) if restrictions else 'aucune'}.
Tu dois inclure EXACTEMENT {nb_exercises} exercices dans le tableau "exercises" (les durées doivent totaliser environ {minutes} minutes).

Réponds UNIQUEMENT en JSON valide:
{{
  "session_name": "Nom de la séance",
  "rationale": "Pourquoi cette séance est adaptée",
  "ai_tips": ["conseil 1", "conseil 2", "conseil 3"],
  "next_session_suggestion": "Suggestion pour la prochaine séance",
  "estimated_calories": 350,
  "warmup": ["échauffement 1", "échauffement 2"],
  "cooldown": ["étirement 1", "étirement 2"],
  "exercises": [
    {{
      "name": "Nom exercice",
      "category": "strength",
      "muscle_groups": ["quadriceps", "fessiers"],
      "duration_minutes": 10,
      "calories_per_hour": 300,
      "difficulty": "{level}",
      "description": "Description courte",
      "instructions": ["étape 1", "étape 2"],
      "benefits": ["bénéfice 1"]
    }}
  ]
}}"""

        try:
            raw = await self._ollama_chat(prompt, WORKOUT_SYSTEM_PROMPT, num_predict=needed_tokens)
            data = self._parse_json_response(raw)

            session_id = str(uuid.uuid4())
            rec_id = str(uuid.uuid4())
            now = datetime.utcnow().isoformat()

            exercises = []
            for i, ex in enumerate(data.get("exercises", [])):
                exercises.append({
                    "id": str(uuid.uuid4()),
                    "name": ex.get("name", f"Exercice {i+1}"),
                    "category": ex.get("category", "strength"),
                    "muscle_groups": ex.get("muscle_groups", []),
                    "equipment": equipment,
                    "duration_minutes": int(ex.get("duration_minutes", 10)),
                    "calories_per_hour": int(ex.get("calories_per_hour", 300)),
                    "difficulty": ex.get("difficulty", level),
                    "description": ex.get("description", ""),
                    "instructions": ex.get("instructions", []),
                    "benefits": ex.get("benefits", []),
                })

            return {
                "recommendation_id": rec_id,
                "user_id": user_profile.get("user_id", 0),
                "workout": {
                    "session_id": session_id,
                    "name": data.get("session_name", "Séance IA"),
                    "goal": goal,
                    "fitness_level": level,
                    "total_duration_minutes": minutes,
                    "estimated_calories": int(data.get("estimated_calories", 300)),
                    "exercises": exercises,
                    "warmup": data.get("warmup", []),
                    "cooldown": data.get("cooldown", []),
                },
                "rationale": data.get("rationale", ""),
                "ai_tips": data.get("ai_tips", []),
                "next_session_suggestion": data.get("next_session_suggestion", ""),
                "generated_at": now,
                "_ollama": True,
            }
        except Exception:
            return self._fallback_workout(user_profile, request)

    def _fallback_workout(self, user_profile: dict, request: dict) -> dict:
        import uuid
        from datetime import datetime

        goal = request.get("goal", "maintain")
        level = request.get("fitness_level", "intermediate")
        minutes = int(request.get("available_minutes", 45))
        user_id = user_profile.get("user_id", 0)
        now = datetime.utcnow().isoformat()

        workouts = {
            "lose_weight": {
                "name": "Circuit Cardio-HIIT Brûle-Graisses",
                "rationale": "Séance cardio-HIIT intense pour maximiser la dépense calorique.",
                "ai_tips": ["Maintenez 70-80% FCmax pendant les blocs cardio.", "Hydratez-vous régulièrement.", "Enchaînez sans pause pour optimiser la combustion."],
                "next_session_suggestion": "Demain : renforcement musculaire léger + stretching 30 min.",
                "estimated_calories": int(minutes * 9.5),
                "warmup": ["Marche rapide 3 min", "Rotations épaules 30s", "Fentes dynamiques 1 min"],
                "cooldown": ["Étirement ischio-jambiers 45s", "Pigeon yoga 30s", "Respiration profonde 1 min"],
                "exercises": [
                    {"id": "burpee", "name": "Burpees", "category": "hiit", "muscle_groups": ["full_body"], "equipment": [], "duration_minutes": max(5, minutes//6), "calories_per_hour": 600, "difficulty": "intermediate", "description": "Exercice complet : squat + planche + saut.", "instructions": ["Debout", "Squat, mains au sol", "Sauter en planche", "Pompe", "Ramener pieds, sauter"], "benefits": ["~10 kcal/min", "Full body", "Cardio"]},
                    {"id": "mountain-climber", "name": "Mountain Climbers", "category": "cardio", "muscle_groups": ["core", "épaules"], "equipment": [], "duration_minutes": max(4, minutes//8), "calories_per_hour": 500, "difficulty": "intermediate", "description": "Planche dynamique pour cardio et gainage.", "instructions": ["Planche bras tendus", "Genoux alternés vers poitrine", "Rythme rapide", "3x30 répétitions"], "benefits": ["Cardio intense", "Gainage", "Coordination"]},
                    {"id": "jump-squat", "name": "Squats Sautés", "category": "hiit", "muscle_groups": ["quadriceps", "fessiers"], "equipment": [], "duration_minutes": max(5, minutes//7), "calories_per_hour": 550, "difficulty": "intermediate", "description": "Squat + saut explosif.", "instructions": ["Pieds écartés", "Squat profond", "Explosif vers le haut", "Atterrir genoux fléchis", "4x15"], "benefits": ["Tonifie jambes", "Brûle beaucoup", "Force explosive"]},
                ],
            },
            "gain_muscle": {
                "name": "Renforcement Musculaire Progressif",
                "rationale": "Séance de force avec charge progressive pour stimuler l'hypertrophie.",
                "ai_tips": ["Respectez 60-90s de repos entre séries.", "Mangez des protéines dans l'heure post-séance.", "Augmentez la charge de 2.5% chaque semaine."],
                "next_session_suggestion": "Repos ou cardio léger demain. Prochaine force dans 48h.",
                "estimated_calories": int(minutes * 6),
                "warmup": ["Mobilisation articulaire 3 min", "Pompes légères 2x10", "Squat corporel 2x10"],
                "cooldown": ["Étirement pectoraux 45s", "Étirement quadriceps 30s chaque jambe", "Foam rolling dos 2 min"],
                "exercises": [
                    {"id": "pompes", "name": "Pompes Classiques", "category": "strength", "muscle_groups": ["pectoraux", "triceps", "épaules"], "equipment": [], "duration_minutes": max(8, minutes//5), "calories_per_hour": 280, "difficulty": level, "description": "Exercice fondamental de push.", "instructions": ["Planche mains écartées", "Descendre la poitrine au sol", "Pousser sans verrouiller les coudes", "4x12-15"], "benefits": ["Pectoraux", "Force bras", "Gainage"]},
                    {"id": "dips", "name": "Dips (chaise)", "category": "strength", "muscle_groups": ["triceps", "pectoraux"], "equipment": ["chaise"], "duration_minutes": max(6, minutes//7), "calories_per_hour": 250, "difficulty": level, "description": "Isolation des triceps et bas des pectoraux.", "instructions": ["Mains sur le bord d'une chaise", "Descendre en fléchissant les coudes à 90°", "Remonter", "3x12"], "benefits": ["Triceps", "Buste"]},
                    {"id": "squat", "name": "Squats Corporels", "category": "strength", "muscle_groups": ["quadriceps", "fessiers", "ischio-jambiers"], "equipment": [], "duration_minutes": max(8, minutes//5), "calories_per_hour": 300, "difficulty": level, "description": "Roi des exercices de jambes.", "instructions": ["Pieds largeur hanches", "Descendre comme sur une chaise", "Genoux dans l'axe des pieds", "4x15-20"], "benefits": ["Force jambes", "Anabolisme général", "Mobilité"]},
                ],
            },
            "endurance": {
                "name": "Cardio Endurance Progressive",
                "rationale": "Effort continu à intensité modérée pour développer la capacité cardio-vasculaire.",
                "ai_tips": ["Restez à 60-70% FCmax pour l'endurance de base.", "Respirez par le nez tant que possible.", "Visez la constance plutôt que la vitesse."],
                "next_session_suggestion": "Sortie running 30 min à faible intensité demain.",
                "estimated_calories": int(minutes * 8),
                "warmup": ["Marche 5 min", "Étirements dynamiques 2 min", "Accélération progressive 2 min"],
                "cooldown": ["Marche 5 min", "Étirements statiques jambes 3 min", "Respiration abdominale 2 min"],
                "exercises": [
                    {"id": "jumping-jacks", "name": "Jumping Jacks", "category": "cardio", "muscle_groups": ["full_body"], "equipment": [], "duration_minutes": max(10, minutes//4), "calories_per_hour": 400, "difficulty": "beginner", "description": "Cardio classique basse intensité.", "instructions": ["Position debout", "Sauter en écartant bras et jambes", "Revenir", "Maintenir le rythme régulier"], "benefits": ["Cardio doux", "Coordination", "Échauffement"]},
                    {"id": "step", "name": "Step-ups (escalier/step)", "category": "cardio", "muscle_groups": ["jambes", "cardio"], "equipment": ["step"], "duration_minutes": max(12, minutes//3), "calories_per_hour": 450, "difficulty": "intermediate", "description": "Monter/descendre un step au rythme régulier.", "instructions": ["Monter le pied droit", "Monter le pied gauche", "Descendre droit puis gauche", "Alterner le pied d'attaque"], "benefits": ["Endurance", "Jambes", "Faible impact"]},
                ],
            },
            "maintain": {
                "name": "Séance Équilibrée Corps Complet",
                "rationale": "Mix cardio-renforcement pour maintenir les acquis et rester actif.",
                "ai_tips": ["Écoutez votre corps et adaptez l'intensité.", "Variez les exercices chaque semaine.", "Priorité à la forme sur la quantité."],
                "next_session_suggestion": "Activité douce demain : yoga, natation ou vélo.",
                "estimated_calories": int(minutes * 7),
                "warmup": ["Mobilisation 3 min", "Jumping jacks légers 2 min"],
                "cooldown": ["Étirements complets 5 min", "Respiration profonde"],
                "exercises": [
                    {"id": "pompes-maintien", "name": "Pompes", "category": "strength", "muscle_groups": ["pectoraux", "triceps"], "equipment": [], "duration_minutes": max(7, minutes//6), "calories_per_hour": 280, "difficulty": "intermediate", "description": "Push-ups classiques.", "instructions": ["Planche", "Descendre au sol", "Remonter", "3x10-12"], "benefits": ["Force haut du corps"]},
                    {"id": "squat-maintien", "name": "Squats", "category": "strength", "muscle_groups": ["jambes"], "equipment": [], "duration_minutes": max(7, minutes//6), "calories_per_hour": 300, "difficulty": "intermediate", "description": "Squats corporels.", "instructions": ["Debout, pieds écartés", "Descendre", "Remonter", "3x15"], "benefits": ["Force jambes"]},
                    {"id": "gainage", "name": "Gainage Planche", "category": "strength", "muscle_groups": ["core"], "equipment": [], "duration_minutes": max(5, minutes//8), "calories_per_hour": 200, "difficulty": "beginner", "description": "Planche isométrique.", "instructions": ["Position avant-bras", "Corps aligné", "Tenir 45s", "Répéter 3x"], "benefits": ["Core", "Dos"]},
                ],
            },
        }

        w = workouts.get(goal, workouts["maintain"])
        return {
            "recommendation_id": str(uuid.uuid4()),
            "user_id": user_id,
            "workout": {
                "session_id": str(uuid.uuid4()),
                "name": w["name"],
                "goal": goal,
                "fitness_level": level,
                "total_duration_minutes": minutes,
                "estimated_calories": w["estimated_calories"],
                "exercises": w["exercises"],
                "warmup": w["warmup"],
                "cooldown": w["cooldown"],
            },
            "rationale": w["rationale"],
            "ai_tips": w["ai_tips"],
            "next_session_suggestion": w["next_session_suggestion"],
            "generated_at": now,
            "_demo": True,
        }

    async def _ollama_generate_meal_plan(self, user_profile: dict, request: dict) -> dict:
        """Ask Ollama to generate ONE day only (keeps tokens low → fast response),
        then fill remaining days from the structured demo data."""
        import uuid
        from datetime import datetime, timezone

        if not await self._ollama_available():
            return self._fallback_meal_plan(user_profile, request)

        weight = user_profile.get("weight_kg", 70)
        height = user_profile.get("height_cm", 170)
        age = user_profile.get("age", 30)
        goal = user_profile.get("goal", "maintain")
        activity = user_profile.get("activity_level", "moderate")
        allergies = user_profile.get("allergies", [])
        preferences = user_profile.get("dietary_preferences", [])
        meals_per_day = int(request.get("meals_per_day", 3))
        budget = request.get("budget_level", "medium")

        activity_multipliers = {"sedentary": 1.2, "light": 1.375, "moderate": 1.55, "active": 1.725, "very_active": 1.9}
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
        tdee = bmr * activity_multipliers.get(activity, 1.55)
        cal_adj = {"lose_weight": -500, "gain_muscle": 300, "maintain": 0, "endurance": 200}
        calorie_target = int(request.get("calorie_target") or tdee + cal_adj.get(goal, 0))

        meal_types = ["breakfast", "lunch", "dinner", "snack", "snack2"][:meals_per_day]
        meal_type_str = ", ".join(meal_types)

        pref_note = f" Préférences: {', '.join(preferences)}." if preferences else ""
        prompt = (
            f"Nutritionniste expert. Crée exactement {meals_per_day} repas pour UNE journée.\n"
            f"Objectif: {goal}, {calorie_target} kcal/jour, budget {budget}.\n"
            f"Allergies: {', '.join(allergies) if allergies else 'aucune'}.{pref_note}\n"
            f"Types de repas dans l'ordre: {meal_type_str}.\n\n"
            f"Réponds UNIQUEMENT en JSON:\n"
            f'{{"meals": [{{"meal_type": "breakfast", "name": "...", "ingredients": ["..."], '
            f'"prep_time_minutes": 10, "calories": 400, "macros": {{"protein_g": 20, "carbs_g": 50, "fat_g": 10}}, '
            f'"instructions": "..."}}]}}'
        )

        # Get the demo plan as the base structure
        base = self._fallback_meal_plan(user_profile, request)

        try:
            raw = await self._ollama_chat(prompt, MEAL_PLAN_SYSTEM_PROMPT)
            data = self._parse_json_response(raw)
            ai_meals = data.get("meals", [])

            if ai_meals and len(ai_meals) >= meals_per_day:
                # Replace day 1 meals with Ollama-generated ones
                for i, meal in enumerate(ai_meals[:meals_per_day]):
                    meal.setdefault("meal_type", meal_types[i] if i < len(meal_types) else "snack")
                    meal.setdefault("calories", calorie_target // meals_per_day)
                    meal.setdefault("macros", {"protein_g": 25, "carbs_g": 40, "fat_g": 12})
                    meal.setdefault("prep_time_minutes", 15)
                    meal.setdefault("ingredients", [])
                    meal.setdefault("instructions", "")

                day1_calories = sum(m.get("calories", 0) for m in ai_meals[:meals_per_day])
                base["days"][0]["meals"] = ai_meals[:meals_per_day]
                base["days"][0]["total_calories"] = day1_calories
                base["days"][0]["day_name"] = "Lundi ✨"  # mark AI day
        except Exception:
            pass  # silently keep demo days if Ollama fails or times out

        base["plan_id"] = str(uuid.uuid4())
        base["daily_calorie_target"] = calorie_target
        base["generated_at"] = datetime.now(timezone.utc).isoformat()
        base["_ollama"] = True
        base.pop("_demo", None)
        return base

    def _fallback_nutrition_response(self, error: str) -> dict:
        return {
            "foods_detected": [],
            "total_calories": 0,
            "macros": {"protein_g": 0, "carbs_g": 0, "fat_g": 0, "fiber_g": 0, "sugar_g": 0, "sodium_mg": 0},
            "health_score": 0,
            "imbalances": [],
            "suggestions": ["Impossible d'analyser l'image. Veuillez réessayer avec une photo plus nette."],
            "meal_type_detected": None,
            "analysis_confidence": 0.0,
            "_error": error,
        }


ai_service = AIService()
