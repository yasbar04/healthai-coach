import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js'
import { Doughnut } from 'react-chartjs-2'

ChartJS.register(ArcElement, Tooltip, Legend)

interface MacroChartProps {
  protein: number
  carbs: number
  fat: number
}

export default function MacroChart({ protein, carbs, fat }: MacroChartProps) {
  const total = protein + carbs + fat || 1

  const chartData = {
    labels: ['Protéines', 'Glucides', 'Lipides'],
    datasets: [
      {
        data: [protein, carbs, fat],
        backgroundColor: [
          'rgba(59, 130, 246, 0.8)',
          'rgba(34, 197, 94, 0.8)',
          'rgba(251, 191, 36, 0.8)',
        ],
        borderColor: ['rgb(59, 130, 246)', 'rgb(34, 197, 94)', 'rgb(251, 191, 36)'],
        borderWidth: 2,
      },
    ],
  }

  const options = {
    cutout: '65%',
    plugins: {
      legend: { position: 'bottom' as const, labels: { padding: 16, font: { size: 12 } } },
      tooltip: {
        callbacks: {
          label: (ctx: { label: string; parsed: number }) =>
            `${ctx.label}: ${ctx.parsed}g (${Math.round((ctx.parsed / total) * 100)}%)`,
        },
      },
    },
  }

  return (
    <div className="max-w-xs mx-auto" aria-label="Répartition des macronutriments">
      <Doughnut data={chartData} options={options} />
    </div>
  )
}
