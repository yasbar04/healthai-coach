import { useState, FormEvent } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { usersApi, UserProfile } from '../api/users'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import Input from '../components/ui/Input'
import Select from '../components/ui/Select'

const GOAL_OPTIONS = [
  { value: 'maintain', label: 'Maintenir mon poids' },
  { value: 'lose_weight', label: 'Perdre du poids' },
  { value: 'gain_muscle', label: 'Prendre de la masse' },
  { value: 'endurance', label: 'Améliorer mon endurance' },
]

const ACTIVITY_OPTIONS = [
  { value: 'sedentary', label: 'Sédentaire' },
  { value: 'light', label: 'Légèrement actif' },
  { value: 'moderate', label: 'Modérément actif' },
  { value: 'active', label: 'Très actif' },
  { value: 'very_active', label: 'Extrêmement actif' },
]

function bmiCategory(bmi: number): string {
  if (bmi < 18.5) return 'Insuffisance pondérale'
  if (bmi < 25) return 'Poids normal'
  if (bmi < 30) return 'Surpoids'
  return 'Obésité'
}

export default function ProfilePage() {
  const qc = useQueryClient()
  const { data: profile, isLoading } = useQuery({ queryKey: ['profile'], queryFn: usersApi.getProfile })
  const [editing, setEditing] = useState(false)
  const [success, setSuccess] = useState(false)
  const [form, setForm] = useState<Partial<UserProfile>>({})

  function startEdit() {
    if (profile) {
      setForm({
        full_name: profile.full_name,
        email: profile.email,
        age: profile.age,
        weight_kg: profile.weight_kg,
        height_cm: profile.height_cm,
        goal: profile.goal,
        activity_level: profile.activity_level,
      })
    }
    setEditing(true)
    setSuccess(false)
  }

  const updateMutation = useMutation({
    mutationFn: (data: Partial<UserProfile>) => usersApi.updateProfile(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['profile'] })
      setEditing(false)
      setSuccess(true)
    },
  })

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    updateMutation.mutate(form)
  }

  function setField(field: keyof UserProfile) {
    return (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
      setForm((p) => ({ ...p, [field]: e.target.type === 'number' ? Number(e.target.value) : e.target.value }))
  }

  if (isLoading) return <p className="text-gray-500">Chargement…</p>
  if (!profile) return null

  return (
    <div className="space-y-6 max-w-2xl">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Mon profil</h1>
        {!editing && (
          <Button variant="secondary" onClick={startEdit}>Modifier</Button>
        )}
      </div>

      {success && (
        <div role="status" aria-live="polite" className="p-3 bg-green-50 border border-green-200 rounded-lg text-sm text-green-700">
          Profil mis à jour avec succès
        </div>
      )}

      {/* Stats overview */}
      <div className="grid grid-cols-3 gap-4">
        {profile.bmi && (
          <Card padding="sm" className="text-center">
            <p className="text-2xl font-bold text-gray-900">{profile.bmi}</p>
            <p className="text-xs text-gray-500">IMC</p>
            <p className="text-xs text-primary-600 mt-1">{bmiCategory(profile.bmi)}</p>
          </Card>
        )}
        {profile.daily_calorie_target && (
          <Card padding="sm" className="text-center">
            <p className="text-2xl font-bold text-gray-900">{profile.daily_calorie_target}</p>
            <p className="text-xs text-gray-500">kcal/jour recommandés</p>
          </Card>
        )}
        <Card padding="sm" className="text-center">
          <p className="text-2xl font-bold text-gray-900">
            {new Date(profile.created_at).toLocaleDateString('fr-FR', { month: 'short', year: 'numeric' })}
          </p>
          <p className="text-xs text-gray-500">Membre depuis</p>
        </Card>
      </div>

      {!editing ? (
        <Card>
          <dl className="grid grid-cols-2 gap-x-6 gap-y-4">
            {[
              { label: 'Nom d\'utilisateur', value: profile.username },
              { label: 'Nom complet', value: profile.full_name },
              { label: 'Email', value: profile.email },
              { label: 'Âge', value: profile.age ? `${profile.age} ans` : '—' },
              { label: 'Poids', value: profile.weight_kg ? `${profile.weight_kg} kg` : '—' },
              { label: 'Taille', value: profile.height_cm ? `${profile.height_cm} cm` : '—' },
              { label: 'Objectif', value: GOAL_OPTIONS.find((o) => o.value === profile.goal)?.label ?? profile.goal },
              { label: 'Activité', value: ACTIVITY_OPTIONS.find((o) => o.value === profile.activity_level)?.label ?? profile.activity_level },
            ].map(({ label, value }) => (
              <div key={label}>
                <dt className="text-xs text-gray-500 font-medium">{label}</dt>
                <dd className="text-sm text-gray-900 mt-0.5">{value}</dd>
              </div>
            ))}
          </dl>
        </Card>
      ) : (
        <Card>
          <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-4">
            <div className="grid grid-cols-2 gap-4">
              <Input label="Nom complet" type="text" value={form.full_name ?? ''} onChange={setField('full_name')} required />
              <Input label="Email" type="email" value={form.email ?? ''} onChange={setField('email')} required />
            </div>
            <div className="grid grid-cols-3 gap-4">
              <Input label="Âge" type="number" value={form.age ?? ''} onChange={setField('age')} min="10" max="120" />
              <Input label="Poids (kg)" type="number" value={form.weight_kg ?? ''} onChange={setField('weight_kg')} step="0.1" />
              <Input label="Taille (cm)" type="number" value={form.height_cm ?? ''} onChange={setField('height_cm')} />
            </div>
            <Select label="Objectif" value={form.goal ?? 'maintain'} onChange={setField('goal')} options={GOAL_OPTIONS} />
            <Select label="Niveau d'activité" value={form.activity_level ?? 'moderate'} onChange={setField('activity_level')} options={ACTIVITY_OPTIONS} />

            {updateMutation.isError && (
              <p role="alert" className="text-sm text-red-600">Erreur lors de la mise à jour</p>
            )}

            <div className="flex gap-3">
              <Button type="submit" loading={updateMutation.isPending}>Enregistrer</Button>
              <Button type="button" variant="secondary" onClick={() => setEditing(false)}>Annuler</Button>
            </div>
          </form>
        </Card>
      )}
    </div>
  )
}
