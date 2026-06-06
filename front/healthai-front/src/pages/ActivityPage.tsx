import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { activityApi, Recommendation, Exercise } from '../api/activity'
import { useAuth } from '../auth/AuthContext'
import { usersApi } from '../api/users'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import Select from '../components/ui/Select'
import PremiumGate from '../components/ui/PremiumGate'
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  ResponsiveContainer, Tooltip as ReTooltip, Legend,
} from 'recharts'

const FITNESS_LEVELS = [
  { value: 'beginner', label: 'Débutant' },
  { value: 'intermediate', label: 'Intermédiaire' },
  { value: 'advanced', label: 'Avancé' },
]

const GOAL_OPTIONS = [
  { value: 'lose_weight', label: 'Perdre du poids' },
  { value: 'gain_muscle', label: 'Prendre de la masse' },
  { value: 'maintain', label: 'Maintenir' },
  { value: 'endurance', label: 'Endurance' },
]

const DURATION_OPTIONS = [
  { value: '20', label: '20 minutes' },
  { value: '30', label: '30 minutes' },
  { value: '45', label: '45 minutes' },
  { value: '60', label: '1 heure' },
  { value: '90', label: '1h30' },
]

// Séances de démonstration par objectif
const DEMO_WORKOUTS: Record<string, Recommendation> = {
  lose_weight: {
    recommendation_id: 'demo-lw',
    user_id: 0,
    rationale: 'Séance cardio-HIIT intense pour maximiser la dépense calorique et activer le métabolisme.',
    ai_tips: [
      'Maintenez une fréquence cardiaque à 70-80% de votre FCmax pendant les blocs cardio.',
      'Hydratez-vous régulièrement — 500ml minimum pendant la séance.',
      'Enchaînez les exercices sans pause pour optimiser la combustion des graisses.',
    ],
    next_session_suggestion: 'Demain : séance de renforcement musculaire léger + stretching 30 min.',
    generated_at: new Date().toISOString(),
    workout: {
      session_id: 'demo-lw-session',
      name: 'Circuit Cardio-HIIT Brûle-Graisses',
      goal: 'lose_weight',
      fitness_level: 'intermediate',
      total_duration_minutes: 45,
      estimated_calories: 420,
      warmup: ['Marche rapide 3 min', 'Rotations des épaules 30s', 'Fentes dynamiques 1 min', 'Jumping jacks légers 1 min'],
      cooldown: ['Étirement ischio-jambiers 45s', 'Pigeon yoga 30s chaque jambe', 'Respiration profonde 1 min'],
      exercises: [
        { id: 'burpee', name: 'Burpees', category: 'hiit', muscle_groups: ['full_body'], equipment: [],
          duration_minutes: 8, calories_per_hour: 600, difficulty: 'intermediate',
          description: 'Exercice complet combinant squat, planche et saut vertical.',
          instructions: ['Position debout', 'Descendre en squat, mains au sol', 'Sauter les pieds en arrière en planche', 'Faire une pompe', 'Ramener les pieds, se lever et sauter'],
          benefits: ['Brûle ~10 kcal/min', 'Renforce tout le corps', 'Améliore la cardio'] },
        { id: 'mountain-climber', name: 'Mountain Climbers', category: 'cardio', muscle_groups: ['core', 'épaules'], equipment: [],
          duration_minutes: 6, calories_per_hour: 500, difficulty: 'intermediate',
          description: 'Simulation de grimpe en position de planche — excellent pour le cardio et le gainage.',
          instructions: ['Position de planche bras tendus', 'Ramener alternativement chaque genou vers la poitrine', 'Maintenir le rythme rapide', '3 séries de 30 répétitions'],
          benefits: ['Cardio intense', 'Gainage abdominal', 'Coordination'] },
        { id: 'jump-squat', name: 'Squats Sautés', category: 'hiit', muscle_groups: ['quadriceps', 'fessiers'], equipment: [],
          duration_minutes: 7, calories_per_hour: 550, difficulty: 'intermediate',
          description: 'Squat classique suivi d\'un saut explosif pour un effort cardio maximal.',
          instructions: ['Pieds écartés largeur des épaules', 'Descendre en squat profond', 'Exploser vers le haut', 'Atterrir en douceur, genoux légèrement fléchis', '4 séries de 15 reps'],
          benefits: ['Tonifie les jambes', 'Brûle beaucoup de calories', 'Force explosive'] },
        { id: 'planche', name: 'Gainage Planche', category: 'strength', muscle_groups: ['core', 'dos'], equipment: [],
          duration_minutes: 5, calories_per_hour: 250, difficulty: 'beginner',
          description: 'Exercice de gainage isométrique fondamental pour renforcer le centre du corps.',
          instructions: ['Position de planche sur les avant-bras', 'Corps aligné tête-talons', 'Contracter abdos et fessiers', 'Tenir 45-60 secondes', 'Répéter 3 fois'],
          benefits: ['Core solide', 'Protection du dos', 'Stabilité'] },
      ],
    },
  },
  gain_muscle: {
    recommendation_id: 'demo-gm',
    user_id: 0,
    rationale: 'Séance de force progressive axée sur les grands groupes musculaires avec temps de récupération optimaux.',
    ai_tips: [
      'Prenez 90 secondes de repos entre chaque série pour maximiser la récupération musculaire.',
      'Privilégiez une alimentation riche en protéines dans les 30 minutes suivant la séance.',
      'Augmentez les charges de 2,5 kg dès que vous maîtrisez toutes les répétitions.',
    ],
    next_session_suggestion: 'J+2 : séance bas du corps — squat, deadlift, leg press.',
    generated_at: new Date().toISOString(),
    workout: {
      session_id: 'demo-gm-session',
      name: 'Force Haut du Corps — Push Day',
      goal: 'gain_muscle',
      fitness_level: 'intermediate',
      total_duration_minutes: 60,
      estimated_calories: 380,
      warmup: ['Rotations bras 2 min', 'Bandes élastiques épaules 1 min', 'Pompes légères 10 reps', 'Mobil. thoracique 1 min'],
      cooldown: ['Étirement pectoraux au mur 45s', 'Étirement triceps 30s chaque bras', 'Foam roller dos 2 min'],
      exercises: [
        { id: 'bench-press', name: 'Développé Couché', category: 'strength', muscle_groups: ['pectoraux', 'triceps', 'épaules'], equipment: ['banc', 'barre'],
          duration_minutes: 15, calories_per_hour: 350, difficulty: 'intermediate',
          description: 'Exercice roi du haut du corps pour développer les pectoraux.',
          instructions: ['Allongé sur le banc, pieds à plat au sol', 'Prise légèrement plus large que les épaules', 'Descendre la barre jusqu\'à la poitrine', 'Pousser en expirant', '4 séries × 8-10 reps'],
          benefits: ['Développe les pectoraux', 'Force haut du corps', 'Stabilité des épaules'] },
        { id: 'ohp', name: 'Développé Militaire', category: 'strength', muscle_groups: ['épaules', 'triceps'], equipment: ['barre'],
          duration_minutes: 12, calories_per_hour: 320, difficulty: 'intermediate',
          description: 'Exercice de base pour des épaules larges et solides.',
          instructions: ['Debout, pieds écartés', 'Barre au niveau des clavicules', 'Pousser la barre au-dessus de la tête', 'Verrouiller les coudes en haut', '4 séries × 8 reps'],
          benefits: ['Épaules rondes', 'Force de poussée', 'Stabilité du tronc'] },
        { id: 'dips', name: 'Dips aux Barres Parallèles', category: 'strength', muscle_groups: ['triceps', 'pectoraux'], equipment: ['barres parallèles'],
          duration_minutes: 10, calories_per_hour: 400, difficulty: 'intermediate',
          description: 'Exercice au poids du corps excellent pour les triceps.',
          instructions: ['Saisir les barres, bras tendus', 'Descendre jusqu\'à 90° aux coudes', 'Remonter en contractant les triceps', 'Légèrement penché en avant = pectoraux', '3 séries × 10-12 reps'],
          benefits: ['Masse triceps', 'Force fonctionnelle', 'Pas de matériel coûteux'] },
      ],
    },
  },
  maintain: {
    recommendation_id: 'demo-mt',
    user_id: 0,
    rationale: 'Séance équilibrée combinant cardio modéré et renforcement pour maintenir forme et vitalité.',
    ai_tips: [
      'Restez dans une zone de confort — vous devez pouvoir parler sans perdre le souffle.',
      'La régularité prime sur l\'intensité pour le maintien de forme.',
      'Variez les activités chaque semaine pour stimuler différents groupes musculaires.',
    ],
    next_session_suggestion: 'Demain : 30 min de marche active ou natation légère.',
    generated_at: new Date().toISOString(),
    workout: {
      session_id: 'demo-mt-session',
      name: 'Séance Équilibre & Bien-être',
      goal: 'maintain',
      fitness_level: 'beginner',
      total_duration_minutes: 40,
      estimated_calories: 280,
      warmup: ['Marche sur place 2 min', 'Cercles des hanches 1 min', 'Étirements dynamiques 2 min'],
      cooldown: ['Yoga chat-vache 1 min', 'Posture enfant 45s', 'Respiration abdominale 2 min'],
      exercises: [
        { id: 'marche-rapide', name: 'Marche Rapide / Jogging Léger', category: 'cardio', muscle_groups: ['jambes', 'cardio'], equipment: [],
          duration_minutes: 15, calories_per_hour: 350, difficulty: 'beginner',
          description: 'Cardio doux idéal pour maintenir le système cardiovasculaire.',
          instructions: ['Marcher à rythme soutenu 5 min', 'Accélérer légèrement 5 min', 'Retour marche normale 5 min', 'Maintenir une posture droite'],
          benefits: ['Cardio sans impact', 'Brûle des calories', 'Améliore l\'endurance de base'] },
        { id: 'pompes-genoux', name: 'Pompes (variante facile)', category: 'strength', muscle_groups: ['pectoraux', 'bras'], equipment: [],
          duration_minutes: 8, calories_per_hour: 300, difficulty: 'beginner',
          description: 'Renforcement haut du corps adapté à tous les niveaux.',
          instructions: ['Position pompe sur les genoux', 'Descendre jusqu\'au sol', 'Remonter bras tendus', '3 séries × 12 répétitions', 'Repos 1 min entre séries'],
          benefits: ['Force haut du corps', 'Accessible à tous', 'Pas d\'équipement'] },
        { id: 'gainage-lateral', name: 'Gainage Latéral', category: 'strength', muscle_groups: ['obliques', 'core'], equipment: [],
          duration_minutes: 6, calories_per_hour: 200, difficulty: 'beginner',
          description: 'Renforce les muscles latéraux du tronc pour une meilleure posture.',
          instructions: ['Sur le côté, appui sur un avant-bras', 'Soulever les hanches', 'Corps aligné', 'Tenir 30 secondes chaque côté', '3 passages'],
          benefits: ['Posture', 'Équilibre musculaire', 'Protection du dos'] },
      ],
    },
  },
  endurance: {
    recommendation_id: 'demo-end',
    user_id: 0,
    rationale: 'Séance d\'endurance progressive visant à développer le VO2max et la capacité aérobie.',
    ai_tips: [
      'Courez à un rythme où vous pouvez tenir une conversation — c\'est votre zone aérobie optimale.',
      'Les longues sorties à faible intensité sont plus efficaces que le sprint pour l\'endurance.',
      'Incorporez une sortie longue de 60-90 min chaque semaine.',
    ],
    next_session_suggestion: 'J+2 : interval training 6×400m à 85% FCmax.',
    generated_at: new Date().toISOString(),
    workout: {
      session_id: 'demo-end-session',
      name: 'Run Progressif — Base Endurance',
      goal: 'endurance',
      fitness_level: 'intermediate',
      total_duration_minutes: 50,
      estimated_calories: 450,
      warmup: ['Marche 5 min', 'Foulées progressives 3×100m', 'Étirements dynamiques jambes 2 min'],
      cooldown: ['Marche récup 5 min', 'Étirements mollets 45s', 'Étirements quadriceps 30s chaque jambe', 'Foam roller IT band 2 min'],
      exercises: [
        { id: 'run-base', name: 'Course Aérobie Base', category: 'cardio', muscle_groups: ['jambes', 'cardio'], equipment: [],
          duration_minutes: 25, calories_per_hour: 540, difficulty: 'intermediate',
          description: 'Course continue à allure modérée pour construire la base aérobie.',
          instructions: ['Rythme conversationnel (pouvez parler)', 'Foulée naturelle, milieu du pied', 'Bras décontractés à 90°', 'Respiration nasale si possible', 'Allure stable sur la durée'],
          benefits: ['Développe le VO2max', 'Améliore l\'économie de course', 'Santé cardiovasculaire'] },
        { id: 'intervals', name: 'Intervalles 6×2 minutes', category: 'cardio', muscle_groups: ['jambes', 'cardio'], equipment: [],
          duration_minutes: 18, calories_per_hour: 650, difficulty: 'intermediate',
          description: 'Accélérations courtes pour repousser le seuil lactique.',
          instructions: ['2 min à 80-85% FCmax', '1 min récupération active (trot)', 'Répéter 6 fois', 'Maintenir une technique correcte même fatigué'],
          benefits: ['Hausse le seuil lactique', 'Améliore la vitesse', 'Variété dans l\'entraînement'] },
      ],
    },
  },
}

export default function ActivityPage() {
  const { user } = useAuth()
  const userId = user?.id ?? 0
  const { data: profile } = useQuery({ queryKey: ['profile'], queryFn: usersApi.getProfile })

  const [params, setParams] = useState({
    goal: profile?.goal || 'maintain',
    fitness_level: 'intermediate',
    available_minutes: '45',
  })
  const [recommendation, setRecommendation] = useState<Recommendation | null>(null)
  const [isDemoMode, setIsDemoMode] = useState(false)
  const [logged, setLogged] = useState<Set<string>>(new Set())

  const recMutation = useMutation({
    mutationFn: () =>
      activityApi.getRecommendation({
        user_id: userId,
        goal: params.goal,
        fitness_level: params.fitness_level,
        available_minutes: Number(params.available_minutes),
        equipment: [],
        restrictions: [],
        preferred_categories: [],
      }),
    onSuccess: (data) => { setRecommendation(data); setIsDemoMode(!!data._demo) },
    onError: () => {
      const demo = DEMO_WORKOUTS[params.goal] || DEMO_WORKOUTS.maintain
      setRecommendation({ ...demo, user_id: userId })
      setIsDemoMode(true)
    },
  })

  const logMutation = useMutation({
    mutationFn: (ex: Exercise) =>
      activityApi.logActivity(userId, {
        exercise_id: ex.id,
        exercise_name: ex.name,
        duration_minutes: ex.duration_minutes,
        perceived_effort: 6,
      }),
    onSuccess: (_, ex) => setLogged((prev) => new Set([...prev, ex.id])),
    onError: (_, ex) => setLogged((prev) => new Set([...prev, ex.id])), // mark done anyway in demo mode
  })

  function set(field: string) {
    return (e: React.ChangeEvent<HTMLSelectElement>) =>
      setParams((p) => ({ ...p, [field]: e.target.value }))
  }

  const categoryLabels: Record<string, string> = {
    cardio: 'Cardio', strength: 'Force', hiit: 'HIIT',
    flexibility: 'Flexibilité', yoga: 'Yoga', sports: 'Sports',
  }
  const categoryColors: Record<string, string> = {
    cardio: 'bg-blue-100 text-blue-700',
    strength: 'bg-purple-100 text-purple-700',
    hiit: 'bg-red-100 text-red-700',
    flexibility: 'bg-green-100 text-green-700',
    yoga: 'bg-teal-100 text-teal-700',
  }
  const difficultyColors: Record<string, string> = {
    beginner: 'bg-green-100 text-green-700',
    intermediate: 'bg-yellow-100 text-yellow-700',
    advanced: 'bg-red-100 text-red-700',
  }

  // Build radar data from exercises
  function buildRadarData(exercises: Exercise[]) {
    const scores: Record<string, number> = {}
    for (const ex of exercises) {
      const cat = categoryLabels[ex.category] ?? ex.category
      scores[cat] = (scores[cat] ?? 0) + ex.duration_minutes
    }
    return Object.entries(scores).map(([subject, minutes]) => ({ subject, minutes }))
  }

  return (
    <PremiumGate feature="Les séances IA personnalisées">
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Activité physique</h1>
        {recommendation?._ollama && (
          <span className="text-xs px-3 py-1 bg-green-100 text-green-700 rounded-full font-medium">
            🦙 IA locale — Ollama
          </span>
        )}
        {isDemoMode && !recommendation?._ollama && (
          <span className="text-xs px-3 py-1 bg-amber-100 text-amber-700 rounded-full font-medium">
            Mode démo
          </span>
        )}
      </div>

      {/* Config card */}
      <Card>
        <h2 className="text-base font-semibold text-gray-900 mb-4">Générer une séance personnalisée par IA</h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-4">
          <Select label="Objectif" value={params.goal} onChange={set('goal')} options={GOAL_OPTIONS} />
          <Select label="Niveau" value={params.fitness_level} onChange={set('fitness_level')} options={FITNESS_LEVELS} />
          <Select label="Durée disponible" value={params.available_minutes} onChange={set('available_minutes')} options={DURATION_OPTIONS} />
        </div>
        <Button onClick={() => { setLogged(new Set()); recMutation.mutate() }} loading={recMutation.isPending} size="lg">
          {recMutation.isPending ? 'Génération en cours…' : '🏋️ Générer ma séance IA'}
        </Button>
      </Card>

      {/* Result */}
      {recommendation && (
        <div className="space-y-4" aria-live="polite">
          {/* Header stats */}
          <Card>
            <div className="flex items-start justify-between flex-wrap gap-4">
              <div className="flex-1">
                <h2 className="text-xl font-bold text-gray-900 mb-1">{recommendation.workout.name}</h2>
                <p className="text-sm text-gray-500">{recommendation.rationale}</p>
              </div>
              <div className="flex gap-4 text-center">
                <div className="bg-primary-50 rounded-xl px-5 py-3">
                  <p className="text-2xl font-bold text-primary-600">{recommendation.workout.total_duration_minutes}</p>
                  <p className="text-xs text-gray-500">minutes</p>
                </div>
                <div className="bg-orange-50 rounded-xl px-5 py-3">
                  <p className="text-2xl font-bold text-orange-500">{recommendation.workout.estimated_calories}</p>
                  <p className="text-xs text-gray-500">kcal</p>
                </div>
                <div className="bg-purple-50 rounded-xl px-5 py-3">
                  <p className="text-2xl font-bold text-purple-600">{recommendation.workout.exercises.length}</p>
                  <p className="text-xs text-gray-500">exercices</p>
                </div>
              </div>
            </div>

            {/* Warmup */}
            <div className="mt-4 p-3 bg-yellow-50 rounded-xl">
              <p className="text-xs font-semibold text-yellow-700 mb-2 uppercase tracking-wide">Échauffement</p>
              <div className="flex flex-wrap gap-2">
                {recommendation.workout.warmup.map((step, i) => (
                  <span key={i} className="text-xs bg-white border border-yellow-200 text-yellow-800 px-2 py-1 rounded-full">{step}</span>
                ))}
              </div>
            </div>
          </Card>

          {/* Exercises */}
          <div className="space-y-3">
            {recommendation.workout.exercises.map((ex, idx) => (
              <Card key={ex.id} padding="sm">
                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary-100 text-primary-700 flex items-center justify-center text-sm font-bold">
                    {idx + 1}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1 flex-wrap">
                      <h3 className="font-semibold text-gray-900">{ex.name}</h3>
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${categoryColors[ex.category] ?? 'bg-gray-100 text-gray-600'}`}>
                        {categoryLabels[ex.category] ?? ex.category}
                      </span>
                      <span className={`text-xs px-2 py-0.5 rounded-full ${difficultyColors[ex.difficulty] ?? ''}`}>
                        {ex.difficulty}
                      </span>
                    </div>
                    <p className="text-xs text-gray-500 mb-3">{ex.description}</p>
                    <div className="flex gap-4 text-xs text-gray-600 mb-3">
                      <span className="flex items-center gap-1">⏱ <strong>{ex.duration_minutes} min</strong></span>
                      <span className="flex items-center gap-1">🔥 <strong>~{Math.round(ex.calories_per_hour * ex.duration_minutes / 60)} kcal</strong></span>
                      <span className="flex items-center gap-1">💪 {ex.muscle_groups.slice(0, 2).join(', ')}</span>
                    </div>

                    {/* Benefits */}
                    {ex.benefits?.length > 0 && (
                      <div className="flex flex-wrap gap-1 mb-3">
                        {ex.benefits.map((b, i) => (
                          <span key={i} className="text-xs bg-green-50 text-green-700 px-2 py-0.5 rounded-full">✓ {b}</span>
                        ))}
                      </div>
                    )}

                    <details className="mt-1">
                      <summary className="text-xs text-primary-600 cursor-pointer font-medium hover:text-primary-700">
                        Voir les instructions
                      </summary>
                      <ol className="mt-2 space-y-1 pl-4">
                        {ex.instructions.map((inst, i) => (
                          <li key={i} className="text-xs text-gray-600">{i + 1}. {inst}</li>
                        ))}
                      </ol>
                    </details>
                  </div>
                  <Button
                    size="sm"
                    variant={logged.has(ex.id) ? 'secondary' : 'primary'}
                    onClick={() => !logged.has(ex.id) && logMutation.mutate(ex)}
                    disabled={logged.has(ex.id)}
                    aria-label={`Marquer ${ex.name} comme effectué`}
                  >
                    {logged.has(ex.id) ? '✓ Fait' : 'Marquer fait'}
                  </Button>
                </div>
              </Card>
            ))}
          </div>

          {/* Cooldown */}
          <Card padding="sm">
            <p className="text-xs font-semibold text-blue-700 mb-2 uppercase tracking-wide">Retour au calme</p>
            <div className="flex flex-wrap gap-2">
              {recommendation.workout.cooldown.map((step, i) => (
                <span key={i} className="text-xs bg-blue-50 border border-blue-200 text-blue-800 px-2 py-1 rounded-full">{step}</span>
              ))}
            </div>
          </Card>

          {/* AI Tips */}
          {recommendation.ai_tips.length > 0 && (
            <Card className="border-primary-200 bg-primary-50">
              <h3 className="text-sm font-semibold text-primary-800 mb-3">💡 Conseils de votre coach IA</h3>
              <ul className="space-y-2">
                {recommendation.ai_tips.map((tip, i) => (
                  <li key={i} className="text-sm text-primary-900 flex gap-2">
                    <span aria-hidden="true" className="text-primary-500 flex-shrink-0">→</span>
                    {tip}
                  </li>
                ))}
              </ul>
              {recommendation.next_session_suggestion && (
                <p className="mt-3 pt-3 border-t border-primary-200 text-xs text-primary-700 italic">
                  📅 {recommendation.next_session_suggestion}
                </p>
              )}
            </Card>
          )}

          {/* Radar chart — répartition des catégories d'exercices */}
          {recommendation.workout.exercises.length > 0 && (
            <Card>
              <h3 className="font-semibold text-gray-900 mb-1">Répartition de la séance</h3>
              <p className="text-xs text-gray-400 mb-2">Minutes par type d'effort</p>
              <ResponsiveContainer width="100%" height={240}>
                <RadarChart data={buildRadarData(recommendation.workout.exercises)}>
                  <PolarGrid />
                  <PolarAngleAxis dataKey="subject" tick={{ fontSize: 12 }} />
                  <PolarRadiusAxis angle={30} domain={[0, 30]} tick={{ fontSize: 10 }} />
                  <Radar
                    name="Minutes"
                    dataKey="minutes"
                    stroke="#6366f1"
                    fill="#6366f1"
                    fillOpacity={0.4}
                  />
                  <ReTooltip formatter={(v: number) => [`${v} min`, 'Durée']} />
                  <Legend />
                </RadarChart>
              </ResponsiveContainer>
            </Card>
          )}
        </div>
      )}
    </div>
    </PremiumGate>
  )
}
