"""
Damodaran DCF Valuation Models
==============================
Implements:
  - Model Selector (model1.xls logic) with full Q&A trail
  - DDM   (Stable, 2-stage, 3-stage) with year-by-year tables
  - FCFE  (Stable, 2-stage, 3-stage) with year-by-year tables
  - FCFF  (Stable, 2-stage, 3-stage) with year-by-year tables

Every model returns:
  - intrinsic value
  - year_by_year: list of dicts (one per year) for tabular display
  - summary: key aggregates
"""

import numpy as np


# ═════════════════════════════════════════════════════════════════════════════
#  MODEL SELECTOR with full decision trail
# ═════════════════════════════════════════════════════════════════════════════

def choose_valuation_model(inputs: dict) -> dict:
    """
    Replicates Damodaran's 'Choosing the Right Valuation Model' (model1.xls).

    Returns the model choice, full Q&A decision trail, and a detailed rationale
    explaining:
      - WHY this model was chosen (with data-driven reasoning)
      - WHY alternative models were rejected
      - Key assumptions and their academic/empirical basis
      - Sensitivity flags and caveats
    """

    economy_growth = inputs.get("inflation_rate", 0.03) + inputs.get("real_growth_rate", 0.02)
    firm_g = inputs.get("firm_growth_rate", 0.08)
    dr = inputs.get("debt_ratio", 0.30)
    cur = inputs.get("currency", "$")
    unit = inputs.get("unit", "")

    # Compute FCFE
    fcfe = (
        inputs.get("net_income", 0)
        - (inputs.get("capex", 0) - inputs.get("depreciation", 0)) * (1 - dr)
        - inputs.get("delta_wc", 0) * (1 - dr)
    )

    # ── Build Q&A trail ─────────────────────────────────────────────────────
    qa = []
    qa.append({
        "question": "Level of Earnings",
        "answer": f"{cur}{inputs.get("net_income", 0):,.0f} {unit}",
    })
    qa.append({
        "question": "Are your earnings positive?",
        "answer": "Yes" if inputs.get("earnings_positive", True) else "No",
    })

    if inputs.get("earnings_positive", True):
        qa.append({
            "question": "What is the expected inflation rate in the economy?",
            "answer": f"{inputs.get("inflation_rate", 0.03):.2%}",
        })
        qa.append({
            "question": "What is the expected real growth rate in the economy?",
            "answer": f"{inputs.get("real_growth_rate", 0.02):.2%}",
        })
        qa.append({
            "question": "Implied nominal growth rate of the economy (inflation + real growth)?",
            "answer": f"{economy_growth:.2%}",
        })
        qa.append({
            "question": "What is the expected growth rate in earnings for this firm?",
            "answer": f"{firm_g:.2%}",
        })
        qa.append({
            "question": "Does this firm have a significant and sustainable competitive advantage?",
            "answer": "Yes" if inputs.get("has_competitive_adv", False) else "No",
            "note": ("Differential advantages include: legal monopoly, technological edge, "
                     "strong brand name, economies of scale, or network effects — both existing and future."),
        })
    else:
        qa.append({
            "question": "Are the earnings negative because the firm is in a cyclical business?",
            "answer": "Yes" if inputs.get("cyclical_negative") else "No",
        })
        qa.append({
            "question": "Are the earnings negative because of a one-time or temporary occurrence?",
            "answer": "Yes" if inputs.get("temporary_negative") else "No",
        })
        qa.append({
            "question": "Are the earnings negative because the firm has too much debt?",
            "answer": "Yes" if inputs.get("excess_debt_negative") else "No",
        })
        if inputs.get("excess_debt_negative"):
            qa.append({
                "question": "If yes, is there a strong likelihood of bankruptcy?",
                "answer": "Yes" if inputs.get("bankruptcy_likely") else "No",
            })
        qa.append({
            "question": "Are the earnings negative because the firm is just starting up?",
            "answer": "Yes" if inputs.get("startup_negative") else "No",
        })

    # Financial leverage
    qa.append({
        "section": "Financial Leverage",
        "question": "What is the current debt ratio (in market value terms)?",
        "answer": f"{dr:.2%}",
    })
    qa.append({
        "question": "Is this debt ratio expected to change significantly?",
        "answer": "Yes" if inputs.get("debt_ratio_changing", False) else "No",
    })

    # Dividend policy
    qa.append({
        "section": "Dividend Policy",
        "question": "What did the firm pay out as dividends in the current year?",
        "answer": f"{cur}{inputs.get("dividends", 0):,.2f} {unit}",
    })
    qa.append({
        "question": "Can you estimate capital expenditures and working capital requirements?",
        "answer": "Yes" if inputs.get("can_estimate_capex", True) else "No",
    })

    # FCFE computation trail
    qa.append({
        "section": "FCFE Computation",
        "question": "Net Income (NI)",
        "answer": f"{cur}{inputs.get("net_income", 0):,.2f}",
    })
    qa.append({
        "question": "Depreciation and Amortization",
        "answer": f"{cur}{inputs.get("depreciation", 0):,.2f}",
    })
    qa.append({
        "question": "Capital Spending (incl. acquisitions)",
        "answer": f"{cur}{inputs.get("capex", 0):,.2f}",
    })
    qa.append({
        "question": "Δ Non-cash Working Capital (ΔWC)",
        "answer": f"{cur}{inputs.get("delta_wc", 0):,.2f}",
    })
    qa.append({
        "question": "FCFE = NI - (CapEx - Dep)×(1-DR) - ΔWC×(1-DR)",
        "answer": f"{cur}{fcfe:,.2f}",
        "formula": (f"= {inputs.get("net_income", 0):,.2f} "
                    f"- ({inputs.get("capex", 0):,.2f} - {inputs.get("depreciation", 0):,.2f})×(1-{dr:.4f}) "
                    f"- {inputs.get("delta_wc", 0):,.2f}×(1-{dr:.4f})"),
    })

    # ── Decision logic ──────────────────────────────────────────────────────
    result = {
        "model_type": "",
        "earnings_level": "",
        "cashflow_type": "",
        "growth_period": "",
        "growth_pattern": "",
        "model_code": "",
        "model_description": "",
        "decision_trail": [],
        "detailed_rationale": [],   # ← NEW: rich explanation paragraphs
        "rejected_alternatives": [], # ← NEW: why other models were ruled out
        "key_assumptions": [],       # ← NEW: list of critical assumption justifications
        "qa_inputs": qa,
    }

    trail = []
    rationale = []   # Verbose explanations
    rejected  = []   # Why alternatives were rejected
    assumptions = [] # Key modelling assumptions

    # ════════════════════════════════════════════════════════════════════════
    #  DECISION 1: Earnings Level — Can we use current earnings?
    # ════════════════════════════════════════════════════════════════════════
    div_payout = inputs.get("dividends", 0)

    if inputs.get("earnings_positive", True):
        result["model_type"] = "Discounted CF Model"
        result["earnings_level"] = "Current Earnings"
        trail.append("✅ Earnings are positive — Discounted Cash Flow model using current earnings.")
        rationale.append(
            f"📘 EARNINGS BASIS: The firm reported positive net income of {cur}{inputs.get("net_income", 0):,.0f} {unit}. "
            f"Per Damodaran's framework (Investment Valuation, Ch. 12), when current earnings are positive "
            f"and expected to persist, they serve as the starting point for projecting future cash flows. "
            f"No normalization is needed — we use current earnings directly."
        )
    else:
        rationale.append(
            f"📘 EARNINGS BASIS: Net income is negative ({cur}{inputs.get("net_income", 0):,.0f} {unit}). "
            f"Using negative earnings directly in a DCF would produce meaningless negative valuations. "
            f"Damodaran prescribes identifying the ROOT CAUSE of negative earnings to determine the "
            f"appropriate treatment."
        )
        if inputs.get("cyclical_negative") or inputs.get("temporary_negative"):
            result["model_type"] = "Discounted CF Model"
            result["earnings_level"] = "Normalized Earnings"
            trail.append("⚠️ Earnings negative due to cyclical/temporary factors → Normalized earnings DCF.")
            rationale.append(
                "🔄 NORMALIZATION REQUIRED: Earnings are negative due to cyclical/temporary factors. "
                "Damodaran recommends normalizing by using average earnings across the business cycle "
                "(typically 5-7 years) or estimating 'mid-cycle' margins and applying them to current revenue. "
                "This prevents over-penalizing the firm for a temporary downturn."
            )
            rejected.append(
                "❌ REJECTED — Direct use of current negative earnings: Would produce a negative intrinsic "
                "value, which is economically incorrect for a solvent going concern."
            )
        elif inputs.get("excess_debt_negative"):
            if inputs.get("bankruptcy_likely"):
                result["model_type"] = "Option Pricing Model"
                result["earnings_level"] = "Current Earnings"
                trail.append("🔴 High bankruptcy risk → Option Pricing Model recommended (beyond standard DCF scope).")
                rationale.append(
                    "☠️ BANKRUPTCY RISK: The firm has negative earnings AND significant excess debt with high "
                    "bankruptcy likelihood. Standard DCF models break down here because equity has option-like "
                    "payoffs. Damodaran recommends the Black-Scholes option pricing model where equity = call "
                    "option on firm assets. Note: We will approximate with FCFF DCF, but interpret with caution."
                )
                rejected.append(
                    "❌ REJECTED — Standard FCFF/FCFE models: Mathematically yield negative or near-zero equity "
                    "values without capturing the option value of equity when the firm is near distress."
                )
            else:
                result["model_type"] = "Discounted CF Model"
                result["earnings_level"] = "Normalized Earnings"
                trail.append("⚠️ Excess debt causing losses, but no bankruptcy risk → Normalized earnings.")
                rationale.append(
                    "💸 EXCESS DEBT, NO BANKRUPTCY: Earnings are depressed by heavy interest charges, "
                    "not by operational failure. Normalizing the capital structure (computing earnings "
                    "at a reasonable debt level) gives a better picture of operating profitability. "
                    "We project EBIT-based cash flows and apply a WACC that reflects the target structure."
                )
        elif inputs.get("startup_negative"):
            result["model_type"] = "Discounted CF Model"
            result["earnings_level"] = "Current Earnings"
            trail.append("⚠️ Startup / early-stage with negative earnings → Revenue growth DCF path.")
            rationale.append(
                "🚀 STARTUP / NEGATIVE EARNINGS: This is an early-stage firm with negative earnings typical "
                "of the investment/growth phase. Damodaran's startup valuation approach focuses on: "
                "(1) Total Addressable Market and market share path, "
                "(2) Operating margin trajectory as scale is reached, "
                "(3) Time to positive FCFF, and "
                "(4) Probability of survival as a risk adjustment. "
                "We use a forward-looking FCFF model anchored to revenue projections."
            )
            rejected.append(
                "❌ REJECTED — DDM / FCFE models: Dividends are zero; FCFE is deeply negative with no "
                "near-term path to recovery. FCFF better captures enterprise value via projected operating margins."
            )
        else:
            result["model_type"] = "Discounted CF Model"
            result["earnings_level"] = "Normalized Earnings"
            trail.append("⚠️ Earnings negative (reason unclear) → Normalize before DCF.")
            rationale.append(
                "❓ NEGATIVE EARNINGS (OTHER): The cause is unclear from available data. Normalizing earnings "
                "to a sustainable level is the prudent approach. We will project FCFF using average industry "
                "margins as a benchmark."
            )

    # ════════════════════════════════════════════════════════════════════════
    #  DECISION 2: What cash flow to discount? (DDM / FCFE / FCFF)
    # ════════════════════════════════════════════════════════════════════════
    debt_ratio_changing = inputs.get("debt_ratio_changing", False)
    can_estimate = inputs.get("can_estimate_capex", True)

    if debt_ratio_changing:
        result["cashflow_type"] = "FCFF (Value firm)"
        trail.append(
            f"📊 Debt ratio ({dr:.1%}) is changing → FCFF model: value the firm, subtract debt for equity."
        )
        rationale.append(
            f"🏗️ WHY FCFF: The firm's debt ratio ({dr:.1%}) is expected to change materially over time. "
            f"When leverage is in flux, using FCFE (which is levered equity cash flow) would require "
            f"re-estimating the cost of equity every year as the capital structure shifts — introducing "
            f"compounding estimation errors. FCFF discounts pre-debt cash flows at WACC, making it "
            f"LEVERAGE-NEUTRAL. The equity value is simply: Firm Value − Net Debt. "
            f"This is Damodaran's explicit recommendation when D/E is changing (Investment Valuation, Ch. 15)."
        )
        rejected.append(
            f"❌ REJECTED — FCFE model: With a changing debt ratio ({dr:.1%}), the cost of equity changes "
            f"every year. Constant-Ke FCFE discounting becomes mathematically inconsistent and would "
            f"either over- or undervalue the equity depending on the direction of the leverage change."
        )
        rejected.append(
            f"❌ REJECTED — DDM: Even if the firm pays dividends, dividends do not equal free cash flow "
            f"when leverage is changing. A firm can pay out more (or less) than its true free cash flow "
            f"by adjusting debt. DDM would give misleading results."
        )
    elif can_estimate:
        if abs(fcfe) > 0 and abs(fcfe - div_payout) / max(abs(fcfe), 1) > 0.20:
            result["cashflow_type"] = "FCFE (Value equity)"
            diff_pct = abs(fcfe - div_payout) / max(abs(fcfe), 1)
            trail.append(
                f"📊 FCFE ({cur}{fcfe:,.0f}) differs from dividends ({cur}{div_payout:,.0f}) by {diff_pct:.0%} → FCFE model."
            )
            rationale.append(
                f"💰 WHY FCFE: Free Cash Flow to Equity ({cur}{fcfe:,.0f} {unit}) differs materially from "
                f"dividends paid ({cur}{div_payout:,.0f} {unit}) — a gap of {diff_pct:.0%}. "
                f"This divergence signals that the firm is RETAINING cash beyond its reinvestment needs "
                f"(or paying dividends it cannot fully support). "
                f"Damodaran's rule: when dividends ≠ FCFE, the DDM will either OVERVALUE (if div > FCFE, "
                f"which is unsustainable) or UNDERVALUE (if div < FCFE, ignoring cash accumulation) the firm. "
                f"FCFE gives the TRUE equity value by measuring what the firm COULD pay, not what it actually pays."
            )
            rejected.append(
                f"❌ REJECTED — DDM: Dividends ({cur}{div_payout:,.0f}) are {diff_pct:.0%} away from FCFE "
                f"({cur}{fcfe:,.0f}). Using actual dividends would systematically misprice the equity."
            )
            rejected.append(
                f"❌ REJECTED — FCFF: Debt ratio ({dr:.1%}) is stable. FCFF → equity requires subtracting "
                f"debt at a fixed capital structure, adding unnecessary complexity with no analytical benefit "
                f"over the more direct FCFE approach."
            )
        else:
            result["cashflow_type"] = "Dividends"
            diff_pct = abs(fcfe - div_payout) / max(abs(fcfe), 1)
            trail.append(
                f"📊 Dividends ({cur}{div_payout:,.0f}) ≈ FCFE ({cur}{fcfe:,.0f}) within {diff_pct:.0%} → DDM."
            )
            rationale.append(
                f"💵 WHY DDM (Dividend Discount Model): Dividends paid ({cur}{div_payout:,.0f} {unit}) "
                f"closely approximate FCFE ({cur}{fcfe:,.0f} {unit}) — difference of only {diff_pct:.0%}. "
                f"When a firm pays out its free cash flows as dividends, the DDM is not only simpler "
                f"but MORE RELIABLE — it requires fewer assumptions about reinvestment rates. "
                f"Damodaran calls this the 'clean' valuation case: the observable cash flow (dividends) "
                f"equals the theoretical cash flow (FCFE). "
                f"This is common for mature, stable firms with consistent dividend policies (e.g., utilities, "
                f"consumer staples, mature banks)."
            )
            rejected.append(
                f"❌ REJECTED — FCFE: Since dividends ≈ FCFE (within {diff_pct:.0%}), FCFE would give "
                f"essentially the same result as DDM but with more assumptions (capex, working capital). "
                f"DDM is simpler and equally accurate here."
            )
    else:
        result["cashflow_type"] = "Dividends"
        trail.append("📊 CapEx/WC not estimable → Default to DDM.")
        rationale.append(
            "💵 WHY DDM (DEFAULT): Capital expenditure and working capital data are unavailable, "
            "making FCFE/FCFF computation impossible. The Dividend Discount Model relies only on "
            "observable dividends and requires no capex estimation. This is Damodaran's fallback "
            "when reinvestment data is incomplete."
        )

    # ════════════════════════════════════════════════════════════════════════
    #  DECISION 3: Growth Stage — Stable / Two-Stage / Three-Stage
    # ════════════════════════════════════════════════════════════════════════
    growth_multiple = firm_g / economy_growth if economy_growth > 0 else 1.0

    if firm_g <= economy_growth * 1.1:
        result["growth_period"] = "Stable"
        result["growth_pattern"] = "Stable Growth"
        trail.append(
            f"📈 Firm growth ({firm_g:.1%}) ≤ 110% of economy ({economy_growth:.1%}) → Stable (Gordon) model."
        )
        rationale.append(
            f"📉 WHY STABLE MODEL: The firm's expected growth ({firm_g:.1%}) is at or near the economy's "
            f"long-run nominal growth rate ({economy_growth:.1%}). A firm cannot sustainably grow faster "
            f"than the economy INDEFINITELY — eventually, it would become the entire economy. "
            f"When the firm is ALREADY at its terminal growth rate, a single-stage perpetuity model "
            f"(Gordon Growth Model) is both appropriate and parsimonious. "
            f"The key input is the terminal growth rate g = {firm_g:.1%}, which must be ≤ nominal GDP growth. "
            f"Damodaran cautions that even mature firms should not use g > inflation rate unless they have "
            f"documented pricing power."
        )
        rejected.append(
            f"❌ REJECTED — Two/Three-Stage models: The firm is already growing at the stable rate "
            f"({firm_g:.1%} ≈ {economy_growth:.1%} economy). Adding a high-growth phase would be "
            f"analytically unjustified and would overstate intrinsic value."
        )
    elif firm_g <= economy_growth * 2.0:
        result["growth_period"] = "5 to 10 years"
        result["growth_pattern"] = "Two-stage Growth"
        trail.append(
            f"📈 Firm growth ({firm_g:.1%}) is {growth_multiple:.1f}× economy ({economy_growth:.1%}) → Two-stage model."
        )
        rationale.append(
            f"📈 WHY TWO-STAGE MODEL: The firm is growing at {firm_g:.1%} — approximately "
            f"{growth_multiple:.1f}× the economy's nominal rate of {economy_growth:.1%}. "
            f"This level of above-average growth is MODERATE and typical of established firms in "
            f"mid-cycle expansion. Empirically, most above-average growth reverts to GDP growth within "
            f"5–10 years (Damodaran cites mean-reversion evidence across 10,000+ firms). "
            f"The two-stage model captures: Phase 1 = high-growth period (7 years used) at {firm_g:.1%}, "
            f"then abrupt transition to stable growth of {inputs.get("stable_growth", inputs.get("inflation_rate",0.03) + inputs.get("real_growth_rate",0.02)*0.5):.1%}. "
            f"This is the most widely used model for 'normal' high-growth firms."
        )
        rejected.append(
            f"❌ REJECTED — Stable model: Growth ({firm_g:.1%}) is {(firm_g/economy_growth - 1):.0%} above "
            f"economy — too high for a one-stage perpetuity. Using stable model would undervalue the firm "
            f"by ignoring the above-average growth period."
        )
        rejected.append(
            f"❌ REJECTED — Three-stage model: Growth ({firm_g:.1%}) is not extreme enough relative to "
            f"economy ({economy_growth:.1%}) to justify a three-phase model with an explicit transition period. "
            f"The abrupt two-stage cut is a reasonable approximation."
        )
    else:
        if inputs.get("has_competitive_adv", False):
            result["growth_period"] = "10 or more years"
            result["growth_pattern"] = "Three-stage Growth"
            trail.append(
                f"📈 Firm growth ({firm_g:.1%}) >> economy ({economy_growth:.1%}) AND sustainable competitive "
                f"advantage → Three-stage model (high → transition → stable)."
            )
            rationale.append(
                f"🚀 WHY THREE-STAGE MODEL: The firm is growing at {firm_g:.1%} — {growth_multiple:.1f}× the "
                f"economy — AND has confirmed sustainable competitive advantages. "
                f"A sudden drop from {firm_g:.1%} to {inputs.get("stable_growth", inputs.get("inflation_rate",0.03) + inputs.get("real_growth_rate",0.02)*0.5):.1%} (as in a two-stage model) "
                f"would be unrealistic for a firm with pricing power and barriers to entry. "
                f"The three-stage model adds a TRANSITION PHASE where growth linearly declines from "
                f"{firm_g:.1%} → {inputs.get("stable_growth", inputs.get("inflation_rate",0.03) + inputs.get("real_growth_rate",0.02)*0.5):.1%}, reflecting the competitive dynamics of "
                f"margins gradually normalizing as the market matures. "
                f"Damodaran uses this for firms like FANG tech companies, dominant platform businesses, "
                f"and capital-light compounders with decades-long competitive moats."
            )
            rejected.append(
                f"❌ REJECTED — Two-stage model: For a firm with durable competitive advantages and "
                f"{firm_g:.1%} growth, an abrupt transition would understate value by ignoring the gradual "
                f"fade period. Firms with moats do not lose competitive advantage overnight."
            )
        else:
            result["growth_period"] = "5 to 10 years"
            result["growth_pattern"] = "Two-stage Growth"
            trail.append(
                f"📈 Firm growth ({firm_g:.1%}) >> economy BUT no sustainable competitive advantage "
                f"→ Two-stage (growth fades faster without moat)."
            )
            rationale.append(
                f"⚡ WHY TWO-STAGE DESPITE HIGH GROWTH: The firm is growing rapidly ({firm_g:.1%}) but "
                f"lacks a confirmed sustainable competitive advantage. Without a moat, competitors will "
                f"erode excess returns faster. Damodaran notes that ROIC → WACC convergence occurs "
                f"more rapidly for firms without barriers to entry. A two-stage model with an abrupt "
                f"transition appropriately prices in this mean-reversion risk. "
                f"Had there been a confirmed competitive advantage, a three-stage model would be preferred."
            )
            rejected.append(
                f"❌ REJECTED — Three-stage model: The firm lacks a documented competitive advantage. "
                f"A long transition period ({firm_g:.1%} slowly fading over 10+ years) would overvalue "
                f"the business by crediting a sustained moat that may not materialize."
            )

    # ════════════════════════════════════════════════════════════════════════
    #  KEY ASSUMPTIONS
    # ════════════════════════════════════════════════════════════════════════
    assumptions.append(
        f"📌 Risk-Free Rate: {inputs.get("risk_free_rate", 0.05):.2%} — "
        f"{'Indian 10-year G-Sec yield' if inputs.get("risk_free_rate", 0.05) > 0.05 else 'US 10-year Treasury yield'}. "
        f"Damodaran recommends using a default-free, long-term government bond rate in the same currency "
        f"as the cash flows being discounted."
    )
    assumptions.append(
        f"📌 Equity Risk Premium (ERP): {inputs.get("erp", 0.055):.2%} — "
        f"{'India-specific ERP (higher to reflect emerging market risk, political risk, and liquidity premium)' if inputs.get("erp", 0.055) > 0.055 else 'US market ERP based on Damodaran 2024 estimates (implied ERP from S&P 500 pricing)'}."
    )
    assumptions.append(
        f"📌 Beta: {inputs.get('beta', 'N/A')} (measured) → "
        f"Ke = Rf + β×ERP = {inputs.get("risk_free_rate", 0.05):.2%} + {inputs.get('beta', 1.0):.2f}×{inputs.get("erp", 0.055):.2%} "
        f"= {inputs.get('cost_of_equity', inputs.get("risk_free_rate", 0.05) + inputs.get('beta', 1.0) * inputs.get("erp", 0.055)):.2%}. "
        f"Beta measures systematic market risk. β > 1 → more volatile than market; β < 1 → defensive."
    )
    assumptions.append(
        f"📌 Stable Growth Rate: {inputs.get("stable_growth", inputs.get("inflation_rate",0.03) + inputs.get("real_growth_rate",0.02)*0.5):.2%} — "
        f"Set equal to expected long-run nominal GDP growth "
        f"(inflation {inputs.get("inflation_rate", 0.03):.1%} + real growth {inputs.get("real_growth_rate", 0.02):.1%}). "
        f"Damodaran's hard rule: terminal growth rate CANNOT exceed the risk-free rate, or the firm "
        f"would eventually be worth more than the entire economy."
    )
    if dr > 0.10:
        assumptions.append(
            f"📌 WACC uses market-value debt ratio {dr:.1%}. This is the FORWARD-LOOKING target structure, "
            f"not the book-value ratio. Damodaran insists on market values because book debt ratios "
            f"reflect historical financing decisions, not current economic reality."
        )

    result["decision_trail"] = trail
    result["detailed_rationale"] = rationale
    result["rejected_alternatives"] = rejected
    result["key_assumptions"] = assumptions

    # Map to model code
    cf = result["cashflow_type"]
    pat = result["growth_pattern"]

    model_map = {
        ("Dividends", "Stable Growth"):                 ("ddmst",   "Stable Growth DDM (Gordon Growth Model)"),
        ("Dividends", "Two-stage Growth"):              ("ddm2st",  "Two-Stage Dividend Discount Model"),
        ("Dividends", "Three-stage Growth"):            ("ddm3st",  "Three-Stage Dividend Discount Model"),
        ("FCFE (Value equity)", "Stable Growth"):       ("fcfest",  "Stable Growth FCFE Model"),
        ("FCFE (Value equity)", "Two-stage Growth"):    ("fcfe2st", "Two-Stage FCFE Discount Model"),
        ("FCFE (Value equity)", "Three-stage Growth"):  ("fcfe3st", "Three-Stage FCFE Discount Model"),
        ("FCFF (Value firm)", "Stable Growth"):         ("fcffst",  "Stable Growth FCFF Model"),
        ("FCFF (Value firm)", "Two-stage Growth"):      ("fcff2st", "Two-Stage FCFF Discount Model"),
        ("FCFF (Value firm)", "Three-stage Growth"):    ("fcff3st", "Three-Stage FCFF Discount Model"),
    }

    key = (cf, pat)
    if key in model_map:
        result["model_code"], result["model_description"] = model_map[key]
    else:
        result["model_code"] = "fcff2st"
        result["model_description"] = "Two-Stage FCFF (Default Fallback)"

    trail.append(f"✅ SELECTED MODEL: **{result['model_description']}** (`{result['model_code']}.xls`)")

    return result


# ═════════════════════════════════════════════════════════════════════════════
#  HELPER: compute FCFE & FCFF
# ═════════════════════════════════════════════════════════════════════════════

def compute_fcfe(net_income, depreciation, capex, delta_wc, debt_ratio):
    return net_income - (capex - depreciation) * (1 - debt_ratio) - delta_wc * (1 - debt_ratio)


def compute_fcff(ebit, tax_rate, depreciation, capex, delta_wc):
    return ebit * (1 - tax_rate) + depreciation - capex - delta_wc


# ═════════════════════════════════════════════════════════════════════════════
#  DDM MODELS — with year-by-year tables
# ═════════════════════════════════════════════════════════════════════════════

def ddm_stable(dps, cost_of_equity, stable_growth):
    """Gordon Growth Model with explicit calculation."""
    ke, g = cost_of_equity, stable_growth
    if ke <= g:
        return {"error": "Cost of equity must exceed stable growth rate"}

    dps1 = dps * (1 + g)
    value = dps1 / (ke - g)

    year_by_year = [{
        "Year": "Terminal (∞)",
        "Dividend": dps1,
        "Growth Rate": g,
        "Discount Rate": ke,
        "PV Factor": "1/(Ke-g)",
        "Present Value": value,
    }]

    return {
        "intrinsic_value": value,
        "model": "Stable DDM (Gordon Growth Model)",
        "formula": f"Value = DPS₁ / (Ke - g) = {dps1:,.2f} / ({ke:.4f} - {g:.4f}) = {value:,.2f}",
        "year_by_year": year_by_year,
        "summary": {
            "Current DPS (D₀)": dps,
            "Next Year DPS (D₁)": dps1,
            "Cost of Equity (Ke)": ke,
            "Stable Growth Rate (g)": g,
            "Intrinsic Value per Share": value,
        },
    }


def ddm_two_stage(dps, cost_of_equity, high_growth, stable_growth,
                   high_growth_years=7):
    ke, hg, sg = cost_of_equity, high_growth, stable_growth
    rows = []
    pv_dividends = 0
    current_dps = dps

    for yr in range(1, high_growth_years + 1):
        current_dps *= (1 + hg)
        pv_factor = 1 / ((1 + ke) ** yr)
        pv = current_dps * pv_factor
        pv_dividends += pv
        rows.append({
            "Year": yr,
            "Expected Growth": f"{hg:.2%}",
            "Dividend (DPS)": current_dps,
            "Cost of Equity": f"{ke:.2%}",
            "PV Factor": pv_factor,
            "PV of Dividend": pv,
        })

    terminal_dps = current_dps * (1 + sg)
    terminal_value = terminal_dps / (ke - sg)
    pv_terminal = terminal_value / ((1 + ke) ** high_growth_years)

    rows.append({
        "Year": f"Terminal (Yr {high_growth_years}+)",
        "Expected Growth": f"{sg:.2%} (stable)",
        "Dividend (DPS)": terminal_dps,
        "Cost of Equity": f"{ke:.2%}",
        "PV Factor": 1 / ((1 + ke) ** high_growth_years),
        "PV of Dividend": pv_terminal,
    })

    intrinsic = pv_dividends + pv_terminal

    return {
        "intrinsic_value": intrinsic,
        "model": "Two-Stage DDM",
        "year_by_year": rows,
        "summary": {
            "Current DPS (D₀)": dps,
            "High Growth Rate": hg,
            "High Growth Period": f"{high_growth_years} years",
            "Stable Growth Rate": sg,
            "Cost of Equity": ke,
            "PV of High-Growth Dividends": pv_dividends,
            "Terminal Value": terminal_value,
            "PV of Terminal Value": pv_terminal,
            "Intrinsic Value per Share": intrinsic,
        },
    }


def ddm_three_stage(dps, cost_of_equity, high_growth, stable_growth,
                     high_years=5, transition_years=5):
    ke, hg, sg = cost_of_equity, high_growth, stable_growth
    rows = []
    pv_total = 0
    current_dps = dps
    year = 0

    # Phase 1
    for yr in range(1, high_years + 1):
        current_dps *= (1 + hg)
        pv_factor = 1 / ((1 + ke) ** yr)
        pv = current_dps * pv_factor
        pv_total += pv
        rows.append({
            "Year": yr, "Phase": "High Growth",
            "Growth Rate": f"{hg:.2%}", "DPS": current_dps,
            "PV Factor": pv_factor, "PV of DPS": pv,
        })
        year = yr

    pv_phase1 = pv_total

    # Phase 2
    pv_phase2 = 0
    for i in range(1, transition_years + 1):
        blended = hg - (hg - sg) * (i / transition_years)
        current_dps *= (1 + blended)
        year += 1
        pv_factor = 1 / ((1 + ke) ** year)
        pv = current_dps * pv_factor
        pv_total += pv
        pv_phase2 += pv
        rows.append({
            "Year": year, "Phase": "Transition",
            "Growth Rate": f"{blended:.2%}", "DPS": current_dps,
            "PV Factor": pv_factor, "PV of DPS": pv,
        })

    # Phase 3
    terminal_dps = current_dps * (1 + sg)
    terminal_value = terminal_dps / (ke - sg)
    pv_terminal = terminal_value / ((1 + ke) ** year)

    rows.append({
        "Year": f"Terminal (Yr {year}+)", "Phase": "Stable",
        "Growth Rate": f"{sg:.2%}", "DPS": terminal_dps,
        "PV Factor": 1 / ((1 + ke) ** year), "PV of DPS": pv_terminal,
    })

    intrinsic = pv_total + pv_terminal

    return {
        "intrinsic_value": intrinsic,
        "model": "Three-Stage DDM",
        "year_by_year": rows,
        "summary": {
            "Current DPS (D₀)": dps,
            "High Growth Rate": hg,
            "High Growth Years": high_years,
            "Transition Years": transition_years,
            "Stable Growth Rate": sg,
            "Cost of Equity": ke,
            "PV Phase 1 (High Growth)": pv_phase1,
            "PV Phase 2 (Transition)": pv_phase2,
            "Terminal Value": terminal_value,
            "PV of Terminal Value": pv_terminal,
            "Intrinsic Value per Share": intrinsic,
        },
    }


# ═════════════════════════════════════════════════════════════════════════════
#  FCFE MODELS — with year-by-year tables
# ═════════════════════════════════════════════════════════════════════════════

def fcfe_stable(fcfe_ps, cost_of_equity, stable_growth):
    ke, g = cost_of_equity, stable_growth
    if ke <= g:
        return {"error": "Cost of equity must exceed stable growth rate"}

    fcfe1 = fcfe_ps * (1 + g)
    value = fcfe1 / (ke - g)

    return {
        "intrinsic_value": value,
        "model": "Stable FCFE Model",
        "formula": f"Value = FCFE₁ / (Ke - g) = {fcfe1:,.2f} / ({ke:.4f} - {g:.4f}) = {value:,.2f}",
        "year_by_year": [{
            "Year": "Terminal (∞)",
            "FCFE": fcfe1, "Growth": g, "Ke": ke, "Value": value,
        }],
        "summary": {
            "Current FCFE/share": fcfe_ps,
            "Next Year FCFE/share": fcfe1,
            "Cost of Equity": ke,
            "Stable Growth": g,
            "Intrinsic Value per Share": value,
        },
    }


def fcfe_two_stage(fcfe_ps, cost_of_equity, high_growth, stable_growth,
                    high_years=7):
    ke, hg, sg = cost_of_equity, high_growth, stable_growth
    rows = []
    pv_fcfe = 0
    current = fcfe_ps

    for yr in range(1, high_years + 1):
        current *= (1 + hg)
        pv_factor = 1 / ((1 + ke) ** yr)
        pv = current * pv_factor
        pv_fcfe += pv
        rows.append({
            "Year": yr, "Growth": f"{hg:.2%}", "FCFE/Share": current,
            "PV Factor": pv_factor, "PV of FCFE": pv,
        })

    terminal = current * (1 + sg)
    tv = terminal / (ke - sg)
    pv_tv = tv / ((1 + ke) ** high_years)

    rows.append({
        "Year": f"Terminal (Yr {high_years}+)", "Growth": f"{sg:.2%} (stable)",
        "FCFE/Share": terminal, "PV Factor": 1 / ((1 + ke) ** high_years),
        "PV of FCFE": pv_tv,
    })

    intrinsic = pv_fcfe + pv_tv

    return {
        "intrinsic_value": intrinsic,
        "model": "Two-Stage FCFE Model",
        "year_by_year": rows,
        "summary": {
            "Current FCFE/share": fcfe_ps,
            "High Growth Rate": hg,
            "High Growth Period": f"{high_years} years",
            "Stable Growth Rate": sg,
            "Cost of Equity": ke,
            "PV of High-Growth FCFE": pv_fcfe,
            "Terminal Value": tv,
            "PV of Terminal Value": pv_tv,
            "Intrinsic Value per Share": intrinsic,
        },
    }


def fcfe_three_stage(fcfe_ps, cost_of_equity, high_growth, stable_growth,
                      high_years=5, transition_years=5):
    ke, hg, sg = cost_of_equity, high_growth, stable_growth
    rows = []
    pv_total = 0
    current = fcfe_ps
    year = 0

    pv_p1 = 0
    for yr in range(1, high_years + 1):
        current *= (1 + hg)
        pv_f = 1 / ((1 + ke) ** yr)
        pv = current * pv_f
        pv_total += pv
        pv_p1 += pv
        rows.append({"Year": yr, "Phase": "High Growth", "Growth": f"{hg:.2%}",
                      "FCFE/Share": current, "PV Factor": pv_f, "PV of FCFE": pv})
        year = yr

    pv_p2 = 0
    for i in range(1, transition_years + 1):
        blended = hg - (hg - sg) * (i / transition_years)
        current *= (1 + blended)
        year += 1
        pv_f = 1 / ((1 + ke) ** year)
        pv = current * pv_f
        pv_total += pv
        pv_p2 += pv
        rows.append({"Year": year, "Phase": "Transition", "Growth": f"{blended:.2%}",
                      "FCFE/Share": current, "PV Factor": pv_f, "PV of FCFE": pv})

    terminal = current * (1 + sg)
    tv = terminal / (ke - sg)
    pv_tv = tv / ((1 + ke) ** year)

    rows.append({"Year": f"Terminal (Yr {year}+)", "Phase": "Stable",
                  "Growth": f"{sg:.2%}", "FCFE/Share": terminal,
                  "PV Factor": 1 / ((1 + ke) ** year), "PV of FCFE": pv_tv})

    intrinsic = pv_total + pv_tv

    return {
        "intrinsic_value": intrinsic,
        "model": "Three-Stage FCFE Model",
        "year_by_year": rows,
        "summary": {
            "Current FCFE/share": fcfe_ps,
            "PV Phase 1 (High Growth)": pv_p1,
            "PV Phase 2 (Transition)": pv_p2,
            "Terminal Value": tv,
            "PV of Terminal Value": pv_tv,
            "Intrinsic Value per Share": intrinsic,
        },
    }


# ═════════════════════════════════════════════════════════════════════════════
#  FCFF MODELS — with year-by-year tables
# ══════════════════════════════════════════��══════════════════════════════════

def fcff_stable(fcff, wacc, stable_growth, total_debt=0, cash=0,
                shares_outstanding=1):
    w, g = wacc, stable_growth
    if w <= g:
        return {"error": "WACC must exceed stable growth rate"}

    fcff1 = fcff * (1 + g)
    firm_value = fcff1 / (w - g)
    equity_value = firm_value - total_debt + cash
    per_share = equity_value / shares_outstanding

    return {
        "intrinsic_value_per_share": per_share,
        "firm_value": firm_value,
        "equity_value": equity_value,
        "model": "Stable FCFF Model",
        "formula": f"Firm Value = FCFF₁/(WACC-g) = {fcff1:,.2f}/({w:.4f}-{g:.4f}) = {firm_value:,.2f}",
        "year_by_year": [{
            "Year": "Terminal (∞)", "FCFF": fcff1, "Growth": g,
            "WACC": w, "Firm Value": firm_value,
        }],
        "summary": {
            "Current FCFF": fcff,
            "Next Year FCFF": fcff1,
            "WACC": w,
            "Stable Growth": g,
            "Firm Value": firm_value,
            "(-) Total Debt": total_debt,
            "(+) Cash": cash,
            "Equity Value": equity_value,
            "Shares Outstanding": shares_outstanding,
            "Intrinsic Value per Share": per_share,
        },
    }


def fcff_two_stage(fcff, wacc_high, wacc_stable, high_growth, stable_growth,
                    high_years=7, total_debt=0, cash=0, shares_outstanding=1):
    wh, ws, hg, sg = wacc_high, wacc_stable, high_growth, stable_growth
    rows = []
    pv_fcff = 0
    current = fcff

    for yr in range(1, high_years + 1):
        current *= (1 + hg)
        pv_f = 1 / ((1 + wh) ** yr)
        pv = current * pv_f
        pv_fcff += pv
        rows.append({
            "Year": yr, "Growth": f"{hg:.2%}", "FCFF": current,
            "WACC": f"{wh:.2%}", "PV Factor": pv_f, "PV of FCFF": pv,
        })

    terminal_fcff = current * (1 + sg)
    tv = terminal_fcff / (ws - sg)
    pv_tv = tv / ((1 + wh) ** high_years)

    rows.append({
        "Year": f"Terminal (Yr {high_years}+)", "Growth": f"{sg:.2%} (stable)",
        "FCFF": terminal_fcff, "WACC": f"{ws:.2%}",
        "PV Factor": 1 / ((1 + wh) ** high_years), "PV of FCFF": pv_tv,
    })

    firm_value = pv_fcff + pv_tv
    equity_value = firm_value - total_debt + cash
    per_share = equity_value / shares_outstanding

    return {
        "intrinsic_value_per_share": per_share,
        "firm_value": firm_value,
        "equity_value": equity_value,
        "model": "Two-Stage FCFF Model",
        "year_by_year": rows,
        "summary": {
            "Current FCFF": fcff,
            "High Growth Rate": hg,
            "High Growth Period": f"{high_years} years",
            "WACC (High Growth)": wh,
            "Stable Growth Rate": sg,
            "WACC (Stable)": ws,
            "PV of High-Growth FCFF": pv_fcff,
            "Terminal Value": tv,
            "PV of Terminal Value": pv_tv,
            "Firm Value (Enterprise Value)": firm_value,
            "(-) Total Debt": total_debt,
            "(+) Cash & Equivalents": cash,
            "Equity Value": equity_value,
            "Shares Outstanding": shares_outstanding,
            "Intrinsic Value per Share": per_share,
        },
    }


def fcff_three_stage(fcff, wacc_high, wacc_stable, high_growth, stable_growth,
                      high_years=5, transition_years=5,
                      total_debt=0, cash=0, shares_outstanding=1):
    wh, ws, hg, sg = wacc_high, wacc_stable, high_growth, stable_growth
    rows = []
    pv_total = 0
    current = fcff
    year = 0

    pv_p1 = 0
    for yr in range(1, high_years + 1):
        current *= (1 + hg)
        pv_f = 1 / ((1 + wh) ** yr)
        pv = current * pv_f
        pv_total += pv
        pv_p1 += pv
        rows.append({"Year": yr, "Phase": "High Growth", "Growth": f"{hg:.2%}",
                      "FCFF": current, "WACC": f"{wh:.2%}",
                      "PV Factor": pv_f, "PV of FCFF": pv})
        year = yr

    pv_p2 = 0
    for i in range(1, transition_years + 1):
        bg = hg - (hg - sg) * (i / transition_years)
        bw = wh - (wh - ws) * (i / transition_years)
        current *= (1 + bg)
        year += 1
        pv_f = 1 / ((1 + bw) ** year)
        pv = current * pv_f
        pv_total += pv
        pv_p2 += pv
        rows.append({"Year": year, "Phase": "Transition", "Growth": f"{bg:.2%}",
                      "FCFF": current, "WACC": f"{bw:.2%}",
                      "PV Factor": pv_f, "PV of FCFF": pv})

    terminal = current * (1 + sg)
    tv = terminal / (ws - sg)
    pv_tv = tv / ((1 + ws) ** year)

    rows.append({"Year": f"Terminal (Yr {year}+)", "Phase": "Stable",
                  "Growth": f"{sg:.2%}", "FCFF": terminal, "WACC": f"{ws:.2%}",
                  "PV Factor": 1 / ((1 + ws) ** year), "PV of FCFF": pv_tv})

    firm_value = pv_total + pv_tv
    equity_value = firm_value - total_debt + cash
    per_share = equity_value / shares_outstanding

    return {
        "intrinsic_value_per_share": per_share,
        "firm_value": firm_value,
        "equity_value": equity_value,
        "model": "Three-Stage FCFF Model",
        "year_by_year": rows,
        "summary": {
            "Current FCFF": fcff,
            "PV Phase 1 (High Growth)": pv_p1,
            "PV Phase 2 (Transition)": pv_p2,
            "Terminal Value": tv,
            "PV of Terminal Value": pv_tv,
            "Firm Value (Enterprise Value)": firm_value,
            "(-) Total Debt": total_debt,
            "(+) Cash & Equivalents": cash,
            "Equity Value": equity_value,
            "Shares Outstanding": shares_outstanding,
            "Intrinsic Value per Share": per_share,
        },
    }