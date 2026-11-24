# Finance projects

Finance and quantum projects by **Shubham**, in one repo. Each folder is an independent Python package with its own tests and README.

| Project | What it does | Dashboard |
|---|---|---|
| [quantum-finance](quantum-finance/) | Quantum amplitude estimation for option pricing, and QUBO portfolio selection | [Results dashboard](quantum-finance/docs/dashboard.html) |
| [ib-valuation-toolkit](ib-valuation-toolkit/) | DCF, trading comps, football field, client and banker reports | [Dashboard](https://claude.ai/artifact/M8waQTWb53eg5pKvHcLJgM) |
| [ib-deal-suite](ib-deal-suite/) | LBO returns, merger accretion/dilution, precedent transactions, Excel export | [Dashboard](https://claude.ai/artifact/THobYEwBB14WVvDMguBqWZ) |
| [nvda-valuation](nvda-valuation/) | NVIDIA equity valuation: DCF with perpetuity and exit methods | [Dashboard](https://claude.ai/artifact/FWEEMTjftXmM9tXZJ7NdWq) |

All company data is hypothetical, except the NVIDIA project, which uses its FY2026 filings and labelled assumptions. None of this is investment advice.

## Running everything

```bash
for p in quantum-finance ib-valuation-toolkit ib-deal-suite nvda-valuation; do
  (cd "$p" && pip install -e ".[dev]" && pytest -q)
done
```

## License

MIT. © Shubham
