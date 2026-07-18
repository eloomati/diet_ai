import { X } from 'lucide-react'
import { useState } from 'react'

import type { DayOfWeek, WeeklyObligation } from '@/api/profile'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { DAY_OF_WEEK_OPTIONS, dayOfWeekLabel } from '@/lib/profileOptions'

interface WeeklyObligationsEditorProps {
  value: WeeklyObligation[]
  onChange: (obligations: WeeklyObligation[]) => void
}

export function WeeklyObligationsEditor({ value, onChange }: WeeklyObligationsEditorProps) {
  const [day, setDay] = useState<DayOfWeek>('MON')
  const [startTime, setStartTime] = useState('')
  const [endTime, setEndTime] = useState('')
  const [label, setLabel] = useState('')

  const canAdd = startTime !== '' && endTime !== '' && label.trim() !== '' && endTime > startTime

  function handleAdd() {
    if (!canAdd) return
    onChange([...value, { day_of_week: day, start_time: startTime, end_time: endTime, label: label.trim() }])
    setStartTime('')
    setEndTime('')
    setLabel('')
  }

  function handleRemove(index: number) {
    onChange(value.filter((_, i) => i !== index))
  }

  return (
    <div className="flex flex-col gap-2">
      {value.length === 0 ? (
        <p className="text-xs text-muted-foreground">Brak stałych zobowiązań w tygodniu.</p>
      ) : (
        value.map((obligation, index) => (
          <div
            key={`${obligation.day_of_week}-${obligation.start_time}-${index}`}
            className="flex items-center justify-between gap-2 rounded-lg border border-border px-2.5 py-1.5 text-[13px]"
          >
            <span>
              <b>{dayOfWeekLabel(obligation.day_of_week)}</b> {obligation.start_time}–{obligation.end_time} ·{' '}
              {obligation.label}
            </span>
            <button
              type="button"
              onClick={() => handleRemove(index)}
              aria-label={`Usuń zobowiązanie: ${obligation.label}`}
              className="text-muted-foreground hover:text-destructive"
            >
              <X className="size-3.5" />
            </button>
          </div>
        ))
      )}

      <div className="flex flex-wrap items-end gap-2">
        <div>
          <label className="mb-1 block text-[11px] font-bold text-muted-foreground">Dzień</label>
          <Select
            value={day}
            onValueChange={(next: DayOfWeek | null) => {
              if (next) setDay(next)
            }}
          >
            <SelectTrigger>
              <SelectValue>{(v: DayOfWeek) => dayOfWeekLabel(v)}</SelectValue>
            </SelectTrigger>
            <SelectContent>
              {DAY_OF_WEEK_OPTIONS.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div>
          <label htmlFor="obligation-start" className="mb-1 block text-[11px] font-bold text-muted-foreground">
            Od
          </label>
          <Input
            id="obligation-start"
            type="time"
            value={startTime}
            onChange={(event) => setStartTime(event.target.value)}
          />
        </div>
        <div>
          <label htmlFor="obligation-end" className="mb-1 block text-[11px] font-bold text-muted-foreground">
            Do
          </label>
          <Input id="obligation-end" type="time" value={endTime} onChange={(event) => setEndTime(event.target.value)} />
        </div>
        <div className="min-w-[120px] flex-1">
          <label htmlFor="obligation-label" className="mb-1 block text-[11px] font-bold text-muted-foreground">
            Nazwa
          </label>
          <Input
            id="obligation-label"
            value={label}
            onChange={(event) => setLabel(event.target.value)}
            placeholder="np. Praca"
          />
        </div>
        <Button type="button" variant="outline" onClick={handleAdd} disabled={!canAdd}>
          Dodaj
        </Button>
      </div>
      {startTime && endTime && endTime <= startTime && (
        <p className="text-[12px] font-bold text-destructive">Godzina końca musi być późniejsza niż początku.</p>
      )}
    </div>
  )
}
