export function scoreTask(task, weights) { return Object.entries(weights).reduce((score, [name, weight]) => score + task.signals[name] * weight, 0); }
function unmetDependency(task, completed) { return task.depends_on.find(dep => !completed.includes(dep)); }
function reasonFor(task, verdict, context) {
  const score = `${Math.round(context.score * 1000) / 1000}`;
  if (verdict === "DO NOW") return `DO NOW — ranked #${context.rank}, score ${score}, ready, capacity available in ${context.needed_categories.join(", ")}.`;
  if (verdict === "QUEUED") return `QUEUED — ready and high priority (score ${score}), but ${context.full_categories.join(", ")} capacity is full this cycle.`;
  if (verdict === "NOT YET") return context.unmet_dep ? `NOT YET — blocked: ${context.unmet_dep} not complete` : `NOT YET — readiness ${context.readiness} below gate ${context.gate}.`;
  return `LATER — score ${score} is below the cutoff ${context.cutoff}; not worth doing yet.`;
}
export function buildPlan(config, modeName = config.active_mode) {
  if (!config.modes[modeName]) throw new Error(`unknown mode '${modeName}'`);
  const weights = config.modes[modeName], gate = config.thresholds.readiness_gate, cutoff = config.thresholds.score_cutoff;
  const scores = Object.fromEntries(config.tasks.map(task => [task.id, scoreTask(task, weights)]));
  const early = new Map(), candidates = [];
  for (const task of config.tasks) {
    if (task.readiness < gate) early.set(task.id, ["NOT YET", {readiness:task.readiness, gate}]);
    else if (scores[task.id] < cutoff) early.set(task.id, ["LATER", {cutoff}]); else candidates.push(task);
  }
  const ranked = [...candidates].sort((a,b) => scores[b.id] - scores[a.id]);
  const remaining = {...config.capacity}, underway = [...config.completed], entries = [];
  ranked.forEach((task, index) => {
    const dep = unmetDependency(task, underway), rank = index + 1;
    if (dep) entries.push(entry(task, scores[task.id], rank, "NOT YET", {unmet_dep:dep, score:scores[task.id], rank}));
    else { const needed = Object.keys(task.needs).filter(key => task.needs[key] > 0), full = needed.filter(key => task.needs[key] > remaining[key]);
      if (full.length) entries.push(entry(task, scores[task.id], rank, "QUEUED", {full_categories:full, score:scores[task.id], rank}));
      else { needed.forEach(key => remaining[key] -= task.needs[key]); underway.push(task.id); entries.push(entry(task, scores[task.id], rank, "DO NOW", {needed_categories:needed, score:scores[task.id], rank})); }
    }
  });
  for (const task of config.tasks) if (early.has(task.id)) { const [verdict, context] = early.get(task.id); entries.push(entry(task, scores[task.id], null, verdict, {...context, score:scores[task.id]})); }
  return {mode:modeName, tasks:entries.sort((a,b) => b.priority_score - a.priority_score), remaining_capacity:remaining};
}
function entry(task, score, rank, verdict, context) { return {id:task.id, priority_score:Math.round(score*1000)/1000, rank, verdict, reason:reasonFor(task, verdict, context)}; }
