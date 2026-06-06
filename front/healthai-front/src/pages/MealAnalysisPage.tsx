import { useState, useRef, useCallback } from 'react'
import { useMutation } from '@tanstack/react-query'
import { nutritionApi } from '../api/nutrition'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import PremiumGate from '../components/ui/PremiumGate'
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis,
  ResponsiveContainer, Tooltip,
} from 'recharts'

interface FoodItem {
  name: string
  quantity_g: number
  calories: number
  macros: {
    protein_g: number
    carbs_g: number
    fat_g: number
    fiber_g: number
    sugar_g: number
    sodium_mg: number
  }
}

interface MealAnalysisResult {
  foods_detected: FoodItem[]
  total_calories: number
  macros: {
    protein_g: number
    carbs_g: number
    fat_g: number
    fiber_g: number
    sugar_g: number
    sodium_mg: number
  }
  health_score: number
  imbalances: string[]
  suggestions: string[]
  meal_type_detected?: string
  analysis_confidence?: number
  _demo?: boolean
  _ollama?: boolean
}

const MEAL_TYPE_LABELS: Record<string, string> = {
  breakfast: 'Petit-déjeuner',
  lunch: 'Déjeuner',
  dinner: 'Dîner',
  snack: 'Collation',
}

function HealthScoreRing({ score }: { score: number }) {
  const color =
    score >= 75 ? '#22c55e' : score >= 50 ? '#f59e0b' : '#ef4444'
  const label =
    score >= 75 ? 'Excellent' : score >= 60 ? 'Bon' : score >= 40 ? 'Moyen' : 'À améliorer'

  return (
    <div className="flex flex-col items-center gap-1">
      <div
        className="relative w-24 h-24 rounded-full flex items-center justify-center"
        style={{ background: `conic-gradient(${color} ${score * 3.6}deg, #e5e7eb ${score * 3.6}deg)` }}
      >
        <div className="absolute inset-2 bg-white rounded-full flex items-center justify-center">
          <span className="text-2xl font-bold" style={{ color }}>{score}</span>
        </div>
      </div>
      <span className="text-sm font-medium" style={{ color }}>{label}</span>
      <span className="text-xs text-gray-400">Score santé / 100</span>
    </div>
  )
}

function MacroRadar({ macros }: { macros: MealAnalysisResult['macros'] }) {
  const data = [
    { subject: 'Protéines', value: Math.min(macros.protein_g, 60), full: 60 },
    { subject: 'Glucides', value: Math.min(macros.carbs_g, 120), full: 120 },
    { subject: 'Lipides', value: Math.min(macros.fat_g, 50), full: 50 },
    { subject: 'Fibres', value: Math.min(macros.fiber_g, 30), full: 30 },
    { subject: 'Sucres', value: Math.min(macros.sugar_g, 50), full: 50 },
  ]
  return (
    <ResponsiveContainer width="100%" height={220}>
      <RadarChart data={data}>
        <PolarGrid />
        <PolarAngleAxis dataKey="subject" tick={{ fontSize: 11 }} />
        <Radar dataKey="value" stroke="#6366f1" fill="#6366f1" fillOpacity={0.35} />
        <Tooltip formatter={(v: number) => `${v}g`} />
      </RadarChart>
    </ResponsiveContainer>
  )
}

function DropZone({
  file,
  preview,
  onFile,
}: {
  file: File | null
  preview: string | null
  onFile: (f: File) => void
}) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [dragging, setDragging] = useState(false)

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      setDragging(false)
      const f = e.dataTransfer.files[0]
      if (f && f.type.startsWith('image/')) onFile(f)
    },
    [onFile]
  )

  return (
    <div
      role="button"
      tabIndex={0}
      aria-label="Zone d'upload — cliquez ou déposez une image"
      onClick={() => inputRef.current?.click()}
      onKeyDown={(e) => e.key === 'Enter' && inputRef.current?.click()}
      onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      className={`relative cursor-pointer border-2 border-dashed rounded-xl transition-all ${
        dragging
          ? 'border-primary-400 bg-primary-50'
          : 'border-gray-300 bg-gray-50 hover:border-primary-300 hover:bg-gray-100'
      }`}
    >
      {preview ? (
        <div className="relative">
          <img
            src={preview}
            alt="Aperçu du repas"
            className="w-full max-h-72 object-cover rounded-xl"
          />
          <div className="absolute inset-0 bg-black/40 rounded-xl flex items-center justify-center opacity-0 hover:opacity-100 transition-opacity">
            <span className="text-white text-sm font-medium">Changer l'image</span>
          </div>
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center py-14 px-4 text-center gap-3">
          <span className="text-5xl">📸</span>
          <p className="font-semibold text-gray-700">Déposez une photo de votre repas</p>
          <p className="text-sm text-gray-400">ou cliquez pour parcourir (JPEG, PNG, WebP — max 10 MB)</p>
        </div>
      )}
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        className="hidden"
        aria-hidden="true"
        onChange={(e) => {
          const f = e.target.files?.[0]
          if (f) onFile(f)
        }}
      />
    </div>
  )
}

export default function MealAnalysisPage() {
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const [result, setResult] = useState<MealAnalysisResult | null>(null)

  function handleFile(f: File) {
    setFile(f)
    setPreview(URL.createObjectURL(f))
    setResult(null)
  }

  const analyzeMutation = useMutation({
    mutationFn: () => nutritionApi.analyzeWithAI(file!),
    onSuccess: (data) => setResult(data),
  })

  const totalMacroG = result
    ? result.macros.protein_g + result.macros.carbs_g + result.macros.fat_g
    : 0

  return (
    <PremiumGate feature="L'analyse de photos de repas par IA">
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Analyse de repas par IA</h1>
            <p className="text-sm text-gray-500 mt-0.5">
              Photographiez votre repas — l'IA identifie les aliments et calcule vos macros
            </p>
          </div>
          {result?._ollama && (
            <span className="text-xs px-3 py-1 bg-green-100 text-green-700 rounded-full font-medium">
              🦙 IA locale — Ollama
            </span>
          )}
          {result?._demo && !result?._ollama && (
            <span className="text-xs px-3 py-1 bg-amber-100 text-amber-700 rounded-full font-medium">
              Mode démo — sans clé IA
            </span>
          )}
        </div>

        <Card>
          <DropZone file={file} preview={preview} onFile={handleFile} />
          <div className="mt-4 flex items-center gap-3">
            <Button
              onClick={() => analyzeMutation.mutate()}
              loading={analyzeMutation.isPending}
              disabled={!file}
              size="lg"
            >
              {analyzeMutation.isPending ? 'Analyse en cours…' : '🔍 Analyser ce repas'}
            </Button>
            {file && (
              <button
                type="button"
                onClick={() => { setFile(null); setPreview(null); setResult(null) }}
                className="text-sm text-gray-400 hover:text-gray-600"
              >
                Effacer
              </button>
            )}
          </div>
          {analyzeMutation.isError && (
            <p role="alert" className="text-sm text-red-600 mt-2">
              Erreur lors de l'analyse — vérifiez votre connexion.
            </p>
          )}
        </Card>

        {result && (
          <div className="space-y-4" aria-live="polite">
            {/* Header: score + meal type + confidence */}
            <Card>
              <div className="flex flex-wrap items-center gap-6">
                <HealthScoreRing score={result.health_score} />
                <div className="flex-1 space-y-2">
                  <div className="flex flex-wrap gap-2">
                    {result.meal_type_detected && (
                      <span className="px-3 py-1 bg-primary-100 text-primary-700 rounded-full text-sm font-medium">
                        {MEAL_TYPE_LABELS[result.meal_type_detected] ?? result.meal_type_detected}
                      </span>
                    )}
                    {result.analysis_confidence !== undefined && (
                      <span className="px-3 py-1 bg-gray-100 text-gray-600 rounded-full text-sm">
                        Confiance : {Math.round(result.analysis_confidence * 100)}%
                      </span>
                    )}
                  </div>
                  <p className="text-3xl font-bold text-gray-900">
                    {Math.round(result.total_calories)} <span className="text-lg font-normal text-gray-500">kcal</span>
                  </p>
                  <div className="flex gap-4 text-sm">
                    <span><span className="font-semibold text-blue-600">{result.macros.protein_g}g</span> prot.</span>
                    <span><span className="font-semibold text-amber-500">{result.macros.carbs_g}g</span> gluc.</span>
                    <span><span className="font-semibold text-red-400">{result.macros.fat_g}g</span> lip.</span>
                    <span><span className="font-semibold text-green-600">{result.macros.fiber_g}g</span> fibres</span>
                  </div>
                  {/* Macro bar */}
                  {totalMacroG > 0 && (
                    <div className="flex rounded-full overflow-hidden h-2 mt-1">
                      <div style={{ width: `${(result.macros.protein_g / totalMacroG) * 100}%` }} className="bg-blue-400" />
                      <div style={{ width: `${(result.macros.carbs_g / totalMacroG) * 100}%` }} className="bg-amber-400" />
                      <div style={{ width: `${(result.macros.fat_g / totalMacroG) * 100}%` }} className="bg-red-400" />
                    </div>
                  )}
                </div>
              </div>
            </Card>

            {/* Two column: foods list + radar chart */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Card>
                <h3 className="font-semibold text-gray-900 mb-3">Aliments détectés</h3>
                <ul className="space-y-2">
                  {result.foods_detected.map((food, i) => (
                    <li key={i} className="flex items-center justify-between py-1.5 border-b border-gray-50 last:border-0">
                      <div>
                        <p className="text-sm font-medium text-gray-800">{food.name}</p>
                        <p className="text-xs text-gray-400">{food.quantity_g}g</p>
                      </div>
                      <span className="text-sm font-semibold text-gray-700">{food.calories} kcal</span>
                    </li>
                  ))}
                </ul>
              </Card>

              <Card>
                <h3 className="font-semibold text-gray-900 mb-1">Profil nutritionnel</h3>
                <MacroRadar macros={result.macros} />
                <div className="flex justify-center gap-3 text-xs text-gray-500 mt-1">
                  <span>Na: {result.macros.sodium_mg}mg</span>
                  <span>·</span>
                  <span>Sucres: {result.macros.sugar_g}g</span>
                </div>
              </Card>
            </div>

            {/* Imbalances + suggestions */}
            {result.imbalances.length > 0 && (
              <Card>
                <h3 className="font-semibold text-gray-900 mb-3">⚠️ Déséquilibres détectés</h3>
                <div className="flex flex-wrap gap-2">
                  {result.imbalances.map((im, i) => (
                    <span key={i} className="px-3 py-1 bg-orange-50 text-orange-700 border border-orange-200 rounded-full text-sm">
                      {im}
                    </span>
                  ))}
                </div>
              </Card>
            )}

            {result.suggestions.length > 0 && (
              <Card>
                <h3 className="font-semibold text-gray-900 mb-3">💡 Suggestions d'amélioration</h3>
                <ul className="space-y-2">
                  {result.suggestions.map((s, i) => (
                    <li key={i} className="flex gap-3 text-sm text-gray-700">
                      <span className="text-primary-500 mt-0.5 shrink-0">→</span>
                      {s}
                    </li>
                  ))}
                </ul>
              </Card>
            )}
          </div>
        )}
      </div>
    </PremiumGate>
  )
}
