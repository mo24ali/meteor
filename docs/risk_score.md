# Weather Risk Score — Méthodologie

Le score de risque météo, noté de **0 à 100**, quantifie la dangerosité
d'une journée de prévision pour une ville donnée. Plus le score est élevé,
plus la vigilance est requise.

## Formule

```
risk_score = 0.30 * temp_score   + 0.30 * precip_score
           + 0.20 * wind_score   + 0.20 * wmo_severity
```

Chaque composante est normalisée sur **0–100**. Les poids favorisent la
chaleur et les précipitations, les deux aléas les plus impactants pour la
sécurité et les infrastructures au Maroc.

## Composantes et seuils

### temp_score — chaleur (`temp_max_celsius`)
| Temp max | Score | Justification |
|---|---|---|
| ≤ 30 °C | 0 | Confort estival courant |
| 30 → 40 °C | 0 → 100 (linéaire) | Au-delà de 30 °C, stress thermique croissant (vague de chaleur) |
| ≥ 40 °C | 100 | Canicule sévère : menace pour les populations fragiles et les réseaux |

### precip_score — précipitations (`precipitation_mm`)
| Précip / 24h | Score | Justification |
|---|---|---|
| < 1 mm | 0 | Sec, aucun risque |
| 1 → 50 mm | `precip/50*100` (plafonné 100) | Risque de ruissellement puis d'inondation |
| ≥ 50 mm | 100 | Pluie torrentielle, crue éclair |

### wind_score — vent (`wind_speed_max_kmh`)
| Vitesse | Score | Justification |
|---|---|---|
| < 20 km/h | 0 | Vent faible |
| 20 → 100 km/h | `(speed-20)/80*100` (plafonné 100) | Le vent devient dangereux au-delà de 20 km/h (trafic, structures) |
| ≥ 100 km/h | 100 | Tempête — dégâts matériels |

### wmo_severity — code météo WMO (`weather_code`)
| Codes WMO | Score | Exemple |
|---|---|---|
| 0 | 0 | Ciel clair |
| 1–3 | 10 | Partiellement nuageux |
| 45–48 | 30 | Brouillard |
| 51–67 | 50–80 | Pluie (faible → forte) |
| 71–77 | 40–70 | Neige |
| 80–82 | 70–85 | Averses |
| 85–86 | 80–90 | Neige en averses |
| 95–99 | 90–100 | Orages / grêle |

## Niveaux de risque

| Intervalle | Niveau | Action suggérée |
|---|---|---|
| [0, 35) | LOW | Aucune vigilance particulière |
| [35, 55) | MODERATE | Conditions dégradées, être attentif |
| [55, 75) | HIGH | Prévoir des mesures de protection |
| [75, 100] | EXTREME | Alerte : éviter tout déplacement |

## Variables d'entrée (silver)

Provenance : `data/silver/weather_enriched.csv` — une ligne = ville × jour de
prévision. Colonnes utilisées : `temp_max_celsius`, `precipitation_mm`,
`wind_speed_max_kmh`, `weather_code`.