"""Q5 restricted mixed discrete-continuous strategy with branch-and-bound assignment."""

from __future__ import annotations

import argparse
from itertools import product
import json
from pathlib import Path
import sys
from time import perf_counter

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = next(parent for parent in HERE.parents if (parent / "core").is_dir())
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(ROOT))

from core.export import export_origin_table, fill_excel_template
from core.optimization import optimize_global, optimize_scalar
from core.plotting import COLORS, save_figure, use_paper_style
from core.units import degree_to_rad
from core.validation import ValidationReport, check_constraints
import matplotlib.pyplot as plt

from common import Strategy, drop_point, event_value_m2, feasible_active_window, interval_duration, marginal_interval_gains, merge_intervals, missile_arrival_time, obscuration_intervals, target_surface_points, validate_drop_gaps
from problem_data import DECOY_POSITION_M, GRAVITY_M_S2, MISSILE_INITIAL_M, UAV_INITIAL_M

RESULTS = ROOT / "results" / "2025A"
TEMPLATE = ROOT / "data" / "2025A" / "official" / "templates" / "result3.xlsx"
UAVS = tuple(UAV_INITIAL_M)
MISSILES = tuple(MISSILE_INITIAL_M)
PROFILES = {
    "FAST": {"seeds": [0], "single_pop": 5, "single_iter": 20, "route_pop": 5, "route_iter": 25, "keep": 1},
    "STANDARD": {"seeds": [0, 1], "single_pop": 6, "single_iter": 30, "route_pop": 6, "route_iter": 35, "keep": 2},
    "FINAL": {"seeds": [0, 1], "single_pop": 6, "single_iter": 30, "route_pop": 5, "route_iter": 25, "keep": 2},
}


def single_bounds(uav, missile):
    max_delay = float(np.sqrt(2.0 * UAV_INITIAL_M[uav][2] / GRAVITY_M_S2))
    return [(0.0, 2.0 * np.pi), (70.0, 140.0), (0.0, missile_arrival_time(missile)), (0.0, max_delay)]


def to_single_strategy(uav, missile, values):
    heading, speed, burst_time, delay = map(float, values)
    if delay > burst_time:
        return None
    try:
        return Strategy(uav, missile, heading, speed, burst_time-delay, delay)
    except ValueError:
        return None


def single_guided_fitness(uav, missile, values):
    strategy = to_single_strategy(uav, missile, values)
    if strategy is None:
        return -1e12
    window = feasible_active_window(strategy)
    if window is None:
        return -1e12
    result = obscuration_intervals(strategy, model="point", precision="FAST")
    if result.duration_s > 0:
        return 1e6 + result.duration_s
    return -min(event_value_m2(strategy, time_s, model="point") for time_s in np.linspace(*window, 15))


def search_single_candidates(profile, *, cached=None):
    if cached:
        return cached
    candidates = {}
    for uav in UAVS:
        for missile in MISSILES:
            rows = []
            for seed in profile["seeds"]:
                result = optimize_global(
                    lambda x, u=uav, m=missile: single_guided_fitness(u, m, x),
                    single_bounds(uav, missile),
                    direction="maximize",
                    seed=seed,
                    popsize=profile["single_pop"],
                    maxiter=profile["single_iter"],
                    tol=1e-7,
                    polish=False,
                )
                strategy = to_single_strategy(uav, missile, result.x)
                full_duration = 0.0 if strategy is None else obscuration_intervals(strategy, model="full", precision="FAST").duration_s
                rows.append({"seed": seed, "success": result.success, "message": result.message, "x": np.asarray(result.x).tolist(), "full_fast_duration_s": full_duration})
            candidates[f"{uav}-{missile}"] = rows
    return candidates


def direct_decoy_heading(uav):
    vector = DECOY_POSITION_M[:2] - UAV_INITIAL_M[uav][:2]
    return float(np.arctan2(vector[1], vector[0]) % (2.0*np.pi))


def route_result(strategies, precision="FAST"):
    results = [obscuration_intervals(strategy, model="full", precision=precision) for strategy in strategies]
    union = merge_intervals([interval for result in results for interval in result.intervals_s])
    return results, union, interval_duration(union)


def polish_pair(uav, missile, heading, speed, bomb_no, pair, minimum_drop, maximum_drop):
    x = np.asarray(pair, dtype=float).copy()
    max_delay = single_bounds(uav, missile)[3][1]
    bounds = np.array([(minimum_drop, maximum_drop), (0.0, max_delay)], dtype=float)

    def make(values):
        drop, delay = map(float, values)
        try:
            strategy = Strategy(uav, missile, heading, speed, drop, delay, bomb_no)
        except ValueError:
            return None
        return strategy if strategy.burst_time_s < missile_arrival_time(missile) else None

    def own_duration(values):
        strategy = make(values)
        return -1e6 if strategy is None else obscuration_intervals(strategy, model="full", precision="FAST").duration_s

    success = True
    for steps in ([2.0, 2.0], [0.5, 0.5], [0.1, 0.1]):
        for index, step in enumerate(steps):
            baseline = own_duration(x)
            low = max(bounds[index, 0], x[index]-step); high = min(bounds[index, 1], x[index]+step)
            if high <= low + 1e-12:
                x[index] = low
                continue
            def objective(value):
                candidate=x.copy(); candidate[index]=value
                return own_duration(candidate)
            result = optimize_scalar(objective, bounds=(low, high), direction="maximize", options={"xatol":1e-6})
            success = success and result.success
            candidate=x.copy(); candidate[index]=result.x
            if own_duration(candidate) >= baseline:
                x=candidate
    return x, success


def build_route(uav, missile, heading, speed, *, seed, profile):
    strategies = []
    maximum_drop = min(45.0, missile_arrival_time(missile)-1e-3)
    surface = target_surface_points("FAST")
    certification = []
    for bomb_no in (1,2,3):
        minimum_drop = 0.0 if not strategies else strategies[-1].drop_time_s + 1.0
        bomb_maximum_drop = maximum_drop - (3-bomb_no)*1.0
        if minimum_drop > bomb_maximum_drop:
            minimum_drop = bomb_maximum_drop
        _, _, base_duration = route_result(strategies, "FAST") if strategies else ([], [], 0.0)
        max_delay = single_bounds(uav, missile)[3][1]

        def make(pair):
            drop, delay = map(float, pair)
            try:
                strategy=Strategy(uav, missile, heading, speed, drop, delay, bomb_no)
            except ValueError:
                return None
            return strategy if strategy.burst_time_s < missile_arrival_time(missile) else None

        def fitness(pair):
            strategy=make(pair)
            if strategy is None:
                return -1e12
            result=obscuration_intervals(strategy,model="full",precision="FAST")
            _,_,total=route_result([*strategies,strategy],"FAST")
            gain=total-base_duration
            if gain>1e-8:
                return 1e6+gain+1e-3*result.duration_s
            if result.duration_s>0:
                return 1e3+result.duration_s
            window=feasible_active_window(strategy)
            if window is None:
                return -1e12
            return -min(event_value_m2(strategy,t,model="full",surface_points=surface) for t in np.linspace(*window,17))

        search=optimize_global(fitness,[(minimum_drop,bomb_maximum_drop),(0.0,max_delay)],direction="maximize",seed=seed+17*bomb_no,popsize=profile["route_pop"],maxiter=profile["route_iter"],tol=1e-7,polish=False)
        polished,success=polish_pair(uav,missile,heading,speed,bomb_no,search.x,minimum_drop,bomb_maximum_drop)
        certification.append({"bomb_no":bomb_no,"search_success":search.success,"coordinate_success":success})
        strategy=make(polished)
        if strategy is None:
            raise RuntimeError(f"route timing infeasible for {uav}-{missile} bomb {bomb_no}")
        strategies.append(strategy)
    results,union,total=route_result(strategies,"FAST")
    return {"uav":uav,"missile":missile,"heading_rad":heading,"speed_m_s":speed,"strategies":strategies,"results":results,"union":union,"duration_s":total,"certification":certification}


def route_to_json(route):
    return {"uav":route["uav"],"missile":route["missile"],"heading_rad":route["heading_rad"],"speed_m_s":route["speed_m_s"],"duration_s":route["duration_s"],"certification":route["certification"],"strategies":[{"drop_time_s":s.drop_time_s,"delay_s":s.delay_s,"bomb_no":s.bomb_no} for s in route["strategies"]]}


def route_from_json(payload):
    strategies=[Strategy(payload["uav"],payload["missile"],payload["heading_rad"],payload["speed_m_s"],row["drop_time_s"],row["delay_s"],row["bomb_no"]) for row in payload["strategies"]]
    results,union,total=route_result(strategies,"FAST")
    return {**payload,"strategies":strategies,"results":results,"union":union,"duration_s":total}


def generate_routes(profile, singles, *, cached=None, progress_path=None):
    routes={} if not cached else {key:[route_from_json(item) for item in values] for key,values in cached.items()}
    pruning={}
    for uav in UAVS:
        ranking=[]
        for missile in MISSILES:
            best=max(singles[f"{uav}-{missile}"],key=lambda item:item["full_fast_duration_s"])
            ranking.append((missile,best["full_fast_duration_s"],best))
        ranking.sort(key=lambda item:item[1],reverse=True)
        kept=ranking[:profile["keep"]]
        pruning[uav]={"kept":[item[0] for item in kept],"removed":[item[0] for item in ranking[profile["keep"]:]],"single_bomb_scores":{m:score for m,score,_ in ranking}}
        for missile,_,best in kept:
            key=f"{uav}-{missile}"
            if key in routes:
                continue
            single_heading,single_speed=best["x"][:2]
            flight_candidates=[(single_heading,single_speed,"single-candidate"),(direct_decoy_heading(uav),140.0,"direct-decoy")]
            built=[]
            for index,(heading,speed,label) in enumerate(flight_candidates):
                route=build_route(uav,missile,heading,speed,seed=31*UAVS.index(uav)+7*MISSILES.index(missile)+index,profile=profile)
                route["flight_source"]=label; built.append(route)
            routes[key]=built
            if progress_path is not None:
                progress_path.write_text(json.dumps({"mode":"FINAL","singles":singles,"routes":{route_key:[route_to_json(item) for item in route_values] for route_key,route_values in routes.items()},"pruning":pruning},ensure_ascii=False,indent=2),encoding="utf-8")
    return routes,pruning


def select_assignment(routes, pruning):
    options=[]
    for uav in UAVS:
        uav_routes=[]
        for missile in pruning[uav]["kept"]:
            uav_routes.append(max(routes[f"{uav}-{missile}"],key=lambda route:route["duration_s"]))
        options.append(uav_routes)
    remaining_upper=[0.0]*(len(UAVS)+1)
    for index in range(len(UAVS)-1,-1,-1):
        remaining_upper[index]=remaining_upper[index+1]+max(route["duration_s"] for route in options[index])
    best={"score":-np.inf,"routes":None,"intervals":None};stats={"visited":0,"pruned":0,"leaves":0,"root_upper_bound_s":remaining_upper[0]}

    def recurse(index,chosen,intervals_by_missile,current_score):
        stats["visited"]+=1
        if current_score+remaining_upper[index] <= best["score"]+1e-12:
            stats["pruned"]+=1;return
        if index==len(UAVS):
            stats["leaves"]+=1
            if current_score>best["score"]:
                best.update(score=current_score,routes=list(chosen),intervals={m:list(v) for m,v in intervals_by_missile.items()})
            return
        for route in options[index]:
            updated={m:list(v) for m,v in intervals_by_missile.items()}
            updated[route["missile"]]=merge_intervals([*updated[route["missile"]],*route["union"]])
            score=sum(interval_duration(updated[m]) for m in MISSILES)
            recurse(index+1,[*chosen,route],updated,score)
    recurse(0,[],{missile:[] for missile in MISSILES},0.0)
    return best,stats


def optimize_q5(mode="FINAL",*,use_cache=True):
    profile=PROFILES[mode]; cache_dir=RESULTS/"cache"/mode;cache_dir.mkdir(parents=True,exist_ok=True)
    cache_path=cache_dir/"q5_search.json";cache=json.loads(cache_path.read_text(encoding="utf-8")) if use_cache and cache_path.exists() else {}
    started=perf_counter();singles=search_single_candidates(profile,cached=cache.get("singles"))
    cache_path.write_text(json.dumps({"mode":mode,"singles":singles,"routes":cache.get("routes",{}),"pruning":cache.get("pruning",{})},ensure_ascii=False,indent=2),encoding="utf-8")
    routes,pruning=generate_routes(profile,singles,cached=cache.get("routes"),progress_path=cache_path)
    cache_path.write_text(json.dumps({"mode":mode,"singles":singles,"routes":{key:[route_to_json(route) for route in value] for key,value in routes.items()},"pruning":pruning},ensure_ascii=False,indent=2),encoding="utf-8")
    assignment,stats=select_assignment(routes,pruning)
    chosen=assignment["routes"]
    strategies=[strategy for route in chosen for strategy in route["strategies"]]
    final_results=[obscuration_intervals(strategy,model="full",precision="FINAL") for strategy in strategies]
    intervals_by_missile={missile:merge_intervals([interval for strategy,result in zip(strategies,final_results) if strategy.missile==missile for interval in result.intervals_s]) for missile in MISSILES}
    duration_by_missile={missile:interval_duration(intervals) for missile,intervals in intervals_by_missile.items()}
    total=sum(duration_by_missile.values())
    gap_ok=validate_drop_gaps(strategies)
    shared_ok=all(len({round(s.heading_rad,12) for s in strategies if s.uav==uav})==1 and len({round(s.speed_m_s,9) for s in strategies if s.uav==uav})==1 for uav in UAVS)
    heights=[result.burst_point_m[2] for result in final_results]
    report=(ValidationReport().add("Q5 15 strategies",len(strategies)==15).add("Q5 shared flight per UAV",shared_ok).add("Q5 drop gaps",gap_ok).add("Q5 burst heights",check_constraints(heights,sense="ge")).add("Q5 explicit assignment",all(strategy.missile in MISSILES for strategy in strategies),str({route['uav']:route['missile'] for route in chosen})).add("Q5 interval recomputation",abs(total-sum(interval_duration(v) for v in intervals_by_missile.values()))<=1e-10).add("Q5 root residuals",max(result.root_residual_max_m2 for result in final_results)<=1e-4).add("Q5 multiple seeds",len(profile["seeds"])>=2).add("Q5 branch upper bound",stats["root_upper_bound_s"]>=assignment["score"]).add("Q5 global optimality",manual=True,detail="restricted one-missile-per-UAV candidate pool; global optimum not proven").add("Model interpretation",manual=True,detail="MODEL_CONFIRMATION_REQUIRED"))
    return {"mode":mode,"routes":chosen,"strategies":strategies,"results":final_results,"intervals_by_missile":intervals_by_missile,"duration_by_missile":duration_by_missile,"total_duration_s":total,"pruning":pruning,"branch_stats":stats,"validation":report,"elapsed_s":perf_counter()-started}


def export_result3(solution):
    values={}
    by_uav={uav:sorted([(strategy,result) for strategy,result in zip(solution["strategies"],solution["results"]) if strategy.uav==uav],key=lambda item:item[0].bomb_no) for uav in UAVS}
    row=2
    for uav in UAVS:
        for strategy,result in by_uav[uav]:
            drop=drop_point(strategy);burst=result.burst_point_m
            row_values=[uav,strategy.heading_deg,strategy.speed_m_s,strategy.bomb_no,*drop,*burst,result.duration_s,strategy.missile]
            # The official table contains coordinates that are also used to
            # reconstruct sub-millisecond fuse delays.  Six decimals are not
            # sufficient when the vertical displacement is O(1e-6 m), so Q5
            # retains nine decimals while still writing plain numeric cells.
            for column,value in zip("ABCDEFGHIJKL",row_values):values[f"{column}{row}"]=round(float(value),9) if isinstance(value,(float,np.floating)) else value
            row+=1
    return fill_excel_template(TEMPLATE,RESULTS/"result3.xlsx","Sheet1",values)


def write_outputs(solution):
    export_result3(solution);rows=[]
    for strategy,result in zip(solution["strategies"],solution["results"]):
        rows.append({"uav":strategy.uav,"missile":strategy.missile,"bomb_no":strategy.bomb_no,"heading_deg":strategy.heading_deg,"speed_m_s":strategy.speed_m_s,"drop_time_s":strategy.drop_time_s,"delay_s":strategy.delay_s,"burst_time_s":strategy.burst_time_s,"duration_s":result.duration_s,"intervals_s":str(result.intervals_s)})
    frame=pd.DataFrame(rows).sort_values(["uav","bomb_no"]);frame.to_csv(RESULTS/"q5_strategy.csv",index=False)
    missile_rows=[{"missile":m,"duration_s":solution["duration_by_missile"][m],"intervals_s":str(solution["intervals_by_missile"][m])} for m in MISSILES];pd.DataFrame(missile_rows).to_csv(RESULTS/"q5_missile_intervals.csv",index=False)
    payload={"assignment":{route["uav"]:route["missile"] for route in solution["routes"]},"duration_by_missile_s":solution["duration_by_missile"],"intervals_by_missile_s":solution["intervals_by_missile"],"total_duration_s":solution["total_duration_s"],"pruning":solution["pruning"],"branch_stats":solution["branch_stats"],"elapsed_s":solution["elapsed_s"]};(RESULTS/"q5_result.json").write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8");(RESULTS/"q5_validation.txt").write_text(solution["validation"].render(),encoding="utf-8")
    figdir=RESULTS/"figures";orig=RESULTS/"origin_data";figdir.mkdir(parents=True,exist_ok=True);orig.mkdir(parents=True,exist_ok=True)
    use_paper_style();fig,ax=plt.subplots(figsize=(7.0,3.4));y=0;yticks=[];labels=[]
    for missile in MISSILES:
        for left,right in solution["intervals_by_missile"][missile]:ax.barh(y,right-left,left=left,height=.55,color=COLORS[MISSILES.index(missile)])
        yticks.append(y);labels.append(missile);y+=1
    ax.set(yticks=yticks,yticklabels=labels,xlabel="Time after detection (s)",title="Q5 union intervals by missile");ax.grid(True,axis="x",color="#D9D9D9",linewidth=.5);fig.tight_layout();save_figure(fig,figdir/"q5_missile_intervals");plt.close(fig)
    matrix=np.zeros((len(UAVS),len(MISSILES)));assignment=payload["assignment"]
    for i,uav in enumerate(UAVS):matrix[i,MISSILES.index(assignment[uav])]=1
    use_paper_style();fig,ax=plt.subplots(figsize=(4.6,3.2));image=ax.imshow(matrix,cmap="Blues",vmin=0,vmax=1);ax.set(xticks=range(3),xticklabels=MISSILES,yticks=range(5),yticklabels=UAVS,xlabel="Assigned missile",ylabel="UAV",title="Q5 discrete assignment");fig.tight_layout();save_figure(fig,figdir/"q5_assignment");plt.close(fig)
    export_origin_table(orig/"q5_strategy.xlsx",frame.drop(columns="intervals_s"),x_column="uav",metadata={"purpose":"Q5 15-bomb strategy","total_duration_s":str(solution["total_duration_s"])});export_origin_table(orig/"q5_missile_intervals.xlsx",pd.DataFrame(missile_rows).drop(columns="intervals_s"),x_column="missile",metadata={"purpose":"Q5 per-missile union duration"})


def main():
    parser=argparse.ArgumentParser();parser.add_argument("--mode",choices=tuple(PROFILES),default="FINAL");parser.add_argument("--no-cache",action="store_true");args=parser.parse_args();solution=optimize_q5(args.mode,use_cache=not args.no_cache);write_outputs(solution);print(f"Q5 total={solution['total_duration_s']:.9f} s; by missile={solution['duration_by_missile']}");print(solution["validation"].render())


if __name__=="__main__":main()
