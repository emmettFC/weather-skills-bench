import argparse
import json
from .catalog import ROOT


def main():
    parser=argparse.ArgumentParser(description="Weather skills benchmark")
    sub=parser.add_subparsers(dest="command",required=True)
    for name in ("reference","build-images","build-e2e-images","validate-end-to-end","validate-containers","validate-python","validate-skills-only","export","list","freeze"):
        sub.add_parser(name)
    study=sub.add_parser("study"); study.add_argument("--config",default=str(ROOT/"configs/pilot.json"))
    study.add_argument("--resume",help="Previous study JSON; preserve completed runs and resume missing conditions")
    args=parser.parse_args()
    if args.command=="reference":
        from .reference import run_reference
        result=run_reference()
        if not all(r["correctness"]["passed"] and r["workflow"]["passed"] for r in result["runs"] if not r['case_id'].startswith('e2e-')):
            raise SystemExit(1)
    elif args.command=="freeze":
        from .fixtures import freeze
        freeze()
    elif args.command=="build-images":
        from .sandbox import build_images
        build_images()
    elif args.command=="build-e2e-images":
        from .e2e_sandbox import build_images
        build_images()
    elif args.command=="validate-end-to-end":
        from .e2e_validation import run
        run()
    elif args.command=="validate-containers":
        from .validation import validate_containers
        validate_containers()
    elif args.command=="validate-skills-only":
        from .validation import validate_skills_only
        validate_skills_only()
    elif args.command=="validate-python":
        from .validation import validate_python
        validate_python()
    elif args.command=="export":
        from .report import export_dashboard
        print(export_dashboard())
    elif args.command=="study":
        from .runner import run_study
        from .report import export_dashboard
        print(run_study(args.config,resume=args.resume)); print(export_dashboard())
    else:
        from .cases import cases
        print(json.dumps([c.public() for c in cases()],indent=2))


if __name__=="__main__": main()
