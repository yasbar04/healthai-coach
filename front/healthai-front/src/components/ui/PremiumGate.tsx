import { useAuth } from '../../auth/AuthContext'

const PLAN_LABELS: Record<string, string> = {
  freemium: 'Gratuit',
  premium: 'Premium',
  premium_plus: 'Premium+',
  b2b: 'B2B',
}

interface PremiumGateProps {
  children: React.ReactNode
  feature?: string
}

export default function PremiumGate({ children, feature }: PremiumGateProps) {
  const { user } = useAuth()
  const plan = user?.plan ?? 'freemium'
  const isPremium =
    plan === 'premium' || plan === 'premium_plus' || user?.role === 'admin'

  if (isPremium) return <>{children}</>

  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 text-center space-y-4">
      <div className="text-5xl">🔒</div>
      <h2 className="text-xl font-bold text-gray-900">Fonctionnalité Premium</h2>
      <p className="text-gray-500 max-w-sm">
        {feature
          ? `${feature} est réservé aux abonnés Premium.`
          : 'Cette fonctionnalité est réservée aux abonnés Premium.'}
      </p>
      <div className="bg-gray-50 border border-gray-200 rounded-xl p-4 w-full max-w-sm space-y-2 text-left">
        <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide">Votre plan actuel</p>
        <div className="flex items-center gap-2">
          <span className="px-2 py-0.5 bg-gray-200 text-gray-700 rounded-full text-xs font-medium">
            {PLAN_LABELS[plan] ?? plan}
          </span>
          <span className="text-sm text-gray-600">— accès limité</span>
        </div>
      </div>
      <div className="bg-gradient-to-br from-primary-50 to-purple-50 border border-primary-100 rounded-xl p-5 w-full max-w-sm space-y-3 text-left">
        <p className="font-semibold text-gray-900">Passez à Premium 🚀</p>
        <ul className="space-y-1.5 text-sm text-gray-600">
          <li className="flex gap-2"><span className="text-green-500">✓</span> Recommandations IA personnalisées</li>
          <li className="flex gap-2"><span className="text-green-500">✓</span> Analyse photo de vos repas</li>
          <li className="flex gap-2"><span className="text-green-500">✓</span> Plans alimentaires sur-mesure</li>
          <li className="flex gap-2"><span className="text-green-500">✓</span> Séances de sport générées par IA</li>
          <li className="flex gap-2"><span className="text-green-500">✓</span> Suivi biométrique avancé</li>
        </ul>
        <p className="text-xs text-gray-400">À partir de 9,99 €/mois — sans engagement</p>
      </div>
    </div>
  )
}
