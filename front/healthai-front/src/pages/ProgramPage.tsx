import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { nutritionApi } from '../api/nutrition'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import Select from '../components/ui/Select'
import PremiumGate from '../components/ui/PremiumGate'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip as ReTooltip, ResponsiveContainer, Cell,
} from 'recharts'

const GOAL_OPTIONS = [
  { value: 'maintain', label: 'Maintien' },
  { value: 'lose_weight', label: 'Perte de poids' },
  { value: 'gain_muscle', label: 'Prise de masse' },
  { value: 'endurance', label: 'Endurance' },
]
const DURATION_OPTIONS = [
  { value: '3', label: '3 jours' },
  { value: '5', label: '5 jours' },
  { value: '7', label: '7 jours' },
  { value: '14', label: '14 jours' },
]
const MEAL_COUNT_OPTIONS = [
  { value: '3', label: '3 repas/jour' },
  { value: '4', label: '4 repas/jour' },
  { value: '5', label: '5 repas/jour' },
]
const BUDGET_OPTIONS = [
  { value: 'low', label: 'Économique' },
  { value: 'medium', label: 'Moyen' },
  { value: 'high', label: 'Premium' },
]

interface Meal {
  meal_type: string
  name: string
  ingredients: string[]
  prep_time_minutes: number
  calories: number
  instructions: string
  macros: { protein_g: number; carbs_g: number; fat_g: number }
}

interface MealPlan {
  plan_id: string
  goal: string
  daily_calorie_target: number
  days: {
    day: number
    day_name: string
    total_calories: number
    meals: Meal[]
  }[]
  shopping_list: string[]
  nutritional_summary: { avg_daily_calories: number; avg_protein_g: number; avg_carbs_g: number; avg_fat_g: number }
  _demo?: boolean
  _ollama?: boolean
}

const MEAL_TYPE_CONFIG: Record<string, { label: string; color: string }> = {
  breakfast: { label: 'Petit-déjeuner', color: 'bg-amber-100 text-amber-800' },
  lunch:     { label: 'Déjeuner',        color: 'bg-green-100 text-green-800' },
  dinner:    { label: 'Dîner',           color: 'bg-blue-100 text-blue-800' },
  snack:     { label: 'Collation',       color: 'bg-purple-100 text-purple-800' },
}

const GOAL_LABELS: Record<string, string> = {
  maintain:     '⚖️ Maintien',
  lose_weight:  '🔥 Perte de poids',
  gain_muscle:  '💪 Prise de masse',
  endurance:    '🏃 Endurance',
}

function MacroBar({ protein, carbs, fat }: { protein: number; carbs: number; fat: number }) {
  const total = protein * 4 + carbs * 4 + fat * 9
  if (total === 0) return null
  const pPct = Math.round((protein * 4 / total) * 100)
  const cPct = Math.round((carbs * 4 / total) * 100)
  const fPct = 100 - pPct - cPct

  return (
    <div className="mt-2">
      <div className="flex rounded-full overflow-hidden h-2">
        <div style={{ width: `${pPct}%` }} className="bg-blue-400" title={`Protéines ${pPct}%`} />
        <div style={{ width: `${cPct}%` }} className="bg-amber-400" title={`Glucides ${cPct}%`} />
        <div style={{ width: `${fPct}%` }} className="bg-red-400" title={`Lipides ${fPct}%`} />
      </div>
      <div className="flex gap-3 mt-1 text-xs text-gray-500">
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-blue-400 inline-block" />P {protein}g</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-amber-400 inline-block" />G {carbs}g</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-400 inline-block" />L {fat}g</span>
      </div>
    </div>
  )
}

function MealCard({ meal }: { meal: Meal }) {
  const [open, setOpen] = useState(false)
  const cfg = MEAL_TYPE_CONFIG[meal.meal_type] ?? { label: meal.meal_type, color: 'bg-gray-100 text-gray-700' }

  return (
    <Card padding="sm">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${cfg.color}`}>
            {cfg.label}
          </span>
          <h4 className="font-semibold text-gray-900 mt-1 leading-tight">{meal.name}</h4>
          <MacroBar
            protein={meal.macros.protein_g}
            carbs={meal.macros.carbs_g}
            fat={meal.macros.fat_g}
          />
        </div>
        <div className="text-right shrink-0">
          <p className="text-base font-bold text-primary-600">{meal.calories} kcal</p>
          <p className="text-xs text-gray-400">{meal.prep_time_minutes} min</p>
        </div>
      </div>

      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="mt-3 text-xs text-primary-600 hover:underline flex items-center gap-1"
        aria-expanded={open ? 'true' : 'false'}
      >
        {open ? '▲' : '▼'} Ingrédients & préparation
      </button>

      {open && (
        <div className="mt-2 space-y-2">
          <ul className="space-y-0.5">
            {meal.ingredients.map((ing, i) => (
              <li key={i} className="text-xs text-gray-600 flex gap-1.5">
                <span className="text-primary-400 mt-0.5">•</span>
                {ing}
              </li>
            ))}
          </ul>
          <p className="text-xs text-gray-500 italic border-t border-gray-100 pt-2">{meal.instructions}</p>
        </div>
      )}
    </Card>
  )
}

export default function ProgramPage() {
  const [config, setConfig] = useState({ goal: 'maintain', duration_days: '7', meals_per_day: '3', budget_level: 'medium' })
  const [plan, setPlan] = useState<MealPlan | null>(null)
  const [activeDay, setActiveDay] = useState(0)
  const [showShopping, setShowShopping] = useState(false)

  const planMutation = useMutation({
    mutationFn: () => nutritionApi.generateMealPlan({
      goal: config.goal,
      duration_days: Number(config.duration_days),
      meals_per_day: Number(config.meals_per_day),
      budget_level: config.budget_level,
    }),
    onSuccess: (data: MealPlan) => { setPlan(data); setActiveDay(0) },
  })

  function set(field: string) {
    return (e: React.ChangeEvent<HTMLSelectElement>) =>
      setConfig((p) => ({ ...p, [field]: e.target.value }))
  }

  const activeData = plan?.days[activeDay]

  return (
    <PremiumGate feature="La génération de programmes alimentaires par IA">
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Programme alimentaire</h1>
        {plan?._ollama && (
          <span className="text-xs px-3 py-1 bg-green-100 text-green-700 rounded-full font-medium">
            🦙 IA locale — Ollama
          </span>
        )}
        {plan?._demo && !plan?._ollama && (
          <span className="text-xs px-3 py-1 bg-amber-100 text-amber-700 rounded-full font-medium">
            Mode démo — sans clé IA
          </span>
        )}
      </div>

      <Card>
        <h2 className="text-base font-semibold text-gray-900 mb-4">Générer un plan personnalisé par IA</h2>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
          <Select label="Objectif" value={config.goal} onChange={set('goal')} options={GOAL_OPTIONS} />
          <Select label="Durée" value={config.duration_days} onChange={set('duration_days')} options={DURATION_OPTIONS} />
          <Select label="Repas par jour" value={config.meals_per_day} onChange={set('meals_per_day')} options={MEAL_COUNT_OPTIONS} />
          <Select label="Budget" value={config.budget_level} onChange={set('budget_level')} options={BUDGET_OPTIONS} />
        </div>
        <Button onClick={() => planMutation.mutate()} loading={planMutation.isPending} size="lg">
          {planMutation.isPending ? 'Génération en cours…' : '🍽️ Générer mon programme IA'}
        </Button>
        {planMutation.isError && (
          <p role="alert" className="text-sm text-red-600 mt-2">Erreur lors de la génération — vérifiez que vous êtes connecté.</p>
        )}
      </Card>

      {plan && (
        <div className="space-y-4" aria-live="polite">
          {/* Goal + summary stats */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {[
              { label: 'Objectif', value: GOAL_LABELS[plan.goal] ?? plan.goal },
              { label: 'Calories/jour', value: `${Math.round(plan.daily_calorie_target)} kcal` },
              { label: 'Protéines moy.', value: `${Math.round(plan.nutritional_summary.avg_protein_g)}g` },
              { label: 'Glucides moy.', value: `${Math.round(plan.nutritional_summary.avg_carbs_g)}g` },
            ].map((s) => (
              <Card key={s.label} padding="sm">
                <p className="text-lg font-bold text-primary-600 leading-tight">{s.value}</p>
                <p className="text-xs text-gray-500 mt-0.5">{s.label}</p>
              </Card>
            ))}
          </div>

          {/* Macro summary bar */}
          <Card padding="sm">
            <p className="text-xs font-medium text-gray-700 mb-2">Répartition macronutriments moyenne</p>
            <MacroBar
              protein={plan.nutritional_summary.avg_protein_g}
              carbs={plan.nutritional_summary.avg_carbs_g}
              fat={plan.nutritional_summary.avg_fat_g}
            />
          </Card>

          {/* Bar chart — calories par jour */}
          <Card>
            <h3 className="font-semibold text-gray-900 mb-1">Calories par jour</h3>
            <p className="text-xs text-gray-400 mb-3">Apport calorique total sur la semaine</p>
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={plan.days.map((d) => ({ name: d.day_name.slice(0, 3), calories: d.total_calories }))}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
                <XAxis dataKey="name" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 11 }} axisLine={false} tickLine={false} width={40} />
                <ReTooltip
                  formatter={(v: number) => [`${Math.round(v)} kcal`, 'Calories']}
                  contentStyle={{ fontSize: 12, borderRadius: 8 }}
                />
                <Bar dataKey="calories" radius={[4, 4, 0, 0]}>
                  {plan.days.map((_, i) => (
                    <Cell
                      key={i}
                      fill={i === activeDay ? '#6366f1' : '#c7d2fe'}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </Card>

          {/* Day tabs */}
          <div className="flex gap-2 overflow-x-auto pb-1" role="tablist">
            {plan.days.map((day, i) => (
              <button
                key={day.day}
                type="button"
                role="tab"
                aria-selected={activeDay === i ? 'true' : 'false'}
                onClick={() => setActiveDay(i)}
                className={`flex-shrink-0 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  activeDay === i
                    ? 'bg-primary-600 text-white'
                    : 'bg-white border border-gray-200 text-gray-600 hover:bg-gray-50'
                }`}
              >
                {day.day_name}
              </button>
            ))}
          </div>

          {/* Day content */}
          {activeData && (
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <h3 className="font-semibold text-gray-900">{activeData.day_name}</h3>
                <span className="text-sm font-medium text-gray-600 bg-gray-100 px-3 py-1 rounded-full">
                  {Math.round(activeData.total_calories)} kcal
                </span>
              </div>

              {activeData.meals.map((meal, mi) => (
                <MealCard key={mi} meal={meal} />
              ))}
            </div>
          )}

          {/* Shopping list */}
          <Card>
            <button
              type="button"
              onClick={() => setShowShopping((v) => !v)}
              className="flex items-center justify-between w-full"
              aria-expanded={showShopping ? 'true' : 'false'}
            >
              <h3 className="font-semibold text-gray-900">
                🛒 Liste de courses <span className="text-gray-400 font-normal text-sm">({plan.shopping_list.length} articles)</span>
              </h3>
              <span aria-hidden="true" className="text-gray-400">{showShopping ? '▲' : '▼'}</span>
            </button>
            {showShopping && (
              <ul className="mt-4 grid grid-cols-2 sm:grid-cols-3 gap-x-4 gap-y-1.5">
                {plan.shopping_list.map((item, i) => (
                  <li key={i} className="text-sm text-gray-700 flex gap-2 items-start">
                    <span className="text-primary-400 mt-0.5" aria-hidden="true">•</span>
                    {item}
                  </li>
                ))}
              </ul>
            )}
          </Card>
        </div>
      )}
    </div>
    </PremiumGate>
  )
}
