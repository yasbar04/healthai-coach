interface StatCardProps {
  label: string
  value: string | number
  unit?: string
  icon?: string
  trend?: 'up' | 'down' | 'neutral'
  description?: string
}

export default function StatCard({ label, value, unit, icon, trend, description }: StatCardProps) {
  const trendColors = {
    up: 'text-green-600',
    down: 'text-red-600',
    neutral: 'text-gray-500',
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 flex flex-col gap-3 shadow-sm">
      <div className="flex items-center justify-between">
        <span className="text-sm text-gray-500 font-medium">{label}</span>
        {icon && <span className="text-2xl" aria-hidden="true">{icon}</span>}
      </div>
      <div className="flex items-end gap-1">
        <span className="text-3xl font-bold text-gray-900">{value}</span>
        {unit && <span className="text-sm text-gray-500 mb-1">{unit}</span>}
      </div>
      {description && (
        <p className={`text-xs ${trend ? trendColors[trend] : 'text-gray-500'}`}>
          {description}
        </p>
      )}
    </div>
  )
}
