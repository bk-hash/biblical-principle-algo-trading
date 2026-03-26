# Export BUSINESS_CASE.md to PDF

This repo stores the business case as Markdown (`docs/business-case/BUSINESS_CASE.md`) and provides a reproducible way to generate a PDF.

## Option 1 (recommended): Use the script

### Prerequisites
- `pandoc`
- A PDF engine: `xelatex` (TeX Live)

### Generate
```bash
./scripts/export_business_case_pdf.sh
```

The PDF will be written to:
- `docs/business-case/BUSINESS_CASE.pdf`

## Option 2: GitHub Actions
If you have Actions enabled, the workflow at `.github/workflows/build-business-case-pdf.yml` will generate the PDF and upload it as a workflow artifact on every push to `main`.