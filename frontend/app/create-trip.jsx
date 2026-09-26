import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import PageHeader from '../components/common/PageHeader.jsx'
import PlanForm from '../components/trip/PlanForm.jsx'
import { api, getToken } from '../services/api.js'

const initialForm = {
  destination: '',
  start: '',
  end: '',
  budget: 1000,
  travelers: 1,
  selected: [],
}

export default function CreateTrip() {
  const navigate = useNavigate()
  const [form, setForm] = useState(initialForm)
  const [formError, setFormError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [justAdded, setJustAdded] = useState(false)

  const set = (key, value) => {
    setForm((f) => ({ ...f, [key]: value }))
    if (formError) setFormError('')
  }

  const toggleInterest = (id) =>
    setForm((f) => ({
      ...f,
      selected: f.selected.includes(id)
        ? f.selected.filter((x) => x !== id)
        : [...f.selected, id],
    }))

  const handlePlan = async (e) => {
    e.preventDefault()
    if (!form.destination.trim()) {
      setFormError('Enter a destination.')
      return
    }
    if (!form.start || !form.end) {
      setFormError('Choose start and end dates.')
      return
    }
    if (new Date(form.end) < new Date(form.start)) {
      setFormError('The end date must be after the start date.')
      return
    }
    setFormError('')
    setSubmitting(true)
    try {
      await api.createTrip(
        {
          destination: form.destination.trim(),
          start_date: form.start,
          end_date: form.end,
          budget: form.budget,
          travelers: form.travelers,
          interests: form.selected,
        },
        getToken(),
      )
      setJustAdded(true)
      setTimeout(() => navigate('/dashboard'), 500)
    } catch (err) {
      setFormError(err.message)
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen w-full">
      <PageHeader />

      <main className="mx-auto max-w-2xl px-5 py-8">
        <h1 className="text-xl font-semibold tracking-tight text-main">Create a trip</h1>
        <p className="mt-1.5 text-[13px] text-mut">
          Enter your destination, dates and budget. The trip is saved to your account.
        </p>

        <section className="card mt-6 p-5">
          <PlanForm
            form={form}
            onFieldChange={set}
            onToggleInterest={toggleInterest}
            onSubmit={handlePlan}
            submitting={submitting}
            justAdded={justAdded}
            error={formError}
          />
        </section>
      </main>
    </div>
  )
}
