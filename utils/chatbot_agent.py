import re
import pandas as pd
import streamlit as st
from utils.data_loader import (
    load_census, load_funds, load_human_deaths, load_tiger_deaths,
    load_reserves, get_national_trend_df, get_reserves_with_population,
    load_predictions
)

# Standard mappings for flexible matching
STATE_MAPPING = {
    "mp": "Madhya Pradesh",
    "madhya pradesh": "Madhya Pradesh",
    "ap": "Andhra Pradesh",
    "andhra pradesh": "Andhra Pradesh",
    "arunachal": "Arunachal Pradesh",
    "arunachal pradesh": "Arunachal Pradesh",
    "assam": "Assam",
    "bihar": "Bihar",
    "chhattisgarh": "Chhattisgarh",
    "jharkhand": "Jharkhand",
    "karnataka": "Karnataka",
    "kerala": "Kerala",
    "maharashtra": "Maharashtra",
    "mizoram": "Mizoram",
    "odisha": "Odisha",
    "orissa": "Odisha",
    "rajasthan": "Rajasthan",
    "tamil nadu": "Tamil Nadu",
    "tn": "Tamil Nadu",
    "telangana": "Telangana",
    "up": "Uttar Pradesh",
    "uttar pradesh": "Uttar Pradesh",
    "uttarakhand": "Uttarakhand",
    "west bengal": "West Bengal",
    "wb": "West Bengal",
}

def clean_text(text: str) -> str:
    """Normalize text by converting to lowercase and stripping punctuation."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    return text

def find_state(cleaned_query: str):
    """Find and return the official state name matched in the query."""
    # Check for direct multi-word matches first
    for key, value in STATE_MAPPING.items():
        if len(key.split()) > 1 and key in cleaned_query:
            return value
    # Check for single-word matches
    for key, value in STATE_MAPPING.items():
        if len(key.split()) == 1 and re.search(r"\b" + re.escape(key) + r"\b", cleaned_query):
            return value
    return None

def find_reserve(cleaned_query: str):
    """Find and return the official reserve name matched in the query."""
    reserves_df = load_reserves()
    for name in reserves_df["reserve_name"].unique():
        cleaned_name = name.lower().strip()
        if cleaned_name in cleaned_query:
            return name
    return None

def extract_year(cleaned_query: str):
    """Extract a 4-digit year from the query."""
    match = re.search(r"\b(19\d{2}|20\d{2})\b", cleaned_query)
    if match:
        return int(match.group(1))
    return None

def answer_query_rule_based(query: str) -> str:
    """Fallback rule-based Q&A engine logic. Checks intent and returns structured response."""
    cleaned = clean_text(query)
    
    # 1. State + Reserve variables
    state = find_state(cleaned)
    reserve = find_reserve(cleaned)
    year = extract_year(cleaned)

    # ── INTENT I: POPULATION GROWTH VS MORTALITY COMPARISON ──
    if ("growth" in cleaned or "compare" in cleaned) and ("death" in cleaned or "died" in cleaned or "mortality" in cleaned or "poach" in cleaned):
        return (
            "### Tiger Population Growth vs. Mortality Analysis (National Insights):\n\n"
            "- **Population Growth**: Between the 2006 Census (1,411 tigers) and the 2022 Census (3,682 tigers), "
            "the population grew by **2,271 tigers** (an average increase of **~142 tigers per year**).\n"
            "- **Mortality Rate**: The Eyes on Tigers database records a total of **1,000 tiger deaths** between 2012 and 2024, "
            "averaging **~77 recorded deaths per year**.\n"
            "- **Comparison**: The average annual population growth rate (~142/year) is nearly **double** the annual recorded mortality rate (~77/year). "
            "This indicates that high birth/recruitment rates in core habitats are outstripping mortality, resulting in net positive population growth."
        )

    # ── INTENT A: TIGER RESERVES GENERAL INFO ──
    if "how many tiger reserves" in cleaned or "total tiger reserves" in cleaned or "number of tiger reserves" in cleaned:
        reserves = load_reserves()
        total_reserves = len(reserves)
        return (
            f"There are **{total_reserves} official tiger reserves** recorded in the Eyes on Tigers database, "
            f"spanning across multiple states in India."
        )

    if "largest reserve" in cleaned or "largest tiger reserve" in cleaned or "biggest reserve" in cleaned or "biggest tiger reserve" in cleaned:
        reserves = load_reserves()
        reserves["total_area_km2"] = reserves["core_area_km2"] + reserves["buffer_area_km2"]
        largest = reserves.sort_values("total_area_km2", ascending=False).iloc[0]
        return (
            f"The **largest tiger reserve** is **{largest['reserve_name']}** in **{largest['state']}**.\n\n"
            f"- **Core Area**: {largest['core_area_km2']:,} km²\n"
            f"- **Buffer Area**: {largest['buffer_area_km2']:,} km²\n"
            f"- **Total Area**: {largest['total_area_km2']:,} km²"
        )

    if "smallest reserve" in cleaned or "smallest tiger reserve" in cleaned:
        reserves = load_reserves()
        reserves["total_area_km2"] = reserves["core_area_km2"] + reserves["buffer_area_km2"]
        smallest = reserves.sort_values("total_area_km2", ascending=True).iloc[0]
        return (
            f"The **smallest tiger reserve** is **{smallest['reserve_name']}** in **{smallest['state']}**.\n\n"
            f"- **Core Area**: {smallest['core_area_km2']:,} km²\n"
            f"- **Buffer Area**: {smallest['buffer_area_km2']:,} km²\n"
            f"- **Total Area**: {smallest['total_area_km2']:,} km²"
        )

    # ── INTENT H: MODEL PREDICTIONS & RISK ──
    if "predict" in cleaned or "at risk" in cleaned or "performance" in cleaned or "forecast" in cleaned:
        pred = load_predictions()
        
        # Check if query specifies a reserve
        if reserve:
            row = pred[pred["reserve_name"] == reserve]
            if not row.empty:
                val = int(row.iloc[0]["predicted_population"])
                perf = float(row.iloc[0]["performance_index"])
                risk = "Yes" if row.iloc[0]["at_risk"] else "No"
                return (
                    f"### Model Predictions for **{reserve} Tiger Reserve**:\n\n"
                    f"- **Predicted Population**: {val} tigers\n"
                    f"- **Performance Index**: {perf} (higher is better)\n"
                    f"- **Flagged At Risk**: {risk}"
                )
            return f"Prediction data unavailable for reserve **{reserve}**."
        
        # Check general at-risk reserves
        if "at risk" in cleaned or "high risk" in cleaned or "endangered" in cleaned:
            at_risk_list = pred[pred["at_risk"]]["reserve_name"].tolist()
            return f"The following tiger reserves are flagged **at risk** by the prediction models:\n\n" + ", ".join(f"**{r}**" for r in at_risk_list)
            
        # Check top performing reserves
        if "best" in cleaned or "top" in cleaned or "highest" in cleaned or "performance" in cleaned:
            top_perf = pred.sort_values("performance_index", ascending=False).head(5)
            list_items = [f"- **{r['reserve_name']}**: {r['performance_index']}" for _, r in top_perf.iterrows()]
            return f"The **top 5 performing tiger reserves** (highest performance index):\n\n" + "\n".join(list_items)
            
        # General response
        total_at_risk = int(pred["at_risk"].sum())
        return (
            f"The prediction model evaluates **{len(pred)} reserves**:\n\n"
            f"- **Reserves Flagged At Risk**: {total_at_risk} reserves\n"
            f"- **Average Performance Index**: {pred['performance_index'].mean():.2f}"
        )

    # ── INTENT B: SPECIFIC RESERVE DETAILS ──
    if reserve:
        res_pop = get_reserves_with_population(year=2022) # latest pop estimate
        res_row = res_pop[res_pop["reserve_name"] == reserve].iloc[0]
        
        # Check if query asks for area
        if "area" in cleaned or "size" in cleaned or "km2" in cleaned:
            return (
                f"**{reserve} Tiger Reserve** Area Details:\n\n"
                f"- **Core Area**: {res_row['core_area_km2']:,} km²\n"
                f"- **Buffer Area**: {res_row['buffer_area_km2']:,} km²\n"
                f"- **Total Protection Area**: {res_row['core_area_km2'] + res_row['buffer_area_km2']:,} km²"
            )
        # Check if query asks for location
        if "location" in cleaned or "where is" in cleaned or "state" in cleaned or "coordinate" in cleaned:
            return (
                f"**{reserve} Tiger Reserve** is located in **{res_row['state']}**.\n\n"
                f"- **Latitude**: {res_row['latitude']}° N\n"
                f"- **Longitude**: {res_row['longitude']}° E"
            )
        # Check if query asks for population or density
        if "population" in cleaned or "tiger" in cleaned or "how many" in cleaned or "density" in cleaned:
            return (
                f"**{reserve} Tiger Reserve** Population & Density Estimates (2022 Census):\n\n"
                f"- **Estimated Tiger Population**: ~{res_row['population']} tigers\n"
                f"- **Density**: {res_row['density_per_100km2']} tigers per 100 km²\n"
                f"- *Note*: {res_row['note']}."
            )
        
        # General response for reserve
        return (
            f"### {reserve} Tiger Reserve ({res_row['state']})\n\n"
            f"- **Total Area**: {res_row['core_area_km2'] + res_row['buffer_area_km2']:,} km² (Core: {res_row['core_area_km2']:,} km², Buffer: {res_row['buffer_area_km2']:,} km²)\n"
            f"- **Estimated Population (2022)**: ~{res_row['population']} tigers\n"
            f"- **Density**: {res_row['density_per_100km2']} tigers per 100 km²\n"
            f"- **Coordinates**: {res_row['latitude']}° N, {res_row['longitude']}° E"
        )

    # ── INTENT G: RANKINGS & WORST/BEST STATES ──
    if "highest tiger population" in cleaned or "most tiger" in cleaned:
        census = load_census()
        latest = census[census["year"] == 2022].sort_values("population_imputed", ascending=False).iloc[0]
        return f"**{latest['state']}** has the **highest tiger population** with **{int(latest['population_imputed'])}** tigers in the latest 2022 Census."

    if "lowest tiger population" in cleaned or "least tiger" in cleaned:
        census = load_census()
        latest = census[(census["year"] == 2022) & (census["population_imputed"] > 0)].sort_values("population_imputed", ascending=True).iloc[0]
        return f"Among states with active tiger populations, **{latest['state']}** has the **lowest tiger population** with **{int(latest['population_imputed'])}** tigers in the 2022 Census."



    # ── INTENT E: TIGER DEATHS & POACHING ──
    if "tiger death" in cleaned or "tiger mortality" in cleaned or "poach" in cleaned or "tigers died" in cleaned or "tiger died" in cleaned:
        tdeaths = load_tiger_deaths()
        
        if "poach" in cleaned:
            if state:
                state_data = tdeaths[tdeaths["state"] == state]
                if year:
                    row = state_data[state_data["year"] == year]
                    if not row.empty:
                        p_deaths = int(row.iloc[0]["deaths_poaching"])
                        return f"In **{state}**, there were **{p_deaths} tiger deaths due to poaching** recorded in the year **{year}**."
                    return f"Poaching mortality data unavailable for **{state}** in the year **{year}**."
                else:
                    total_p = int(state_data["deaths_poaching"].sum())
                    return f"A total of **{total_p} tiger deaths due to poaching** have been recorded in **{state}** across all monitored years."
            else:
                if year:
                    year_data = tdeaths[tdeaths["year"] == year]
                    if not year_data.empty:
                        total_p = int(year_data["deaths_poaching"].sum())
                        return f"Nationally, there were **{total_p} tiger deaths due to poaching** recorded in the year **{year}**."
                    return f"National poaching mortality data unavailable for the year **{year}**."
                else:
                    total_p = int(tdeaths["deaths_poaching"].sum())
                    return f"A total of **{total_p} tiger deaths due to poaching** have been recorded nationally in the Eyes on Tigers database."
        else:
            if state:
                state_data = tdeaths[tdeaths["state"] == state]
                if year:
                    row = state_data[state_data["year"] == year]
                    if not row.empty:
                        total_d = int(row.iloc[0]["total_deaths_imputed"])
                        poach_d = int(row.iloc[0]["deaths_poaching"])
                        nat_d = int(row.iloc[0]["deaths_natural_other"])
                        return (
                            f"Tiger mortality in **{state}** during **{year}**:\n\n"
                            f"- **Total Deaths**: {total_d}\n"
                            f"- **Poaching**: {poach_d}\n"
                            f"- **Natural / Other Causes**: {nat_d}"
                        )
                    return f"Tiger mortality data unavailable for **{state}** in **{year}**."
                else:
                    total_d = int(state_data["total_deaths_imputed"].sum())
                    poach_d = int(state_data["deaths_poaching"].sum())
                    nat_d = int(state_data["deaths_natural_other"].sum())
                    return (
                        f"Cumulative tiger mortality in **{state}** (all recorded years combined):\n\n"
                        f"- **Total Deaths**: {total_d}\n"
                        f"- **Poaching**: {poach_d}\n"
                        f"- **Natural / Other Causes**: {nat_d}"
                    )
            else:
                if year:
                    year_data = tdeaths[tdeaths["year"] == year]
                    if not year_data.empty:
                        total_d = int(year_data["total_deaths_imputed"].sum())
                        return f"The total national tiger deaths recorded in the year **{year}** was **{total_d}**."
                    return f"National tiger mortality data unavailable for **{year}**."
                else:
                    total_d = int(tdeaths["total_deaths_imputed"].sum())
                    return f"A total of **{total_d:,} tiger deaths** (observed and estimated) are recorded in the Eyes on Tigers database."

    # ── INTENT F: HUMAN DEATHS & CONFLICT ──
    if "human death" in cleaned or "human fatalities" in cleaned or "human attack" in cleaned or "conflict" in cleaned or "people died" in cleaned:
        hdeaths = load_human_deaths()
        
        if state:
            state_data = hdeaths[hdeaths["state"] == state]
            if year:
                row = state_data[state_data["year"] == year]
                if not row.empty:
                    val = int(row.iloc[0]["deaths_imputed"])
                    return f"There were **{val} recorded human fatalities** due to tiger attacks/conflict in **{state}** in **{year}**."
                return f"Human conflict data unavailable for **{state}** in **{year}**."
            else:
                total_h = int(state_data["deaths_imputed"].sum())
                return f"A total of **{total_h} human fatalities** due to tiger attacks have been recorded in **{state}** across all monitored years."
        else:
            if year:
                year_data = hdeaths[hdeaths["year"] == year]
                if not year_data.empty:
                    total_h = int(year_data["deaths_imputed"].sum())
                    return f"The total recorded human fatalities from tiger conflict across all states in **{year}** was **{total_h}**."
                return f"National human conflict statistics unavailable for **{year}**."
            else:
                total_h = int(hdeaths["deaths_imputed"].sum())
                return f"A total of **{total_h:,} human fatalities** from tiger conflict are recorded in the Eyes on Tigers database."

    # ── INTENT C: TIGER POPULATION (STATE OR NATIONAL) ──
    if "population" in cleaned or "how many tiger" in cleaned or "tiger count" in cleaned or "number of tiger" in cleaned:
        census = load_census()
        
        if state:
            # Query population for state
            state_data = census[census["state"] == state]
            if year:
                row = state_data[state_data["year"] == year]
                if not row.empty:
                    val = int(row.iloc[0]["population_imputed"])
                    obs = row.iloc[0]["population"]
                    obs_text = f" (observed: {int(obs)})" if not pd.isna(obs) else " (estimated/imputed)"
                    return f"The tiger population in **{state}** in **{year}** was **{val}**{obs_text}."
                else:
                    return f"Data unavailable for **{state}** in the year **{year}**."
            else:
                # Latest census (2022)
                row_2022 = state_data[state_data["year"] == 2022]
                if not row_2022.empty:
                    val = int(row_2022.iloc[0]["population_imputed"])
                    return f"In the latest **2022 Census**, the tiger population in **{state}** was **{val}**."
                else:
                    return f"Tiger population data unavailable for **{state}**."
        else:
            # National/total queries
            trend = get_national_trend_df()
            if year:
                row = trend[trend["year"] == year]
                if not row.empty:
                    return f"The total national tiger population in **{year}** was **{int(row.iloc[0]['population'])}** tigers."
                else:
                    # Let's sum the state census if it matches census years
                    summed_data = census[census["year"] == year]
                    if not summed_data.empty:
                        val = int(summed_data["population_imputed"].sum())
                        return f"The total estimated national tiger population in **{year}** was **{val}** (summed across all states)."
                    return f"National tiger population data unavailable for **{year}**."
            else:
                # Give latest census pop
                latest_year = trend["year"].max()
                latest_pop = trend[trend["year"] == latest_year].iloc[0]["population"]
                return f"The latest national tiger population (**{latest_year} Census**) is **{int(latest_pop):,}** tigers."

    # ── INTENT D: CONSERVATION FUNDING ──
    if "fund" in cleaned or "budget" in cleaned or "money" in cleaned or "cost" in cleaned or "allocated" in cleaned or "allocation" in cleaned:
        funds = load_funds()
        
        if state:
            state_data = funds[funds["state"] == state]
            if year:
                row = state_data[state_data["year"] == year]
                if not row.empty:
                    total_f = row.iloc[0]["funds_best"]
                    central = row.iloc[0]["funds_central_share"]
                    return (
                        f"Funding details for **{state}** in **{year}**:\n\n"
                        f"- **Total Funding (incl. TPF)**: {total_f:,.2f} Lakhs\n"
                        f"- **Central Government Share**: {central:,.2f} Lakhs"
                    )
                else:
                    return f"Funding data unavailable for **{state}** in **{year}**."
            else:
                total_sum = state_data["funds_best"].sum()
                avg_fund = state_data["funds_best"].mean()
                return (
                    f"Conservation funding details for **{state}** (all recorded years combined):\n\n"
                    f"- **Total Cumulative Funding**: **{total_sum:,.2f} Lakhs**\n"
                    f"- **Annual Average Funding**: {avg_fund:,.2f} Lakhs"
                )
        else:
            try:
                from utils.data_loader import load_funding_geographical_area_year
                agg_df = load_funding_geographical_area_year()
                if year:
                    row = agg_df[agg_df["year"] == year]
                    if not row.empty:
                        total_f = row.iloc[0]["total_funding"]
                        return f"The total conservation funding allocated across all states in **{year}** was **{total_f:,.2f} Lakhs**."
                    return f"National funding data unavailable for the year **{year}**."
                else:
                    total_sum = agg_df["total_funding"].sum()
                    return f"The total cumulative conservation funding allocated across all states in the Eyes on Tigers database is **{total_sum:,.2f} Lakhs**."
            except Exception:
                if year:
                    year_data = funds[funds["year"] == year]
                    if not year_data.empty:
                        total_f = year_data["funds_best"].sum()
                        return f"The total conservation funding allocated across all states in **{year}** was **{total_f:,.2f} Lakhs**."
                    return f"National funding data unavailable for the year **{year}**."
                else:
                    total_sum = funds["funds_best"].sum()
                    return f"The total cumulative conservation funding allocated across all states in the Eyes on Tigers database is **{total_sum:,.2f} Lakhs**."

    # ── DEFAULT FALLBACK (Data Unavailable) ──
    return "I'm sorry, that data is unavailable in the current Eyes on Tigers dashboard records."


def get_context_str() -> str:
    """Load all relevant datasets and compile them into a compact CSV context string."""
    try:
        trend = get_national_trend_df()
        trend_str = trend.to_csv(index=False)

        res = load_reserves()[["reserve_name", "state", "core_area_km2", "buffer_area_km2"]]
        res_str = res.to_csv(index=False)
        
        cen = load_census()[["state", "year", "population_imputed"]]
        cen_str = cen.to_csv(index=False)
        
        funds = load_funds()[["state", "year", "funds_best"]]
        funds_str = funds.to_csv(index=False)
        
        hdeaths = load_human_deaths()[["state", "year", "deaths_imputed"]]
        hdeaths_str = hdeaths.to_csv(index=False)
        
        tdeaths = load_tiger_deaths()[["state", "year", "total_deaths_imputed", "deaths_poaching", "deaths_natural_other"]]
        tdeaths_str = tdeaths.to_csv(index=False)
        
        pred = load_predictions()[["reserve_name", "predicted_population", "performance_index", "at_risk"]]
        pred_str = pred.to_csv(index=False)
        
        context = (
            "=== NATIONAL TIGER POPULATION TRENDS (year, population) ===\n"
            f"{trend_str}\n"
            "=== TIGER RESERVES REFERENCE (reserve_name, state, core_area_km2, buffer_area_km2) ===\n"
            f"{res_str}\n"
            "=== STATE TIGER POPULATIONS (state, year, population_imputed) ===\n"
            f"{cen_str}\n"
            "=== STATE CONSERVATION FUNDING LAKHS (state, year, funds_best) ===\n"
            f"{funds_str}\n"
            "=== HUMAN FATALITIES FROM CONFLICT (state, year, deaths_imputed) ===\n"
            f"{hdeaths_str}\n"
            "=== TIGER MORTALITY BY CAUSE (state, year, total_deaths_imputed, deaths_poaching, deaths_natural_other) ===\n"
            f"{tdeaths_str}\n"
            "=== MODEL PREDICTIONS AND RISK FOR RESERVES (reserve_name, predicted_population, performance_index, at_risk) ===\n"
            f"{pred_str}\n"
        )
        return context
    except Exception as e:
        return f"Error loading data context: {str(e)}"


def query_gemini(query: str, api_key: str) -> str:
    """Configures Generative AI with the given api_key and queries Gemini with context."""
    import google.generativeai as genai
    try:
        genai.configure(api_key=api_key)
        context_str = get_context_str()
        
        system_instruction = (
            "You are the Eyes on Tigers (Eyes on Tigers (EoT) Conservation Monitoring System) Conservation Assistant.\n"
            "Your task is to answer user queries accurately based on the provided dataset context.\n"
            "The context includes national tiger population trends, state-level census counts, conservation funding (in Lakhs), tiger mortality (poaching/natural/other), human attacks/deaths from conflict, and reference data for the 58 tiger reserves in India.\n\n"
            "Guidelines:\n"
            "1. Use the provided dataset tables to calculate sums, averages, ratios, percentages, rankings, or lookup specific stats.\n"
            "2. If asked about tiger population growth or comparing growth vs deaths, calculate it by comparing census years (e.g. the 2018 census population of 2,967 vs the 2022 census population of 3,682 to find the net growth of 715 tigers) and compare it to the deaths in the target year.\n"
            "3. If a specific year (like 2023 or 2024) does not have census population data, explain that census data is not available for that year (as censuses are conducted every 4 years, e.g. 2018 and 2022), but provide the mortality/death data for that year and compare it to growth from the nearest census period where relevant.\n"
            "4. Be conversational, direct, and precise. Cite the exact numbers, years, and states when answering.\n"
            "5. If the user asks a question that is completely unrelated to the data or is completely outside the scope of the provided dataset, reply exactly with:\n"
            "\"I'm sorry, that data is unavailable in the current Eyes on Tigers dashboard records.\"\n"
            "6. Do not assume or hallucinate any information outside the provided context. If data is missing or unavailable, explicitly state so rather than making it up.\n"
            "7. Always expand abbreviations if asked (e.g. MP = Madhya Pradesh, UP = Uttar Pradesh, AP = Andhra Pradesh, WB = West Bengal, etc.).\n"
        )
        
        model = genai.GenerativeModel(
            model_name='gemini-3.5-flash',
            system_instruction=system_instruction
        )
        
        prompt = (
            f"=== DATASETS CONTEXT ===\n{context_str}\n\n"
            f"=== USER QUERY ===\n{query}"
        )
        
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Error connecting to Gemini API: {str(e)}"


def answer_query(query: str, api_key: str = None) -> str:
    """Main Q&A engine logic. If an API key is available, calls Gemini; otherwise falls back to rule-based."""
    if not api_key:
        import os
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            try:
                # Safely read secrets, catching missing files/keys
                api_key = st.secrets.get("GEMINI_API_KEY")
            except Exception:
                api_key = None
    
    if api_key:
        return query_gemini(query, api_key)
        
    return answer_query_rule_based(query)
