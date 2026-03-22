Add this to run_pipeline.py
Step 1 — Add the import at the top with the other imports:
pythonfrom generation.generate_contract_pdf import generate_pdf
Step 2 — Add the flags to the CLI argument parser at the bottom:
pythonparser.add_argument("--generate", action="store_true",
                    help="Generate PDF contract after extraction")
parser.add_argument("--output-pdf", 
                    help="Path for generated PDF (requires --generate)")
Step 3 — Add the generation call right after the existing output save block:
python    if args.output:
        from pathlib import Path
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w") as f:
            json.dump(result, f, indent=2)
        log.info(f"[Pipeline] Output saved to {args.output}")
    else:
        print(json.dumps(result, indent=2))

    # ── ADD THIS BLOCK ────────────────────────────────────────────────────
    if args.generate:
        pdf_path = args.output_pdf or args.output.replace(".json", ".pdf")
        contract_type = args.type if args.type != "auto" else "nda"
        generate_pdf(result, contract_type, pdf_path)
        log.info(f"[Pipeline] PDF generated: {pdf_path}")
