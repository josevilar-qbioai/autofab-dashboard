# 🤖 Modelo Logístico Anidado — Autofabricación 2027

Dashboard interactivo que visualiza el modelo de **4 olas tecnológicas anidadas** y la **dinámica de autofabricación de robots** con impacto en el portfolio de inversión.

**URL:** https://josevilar-qbioai.github.io/autofab-dashboard/

## Modelo matemático

```
V_i(t) = Capital_i × (1+r_i)^t × Φ_nested(t)/Φ_nested(0) × S_i(t)
```

donde:
- **Φ_nested(t)** = 1 + Σᵢ Kᵢ / (1 + e^(−γᵢ(t−t₀ᵢ))) — suma de 4 olas logísticas
- **S_i(t)** = 1 + εᵢ · (R(t)−1)/R(t) — prima de escasez
- **R(t)** = robot population con autofabricación desde 2027

## Las 4 olas

| Ola | Arranque | K | γ |
|-----|----------|---|---|
| LLM / Software IA | 2026 (t=0.5) | 1.5 | 1.4 |
| Robótica + autofab | **2027** (t=1.0) | 2.5 | 1.2 |
| Agentes autónomos | 2029 (t=3.0) | 3.5 | 0.9 |
| Autofab 2ª fase | 2031 (t=5.0) | 5.0 | 0.7 |

## Actualizar

```bash
python3 scripts/generate_dashboard.py
git add docs/index.html && git commit -m "Actualizar dashboard" && git push
```

## Referencias

Bass (1969), Rogers (1962), Kondratiev (1925), Freeman & Louçã (2001)
