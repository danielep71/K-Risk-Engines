# 🗺️ Portfolio expansion roadmap

**Planning snapshot: 4 November 2026. Status: proposed direction.**

This document describes potential extensions to K-Risk Engines for independent
benchmarking, model challenge, advisory and education. Candidate names are
working names, not statements that repositories or implementations exist.
The sequence is a recommendation, not a funded delivery schedule.

Existing engine commitments remain in their own repositories. Before activating
a candidate, review those roadmaps and decide whether it belongs in an existing
engine, a shared module or a new repository. This document does not authorize
engine releases or claim regulatory compliance.

## 📍 Starting point

The [portfolio catalogue](../README.md#explore-the-portfolio) covers eight engines:

| Area | Existing projects | Complementary direction |
| --- | --- | --- |
| Counterparty credit risk | K-SACCR, K-SFTs | Collateral and margin analysis |
| Market and CVA risk | K-FRTB-SA, K-CVA | Management risk measures and valuation uncertainty |
| Banking book | K-IRRBB NMDs, K-IRRBB Prepayment Models | Portfolio EVE/NII measurement and CSRBB |
| Liquidity | K-LCR, K-NSFR | Dynamic cash-flow stress and survival horizon |

These are scope descriptions, not implementation-status claims.
See the [portfolio evidence report](PORTFOLIO_STATUS.md) and each engine's own
documentation for availability and limitations.

## 🎯 Recommended sequence

1. **K-IRRBB-EVE-NII:** connect contractual and behavioural cash flows to
   portfolio economic-value and earnings measures.
2. **K-Prudent-Valuation:** provide transparent IPV and AVA calculations with
   traceable assumptions and reconciliation.
3. **K-Liquidity-Stress:** add a dynamic view of cash shortages and buffer
   exhaustion alongside LCR and NSFR.
4. **Further candidates:** select by user demand, input-data availability,
   reuse potential and access to independent validation evidence.

Build a small shared reconciliation capability alongside the first engine.
Avoid starting every candidate simultaneously. K-PD-Calibration is a narrower
alternative starting point when credit modelling and education take priority.
No calendar dates are committed; each activated project needs a scoped
specification and its own milestones.

## 📋 Candidate portfolio

Complexity is a qualitative assessment of an initial benchmark implementation,
not an effort estimate. All entries below are proposals.

| Working name | Main purpose | Initial complexity | Position |
| --- | --- | --- | --- |
| K-IRRBB-EVE-NII | Cash flows, repricing gaps, delta EVE and delta NII | High | First priority |
| K-Prudent-Valuation | Separate IPV and AVA modules with calculation evidence | Medium-high | Second priority |
| K-Liquidity-Stress | Stressed cash flows, usable buffer and survival horizon | Medium | Third priority |
| K-CSRBB | Banking-book credit-spread sensitivities and scenario effects | Medium-high | Follow-on |
| K-Market-Risk | VaR, Expected Shortfall, stress testing and backtesting | Medium | Follow-on |
| K-PD-Calibration | PD estimation, calibration and model diagnostics | Medium | Focused alternative |
| K-IFRS9-ECL | Twelve-month and lifetime expected credit losses | High | Later extension |
| K-Hedge-Effectiveness | Quantitative hedge-effectiveness assessment | Medium | Follow-on |
| K-Collateral | Margin calls, eligibility, haircuts and collateral allocation | Medium-high | Follow-on |
| K-Reconciliation | Explain differences between engines and versions | Medium | Shared foundation |

## 🏦 Priority 1: K-IRRBB-EVE-NII

**Question:** How do changes in interest rates affect portfolio economic value
and net interest income?

### Initial scope

- Import contractual cash flows, repricing dates, instrument conventions and
  baseline and shocked curves.
- Calculate discounted cash flows and delta EVE by instrument, currency and
  time band.
- Calculate twelve-month delta NII with explicit balance-sheet, reinvestment,
  renewal, margin and repricing assumptions.
- Expose intermediate cash flows and scenario contributions for reconciliation.

Start with a limited instrument set and clearly specified assumptions.
A full dynamic ALM platform, commercial planning and complex embedded-option
pricing are outside the first version.

### Dependencies and subsequent scope

Define interfaces to NMD and prepayment outputs before integration, including
units, dates, balances and scenario dependence. A contractual-only prototype
can precede those integrations if its limitations are explicit.

Subsequently add behavioural cash flows, richer balance-sheet assumptions and
supervisory measures under separately documented jurisdiction/version profiles.

### Evidence required

Hand-checkable fixed- and floating-rate instruments; cash-flow conservation;
base-versus-shock reconciliation; tests of repricing and renewal boundaries;
comparison with an independent reference under identical assumptions.

## 🔎 Priority 2: K-Prudent-Valuation

**Question:** What valuation differences and uncertainties explain the proposed
adjustment, and how is double counting avoided?

### Initial scope

Keep two distinct modules:

- **IPV:** import internal valuations and independent observations; compare
  like-for-like prices or parameters; record source quality, timestamps,
  tolerances and investigated differences.
- **AVA:** implement a specifically selected methodology profile, expose each
  supported component and its aggregation, and reconcile relevant existing
  fair-value adjustments.

Start with a bounded instrument universe and documented observation rules.
An IPV difference is not automatically an AVA; the two calculations need
separate definitions and evidence.

### Dependencies and subsequent scope

Requires consistent valuation units, independent data, position mapping and a
versioned methodology. Broader AVA components and portfolios follow only after
their inputs and treatment are specified. No automatic accounting posting or
production valuation approval is included in the initial scope.

### Evidence required

Small portfolios with independently reproduced adjustments, tests of
aggregation and overlap treatment, and a traceable record from observations
through assumptions to the final result.

## 💧 Priority 3: K-Liquidity-Stress

**Question:** On which day does a cash deficit arise, how large is it, and what
causes it?

### Initial scope

- Daily contractual inflows and outflows by currency.
- Configurable deposit runoff, funding non-renewal, margin calls and haircuts.
- Usable liquidity buffer with explicit encumbrance, monetisation timing and
  restrictions on transfer or currency conversion.
- Cumulative cash position, first shortfall date, maximum funding need and
  survival horizon, with driver attribution.

### Dependencies and subsequent scope

Reuse classifications from LCR/NSFR where appropriate without equating their
regulatory weights with behavioural stress assumptions. Begin with deterministic
scenarios; add management actions, reverse stress and collateral integration
later. Avoid double counting assets as both available buffer and pledged
collateral.

### Evidence required

Cash conservation, timing and currency tests; hand-calculated depletion
examples; reconciliation between baseline and stress; explicit treatment of a
horizon with no observed shortfall.

## 🧩 Further candidates

### K-CSRBB

Start with spread sensitivities and economic-value changes for a clearly defined
banking-book portfolio. Document the separation of risk-free rates, spread
components and default/migration effects. Add earnings effects only with
explicit recognition and balance-sheet assumptions. Reuse EVE/NII interfaces
where suitable; consider a module rather than a separate repository.

### K-Market-Risk

Start with historical and parametric VaR/ES, deterministic stress scenarios and
VaR backtesting on imported returns, exposures or P&L series. Specify horizon,
confidence level, weighting, missing-data treatment and quantile conventions.
Add Monte Carlo and broader revaluation later. This is a management-risk engine;
it does not duplicate FRTB-SA or represent an approved internal-model approach.

### K-PD-Calibration

Start with logistic regression, intercept recalibration, discrimination,
calibration diagnostics and stability analysis. Support rare-event and sampled
data treatments only where their statistical assumptions are documented.
Use independent numerical comparisons and out-of-sample evidence.
This can precede ECL, but estimated PDs are not automatically suitable for
IFRS 9 or regulatory capital.

### K-IFRS9-ECL

Begin with imported, validated PD term structures, LGD, EAD and scenario weights,
plus externally supplied stage assignments. Calculate twelve-month and lifetime
ECL with explicit timing, survival and discounting conventions.
Distinguish marginal from cumulative PDs. Add staging/SICR, forward-looking
calibration and parameter estimation as separately validated extensions.

### K-Hedge-Effectiveness

Start with defined hedge relationships, hedge ratios and transparent
quantitative comparisons, including dollar-offset and regression diagnostics
where appropriate. Add hypothetical-derivative calculations and explanations of
ineffectiveness later. Specify the accounting framework; quantitative results
alone do not establish hedge-accounting eligibility.

### K-Collateral

Start with agreement terms, imported exposures, margin calls, eligible assets,
haircuts, settlement timing and available inventory. Add allocation optimisation
after the operational constraints are specified. Keep VM, IM and liquidity
effects distinct and reconcile with SA-CCR/SFT inputs without implying that
their regulatory exposure measures are contractual margin-call amounts.

### K-Reconciliation

Implement reusable imports, canonical identifiers, units, absolute/relative
tolerances and intermediate-result comparisons. Attribute differences to input,
mapping, parameter version, numerical convention or aggregation where the
evidence supports it; leave unexplained differences explicitly unresolved.
Initially deliver this as a shared component. A separate repository is optional.

## 🧮 Conditional workstream: Initial Margin / ISDA SIMM

A sensitivity-based Initial Margin benchmark is an additional candidate from
the portfolio discussion. Its first boundary would be importing sensitivities,
including CRIF-compatible inputs, rather than building a complete derivatives
pricing library.

Proposed progression:

1. Interest-rate and FX delta, concentration and transparent aggregation.
2. Vega and curvature for the supported risk classes.
3. Equity, commodity and credit coverage.
4. Incremental-margin and parameter-version comparisons.

Unsupported inputs must stop the calculation rather than silently produce an
apparently complete margin. Parameters require version and effective-date
control, and results require independent benchmark evidence.

**Publication gate:** clarify applicable ISDA permissions for implementation,
parameter distribution, documentation and naming before committing to a public
SIMM deliverable. Public access to methodology does not establish unrestricted
reuse rights, and an educational label is not evidence of an exemption.
Record the applicable permissions in the implementation repository.
This is a conditional proposal, not a licensing determination.

## 🏗️ Shared implementation principles

- **Excel/VBA first:** use transparent workbook inputs and outputs, with
  calculations in memory and exported source suitable for version control.
  Establish a supported Excel platform and measure practical volume limits.
- **Separate layers:** distinguish input validation, methodology parameters,
  calculation logic and reporting.
- **Reusable numerical components:** assess existing portfolio libraries before
  adding calendars, day counts, cash-flow generation, curves, scenarios or
  statistical routines.
- **Versioned contracts:** specify identifiers, units, currencies, valuation
  dates, sign conventions, aggregation boundaries and treatment of missing data.
  Model-specific sensitivities must not be assumed interchangeable.
- **Reproducible runs:** record input snapshots, methodology and parameter
  versions, code version, assumptions and intermediate results.
- **Independent evidence:** combine hand-worked cases and external/reference
  comparisons with boundary and numerical tests. Agreement alone does not
  establish model validity.
- **Scale when needed:** consider a Python engine behind Excel for workloads
  that exceed measured VBA limits; do not add a second implementation solely
  for architectural symmetry.
- **Safe examples:** distribute synthetic or appropriately reusable data.

## ✅ Activation and completion criteria

Before a candidate becomes an active project:

1. Check overlap with existing engine roadmaps and select repository ownership.
2. Define users, decisions supported, initial inputs/outputs and exclusions.
3. Specify the applicable methodology and any jurisdiction/version profile.
4. Confirm data and intellectual-property permissions.
5. Identify an independent validation reference and acceptance tolerances.
6. Create engine-level issues and milestones with realistic dependencies.

An initial benchmark is ready for release only when its documented scope is
implemented, invalid or unsupported inputs are handled explicitly, required
checks pass, and validation evidence and limitations accompany a reproducible
example. Release availability does not imply production readiness or regulatory
approval.

The maintainer should revisit priorities after each initial benchmark and when
data availability or user needs change. Follow the hub's
[governance](../GOVERNANCE.md) for portfolio inclusion and publication.
