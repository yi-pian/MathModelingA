# 2023A 独立反向审查

结论：**PASS**

- PASS — Q1 official time order：rows=60, unique=60
- PASS — Q1 efficiency finite/range：min=0.483368, max=0.965160
- PASS — Q1 monthly/year aggregation：equal 5-times/month and 12-month arithmetic means
- PASS — Q2 official time order：rows=60, unique=60
- PASS — Q2 efficiency finite/range：min=0.368238, max=0.963618
- PASS — Q2 monthly/year aggregation：equal 5-times/month and 12-month arithmetic means
- PASS — Q3 official time order：rows=60, unique=60
- PASS — Q3 efficiency finite/range：min=0.371982, max=0.963766
- PASS — Q3 monthly/year aggregation：equal 5-times/month and 12-month arithmetic means
- PASS — max/min direction Q2：candidate table maximizes power_per_area subject to calibrated feasibility threshold
- PASS — Q2 rated power：60.895838359 MW
- PASS — Q3 rated power：60.656295785 MW
- PASS — Q3 improves Q2 area objective：Q2=0.471945520, Q3=0.477353845
- PASS — Q2 constraints and signs：{"mirror_count": 3054, "total_area_m2": 129031.5, "field_center_margin_min_m": 0.10528122158166298, "tower_exclusion_margin_min_m": 0.1146020245086703, "dimension_margin_min_m": 0.0, "installation_margin_min_m": 0.04999999999999982, "spacing_margin_min_m": 0.04999999999991722, "nearest_distance_min_m": 11.549999999999917, "tower_inside_field_margin_m": 300.0, "rated_power_margin_mw": 0.8958383592647863, "all_geometric_constraints_pass": true}
- PASS — Q2 Excel exact values：shape=(3054, 8), NaN=0
- PASS — Q3 constraints and signs：{"mirror_count": 3054, "total_area_m2": 127067.78520000001, "field_center_margin_min_m": 0.10528122158166298, "tower_exclusion_margin_min_m": 0.1146020245086703, "dimension_margin_min_m": 0.0, "installation_margin_min_m": 0.04999999999999982, "spacing_margin_min_m": 0.009999999999918074, "nearest_distance_min_m": 11.549999999999917, "tower_inside_field_margin_m": 300.0, "rated_power_margin_mw": 0.6562957850183224, "all_geometric_constraints_pass": true}
- PASS — Q3 Excel exact values：shape=(3054, 8), NaN=0
- PASS — figure/Origin FINAL-data consistency：Origin monthly Q1 equals FINAL monthly CSV

## 常数与假设

- receiver radius/height/center：official statement
- reflectivity 0.92：official permitted example
- solar half-angle 4.65 mrad：external physical constant; MODEL_CONFIRMATION_REQUIRED
- 0.05 m layout/ground margins：explicit numerical feasibility margins
- Q2 60.35 MW screen threshold：calibrated by three independent FINAL candidates

## 未消除的模型边界

- equal weighting of the 60 official points requires model confirmation
- uniform 4.65 mrad solar disk is external to the statement
- triangular lattice and four radial zones do not prove unrestricted global optimality
- shadow/blocking uses central solar/receiver rays per mirror cell; sun-cone effects are applied in truncation
