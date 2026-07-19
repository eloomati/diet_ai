import { Badge } from '@/components/ui/badge'
import { dietTypeLabel, goalLabel } from '@/lib/profileOptions'
import type { DietPlan } from '@/api/dietPlans'

export function DietPlanCard({ plan }: { plan: DietPlan }) {
  return (
    <div className="mx-auto w-full max-w-2xl rounded-2xl border border-border bg-card p-4 shadow-sm">
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <Badge className="rounded-full bg-accent px-2.5 py-1 text-xs font-bold text-accent-foreground uppercase">
          Wygenerowany plan
        </Badge>
        <span className="text-[12.5px] font-bold text-muted-foreground">
          {goalLabel(plan.goal)} · {dietTypeLabel(plan.diet_type)} · {plan.duration_days}{' '}
          {plan.duration_days === 1 ? 'dzień' : 'dni'}
        </span>
      </div>
      <div className="flex flex-col gap-3">
        {plan.days.map((day) => (
          <div key={day.day_number}>
            <p className="mb-1 text-[12.5px] font-bold text-foreground">Dzień {day.day_number}</p>
            <ul className="flex flex-col gap-1">
              {day.meals.map((meal) => (
                <li
                  key={meal.name}
                  className="flex items-center justify-between gap-2 rounded-lg bg-muted px-2.5 py-1.5 text-[12.5px]"
                >
                  <span className="font-bold">
                    {meal.time ? `${meal.time} · ` : ''}
                    {meal.name}
                  </span>
                  <span className="text-muted-foreground">
                    {meal.calories} kcal · B{meal.protein}/W{meal.carbohydrates}/T{meal.fat}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </div>
  )
}
