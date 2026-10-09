import json

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.ai.evals.retrieval import run_retrieval
from apps.ai.evals.tools import run_tools
from apps.ai.evals.world import build_world, load_dataset
from apps.ai.services.providers import provider_status, use_provider


class Command(BaseCommand):
    help = (
        "Measure semantic search (recall@k, MRR, score cutoffs) and, with --live, tool calling accuracy. "
        "Everything runs inside a transaction that is rolled back, so your real cards are never touched."
    )

    def add_arguments(self, parser):
        parser.add_argument("--live", action="store_true", help="Also run the tool calling cases against the real Anthropic API.")
        parser.add_argument("--provider", help="Model vendor for --live (default: AI_PROVIDER). Use it to compare vendors.")
        parser.add_argument("--model", help="Model name for --live (default: AI_MODEL).")
        parser.add_argument("--pause", type=float, default=0.0, help="Seconds to wait between tool cases (free tiers allow only a few requests per minute).")
        parser.add_argument("--min-recall", type=float, default=0.85, help="Fail if recall@5 is below this.")
        parser.add_argument("--min-mrr", type=float, default=0.7, help="Fail if MRR is below this.")
        parser.add_argument("--min-tool-accuracy", type=float, default=0.8, help="Fail (with --live) if tool accuracy is below this.")
        parser.add_argument("--json", dest="json_path", help="Write the full results to this file.")

    def handle(self, *args, **options):
        live = options["live"]
        if live:
            problem = provider_status(options["provider"], options["model"])["problem"]
            if problem:
                raise CommandError(f"--live needs a configured model provider: {problem}")

        report = {}
        with transaction.atomic():
            world = build_world(load_dataset("corpus"))
            report["retrieval"] = run_retrieval(world, load_dataset("retrieval"))
            if live:
                status = provider_status(options["provider"], options["model"])
                report["provider"] = {"name": status["provider"], "model": status["model"]}
                with use_provider(options["provider"], options["model"]):
                    report["tools"] = run_tools(world, load_dataset("tools"), pause=options["pause"])
            transaction.set_rollback(True)

        self._print(report, live)
        if options["json_path"]:
            with open(options["json_path"], "w") as handle:
                json.dump(report, handle, indent=2)

        failures = self._failures(report, options)
        if failures:
            raise CommandError("Eval thresholds missed: " + "; ".join(failures))
        self.stdout.write(self.style.SUCCESS("Evals passed."))

    def _failures(self, report, options):
        retrieval, failures = report["retrieval"], []
        if retrieval["recall_at_5"] < options["min_recall"]:
            failures.append(f"recall@5 {retrieval['recall_at_5']:.2f} < {options['min_recall']}")
        if retrieval["mrr"] < options["min_mrr"]:
            failures.append(f"MRR {retrieval['mrr']:.2f} < {options['min_mrr']}")
        tools = report.get("tools")
        if tools and tools["accuracy"] < options["min_tool_accuracy"]:
            failures.append(f"tool accuracy {tools['accuracy']:.2f} < {options['min_tool_accuracy']}")
        return failures

    def _print(self, report, live):
        r = report["retrieval"]
        out = self.stdout.write
        out(f"Retrieval ({r['queries']} queries)")
        out(f"  recall@1 {r['recall_at_1']:.2f}   recall@5 {r['recall_at_5']:.2f}   MRR {r['mrr']:.2f}")
        out(f"  median score of the right card {r['median_relevant_score']}, median best score for unrelated queries {r['median_best_unrelated_score']}")
        out("  cutoff   recall@5   unrelated queries still answered")
        for row in r["threshold_sweep"]:
            out(f"  {row['threshold']:<7}  {row['recall_at_5']:<9.2f}  {row['unrelated_answered']}")
        out(f"  suggested AI_SEARCH_MIN_SCORE: {r['suggested_min_score']}")
        for miss in r["misses"]:
            out(f"  MISS {miss['query']!r}: wanted {miss['expected']}, got {miss['got']}")
        if not live:
            out("Tool calling: skipped (add --live to run it against the Anthropic API).")
            return
        t = report["tools"]
        out(f"Provider: {report['provider']['name']} / {report['provider']['model']}")
        out(f"Tool calling ({t['cases']} cases): {t['passed']}/{t['cases']} passed, accuracy {t['accuracy']:.2f}, {t['total_tokens']} tokens")
        for result in t["results"]:
            mark = "ok  " if result["passed"] else "FAIL"
            out(f"  {mark} {result['id']:<26} {result['seconds']:>5}s  calls={result['tool_calls']}")
            for failure in result["failures"]:
                out(f"       - {failure}")
