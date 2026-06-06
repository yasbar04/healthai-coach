import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js'
import { Bar } from 'react-chartjs-2'

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend)

interface CalorieChartProps {
  data: { day: string; calories: number }[]
  target?: number
}

export default function CalorieChart({ data, target }: CalorieChartProps) {
  const labels = data.map((d) => {
    const date = new Date(d.day)
    return date.toLocaleDateString('fr-FR', { weekday: 'short', day: 'numeric' })
  })

  const chartData = {
    labels,
    datasets: [
      {
        label: 'Calories (kcal)',
        data: data.map((d) => d.calories),
        backgroundColor: data.map((d) =>
          target && d.calories > target * 1.1
            ? 'rgba(239, 68, 68, 0.7)'
            : 'rgba(34, 197, 94, 0.7)',
        ),
        borderColor: data.map((d) =>
          target && d.calories > target * 1.1
            ? 'rgb(239, 68, 68)'
            : 'rgb(34, 197, 94)',
        ),
        borderWidth: 2,
        borderRadius: 6,
      },
    ],
  }

  const options = {
    responsive: true,
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: (ctx: { parsed: { y: number } }) => `${ctx.parsed.y} kcal`,
        },
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        grid: { color: 'rgba(0,0,0,0.05)' },
        ticks: { callback: (v: number | string) => `${v} kcal` },
      },
      x: { grid: { display: false } },
    },
  }

  return (
    <div aria-label="Graphique des calories par jour">
      <Bar data={chartData} options={options as never} />
    </div>
  )
}
