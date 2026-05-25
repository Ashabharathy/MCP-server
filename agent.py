"""
agent.py — Phase 5 orchestrator for GROWW Weekly Review Pulse Agent.

Connects all pipeline stages into a single, reliable orchestrated agent.
"""

import argparse
import json
import logging
import os
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# ── logging setup ──────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("agent")

# ── paths ──────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent
LOGS_DIR = ROOT / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)


class PipelineStage:
    """Represents a stage in the pipeline with timing and error tracking."""

    def __init__(self, name: str):
        self.name = name
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.success: bool = False
        self.error: Optional[str] = None
        self.output: Optional[Dict[str, Any]] = None

    def start(self) -> None:
        """Start timing the stage."""
        self.start_time = time.time()
        logger.info("=" * 60)
        logger.info(f"Starting stage: {self.name}")
        logger.info("=" * 60)

    def complete(self, output: Dict[str, Any]) -> None:
        """Mark stage as successful with output."""
        self.end_time = time.time()
        self.success = True
        self.output = output
        duration = self.end_time - self.start_time
        logger.info(f"Stage completed: {self.name} ({duration:.2f}s)")

    def fail(self, error: str) -> None:
        """Mark stage as failed with error message."""
        self.end_time = time.time()
        self.success = False
        self.error = error
        duration = self.end_time - self.start_time
        logger.error(f"Stage failed: {self.name} ({duration:.2f}s) - {error}")

    @property
    def duration(self) -> float:
        """Get stage duration in seconds."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0


class AgentOrchestrator:
    """Main orchestrator for the GROWW Weekly Review Pulse Agent."""

    def __init__(
        self,
        weeks: int = 8,
        dry_run: bool = False,
        doc_id: Optional[str] = None,
        recipient: Optional[str] = None,
        model: Optional[str] = None,
        token_budget: int = 50000,
    ):
        """
        Initialize the orchestrator.

        Args:
            weeks: Number of weeks to look back for reviews.
            dry_run: If True, skip delivery stages.
            doc_id: Google Doc ID to update (if omitted, creates new doc).
            recipient: Email address for Gmail draft.
            model: LLM model override.
            token_budget: Maximum LLM tokens to use per run.
        """
        self.weeks = weeks
        self.dry_run = dry_run
        self.doc_id = doc_id
        self.recipient = recipient
        self.model = model
        self.token_budget = token_budget

        self.run_id = str(uuid.uuid4())
        self.run_mode = "dry-run" if dry_run else "full"
        self.stages: Dict[str, PipelineStage] = {}
        self.errors: list[str] = []
        self.tokens_used: int = 0

    def run(self) -> Dict[str, Any]:
        """
        Run the full pipeline.

        Returns:
            Run log with all stage results and metadata.
        """
        logger.info("=" * 60)
        logger.info("GROWW Weekly Review Pulse Agent")
        logger.info("=" * 60)
        logger.info(f"Run ID: {self.run_id}")
        logger.info(f"Run mode: {self.run_mode}")
        logger.info(f"Weeks: {self.weeks}")
        logger.info(f"Dry run: {self.dry_run}")
        logger.info(f"Doc ID: {self.doc_id or 'create new'}")
        logger.info(f"Recipient: {self.recipient or 'not set'}")
        logger.info(f"Model: {self.model or 'default'}")
        logger.info(f"Token budget: {self.token_budget}")
        logger.info("=" * 60)

        start_time = time.time()

        try:
            # Stage 1: Ingestion
            self._run_ingestion()

            # Stage 2: Analysis
            self._run_analysis()

            # Stage 3: Generation
            self._run_generation()

            # Stage 4: Delivery (skip if dry run)
            if not self.dry_run:
                self._run_delivery()
            else:
                logger.info("Dry run: skipping delivery stages")

        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            self.errors.append(str(e))

            # Send alert on unrecoverable failure
            self._send_failure_alert(str(e))

        total_duration = time.time() - start_time

        # Build run log
        run_log = self._build_run_log(total_duration)

        # Write run log
        self._write_run_log(run_log)

        return run_log

    def _run_ingestion(self) -> None:
        """Run Phase 1: Review Ingestion."""
        stage = PipelineStage("ingestion")
        self.stages["ingestion"] = stage
        stage.start()

        try:
            from ingestion.loader import load_playstore_reviews

            # Load reviews
            reviews = load_playstore_reviews(
                playstore_path=str(ROOT / "ingestion" / "sample_data" / "playstore_sample.csv"),
                weeks=self.weeks,
            )

            if not reviews:
                raise ValueError("No reviews loaded - ingestion failed")

            stage.complete({
                "review_count": len(reviews),
                "date_range": {
                    "from": min(r.date for r in reviews).isoformat() if reviews else None,
                    "to": max(r.date for r in reviews).isoformat() if reviews else None,
                },
            })

        except Exception as e:
            stage.fail(str(e))
            self.errors.append(f"Ingestion failed: {str(e)}")
            raise  # Halt pipeline on ingestion failure

    def _run_analysis(self) -> None:
        """Run Phase 2: Theme Analysis."""
        stage = PipelineStage("analysis")
        self.stages["analysis"] = stage
        stage.start()

        try:
            from analyzer.analyzer import analyze_themes
            from ingestion.loader import load_playstore_reviews

            groq_api_key = os.getenv("GROQ_API_KEY")
            if not groq_api_key:
                raise ValueError("GROQ_API_KEY not set")

            # Load reviews
            reviews = load_playstore_reviews(
                playstore_path=str(ROOT / "ingestion" / "sample_data" / "playstore_sample.csv"),
                weeks=self.weeks,
            )

            # Analyze themes
            analysis_result = analyze_themes(
                reviews=reviews,
                groq_api_key=groq_api_key,
                sample_count=500,
                batch_size=50,
                max_themes=5,
            )

            tokens_used = analysis_result.get("metadata", {}).get("estimated_tokens_used", 0)
            self.tokens_used += tokens_used

            # Check token budget
            if self.tokens_used > self.token_budget:
                error_msg = f"Token budget exceeded: {self.tokens_used} > {self.token_budget}"
                logger.error(error_msg)
                self.errors.append(error_msg)
                raise RuntimeError(error_msg)

            stage.complete({
                "theme_count": len(analysis_result["themes"]),
                "llm_tokens_used": tokens_used,
            })

        except Exception as e:
            stage.fail(str(e))
            self.errors.append(f"Analysis failed: {str(e)}")
            # Continue pipeline on analysis failure (partial run)

    def _run_generation(self) -> None:
        """Run Phase 3: Pulse Generation."""
        stage = PipelineStage("generation")
        self.stages["generation"] = stage
        stage.start()

        try:
            from generator.generator import generate_pulse
            from analyzer.analyzer import analyze_themes
            from ingestion.loader import load_playstore_reviews

            groq_api_key = os.getenv("GROQ_API_KEY")
            if not groq_api_key:
                raise ValueError("GROQ_API_KEY not set")

            # Load reviews
            reviews = load_playstore_reviews(
                playstore_path=str(ROOT / "ingestion" / "sample_data" / "playstore_sample.csv"),
                weeks=self.weeks,
            )

            # Analyze themes
            analysis_result = analyze_themes(
                reviews=reviews,
                groq_api_key=groq_api_key,
                sample_count=500,
                batch_size=50,
                max_themes=5,
            )

            # Generate pulse
            pulse_result = generate_pulse(
                themes=analysis_result["themes"],
                groq_api_key=groq_api_key,
                max_words=250,
                max_retries=2,
            )

            tokens_used = pulse_result.get("metadata", {}).get("llm_tokens_used", 0)
            self.tokens_used += tokens_used

            # Check token budget
            if self.tokens_used > self.token_budget:
                error_msg = f"Token budget exceeded: {self.tokens_used} > {self.token_budget}"
                logger.error(error_msg)
                self.errors.append(error_msg)
                raise RuntimeError(error_msg)

            stage.complete({
                "pulse_word_count": pulse_result["metadata"]["word_count"],
                "llm_tokens_used": tokens_used,
            })

        except Exception as e:
            stage.fail(str(e))
            self.errors.append(f"Generation failed: {str(e)}")
            # Continue pipeline on generation failure (partial run)

    def _run_delivery(self) -> None:
        """Run Phase 4: Delivery (Google Docs and Gmail)."""
        stage = PipelineStage("delivery")
        self.stages["delivery"] = stage
        stage.start()

        try:
            from delivery.docs import update_google_doc
            from delivery.gmail import draft_email
            from generator.generator import generate_pulse
            from analyzer.analyzer import analyze_themes
            from ingestion.loader import load_playstore_reviews

            groq_api_key = os.getenv("GROQ_API_KEY")
            google_doc_id = self.doc_id or os.getenv("GOOGLE_DOC_ID")
            gmail_recipient = self.recipient or os.getenv("GMAIL_RECIPIENT")

            if not groq_api_key:
                raise ValueError("GROQ_API_KEY not set")
            if not google_doc_id:
                raise ValueError("GOOGLE_DOC_ID not set")
            if not gmail_recipient:
                raise ValueError("GMAIL_RECIPIENT not set")

            # Load reviews
            reviews = load_playstore_reviews(
                playstore_path=str(ROOT / "ingestion" / "sample_data" / "playstore_sample.csv"),
                weeks=self.weeks,
            )

            # Analyze themes
            analysis_result = analyze_themes(
                reviews=reviews,
                groq_api_key=groq_api_key,
                sample_count=500,
                batch_size=50,
                max_themes=5,
            )

            # Generate pulse
            pulse_result = generate_pulse(
                themes=analysis_result["themes"],
                groq_api_key=groq_api_key,
                max_words=250,
                max_retries=2,
            )

            # Deliver to Google Docs
            docs_result = update_google_doc(
                doc_id=google_doc_id,
                content=pulse_result["formats"]["markdown"],
            )

            # Draft Gmail
            gmail_result = draft_email(
                to=gmail_recipient,
                subject=f"Weekly Review Pulse - {datetime.now().strftime('%Y-%m-%d')}",
                body=pulse_result["formats"]["plain_text"],
            )

            stage.complete({
                "docs_delivery_status": "success" if docs_result["success"] else "partial",
                "gmail_delivery_status": "success" if gmail_result["success"] else "partial",
                "doc_url": docs_result.get("doc_url"),
                "draft_id": gmail_result.get("draft_id"),
            })

        except Exception as e:
            stage.fail(str(e))
            self.errors.append(f"Delivery failed: {str(e)}")
            # Continue pipeline on delivery failure (partial run)

    def _build_run_log(self, total_duration: float) -> Dict[str, Any]:
        """Build structured run log."""
        ingestion_stage = self.stages.get("ingestion")
        analysis_stage = self.stages.get("analysis")
        generation_stage = self.stages.get("generation")
        delivery_stage = self.stages.get("delivery")

        return {
            "run_id": self.run_id,
            "run_mode": self.run_mode,
            "run_at": datetime.now().isoformat(),
            "config": {
                "weeks": self.weeks,
                "dry_run": self.dry_run,
                "doc_id": self.doc_id,
                "recipient": self.recipient,
                "model": self.model,
                "token_budget": self.token_budget,
            },
            "stages": {
                "ingestion": {
                    "success": ingestion_stage.success if ingestion_stage else False,
                    "duration": ingestion_stage.duration if ingestion_stage else 0,
                    "error": ingestion_stage.error if ingestion_stage else None,
                    "output": ingestion_stage.output if ingestion_stage else None,
                },
                "analysis": {
                    "success": analysis_stage.success if analysis_stage else False,
                    "duration": analysis_stage.duration if analysis_stage else 0,
                    "error": analysis_stage.error if analysis_stage else None,
                    "output": analysis_stage.output if analysis_stage else None,
                },
                "generation": {
                    "success": generation_stage.success if generation_stage else False,
                    "duration": generation_stage.duration if generation_stage else 0,
                    "error": generation_stage.error if generation_stage else None,
                    "output": generation_stage.output if generation_stage else None,
                },
                "delivery": {
                    "success": delivery_stage.success if delivery_stage else False,
                    "duration": delivery_stage.duration if delivery_stage else 0,
                    "error": delivery_stage.error if delivery_stage else None,
                    "output": delivery_stage.output if delivery_stage else None,
                },
            },
            "summary": {
                "date_range": ingestion_stage.output.get("date_range") if ingestion_stage and ingestion_stage.output else None,
                "review_count": ingestion_stage.output.get("review_count") if ingestion_stage and ingestion_stage.output else 0,
                "theme_count": analysis_stage.output.get("theme_count") if analysis_stage and analysis_stage.output else 0,
                "pulse_word_count": generation_stage.output.get("pulse_word_count") if generation_stage and generation_stage.output else 0,
                "docs_delivery_status": delivery_stage.output.get("docs_delivery_status") if delivery_stage and delivery_stage.output else "skipped",
                "gmail_delivery_status": delivery_stage.output.get("gmail_delivery_status") if delivery_stage and delivery_stage.output else "skipped",
                "doc_url": delivery_stage.output.get("doc_url") if delivery_stage and delivery_stage.output else None,
                "duration_seconds": total_duration,
                "tokens_used": self.tokens_used,
                "token_budget": self.token_budget,
                "errors": self.errors,
            },
            "status": "success" if not self.errors else "partial",
        }

    def _write_run_log(self, run_log: Dict[str, Any]) -> None:
        """Write run log to file."""
        log_file = LOGS_DIR / f"run_{self.run_id}.json"
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(run_log, f, indent=2, ensure_ascii=False)
        logger.info(f"Run log written to: {log_file}")

    def _send_failure_alert(self, error: str) -> None:
        """Send alert on unrecoverable failure."""
        try:
            from delivery.alerting import send_alert

            # Determine which stage failed
            failed_stage = "unknown"
            for stage_name, stage in self.stages.items():
                if not stage.success:
                    failed_stage = stage_name
                    break

            # Get alert configuration
            alert_channel = os.getenv("ALERT_CHANNEL", "email")
            webhook_url = os.getenv("SLACK_WEBHOOK_URL")
            recipient = os.getenv("ALERT_RECIPIENT") or self.recipient

            # Send alert
            send_alert(
                run_id=self.run_id,
                stage=failed_stage,
                error_summary=error,
                alert_channel=alert_channel,
                webhook_url=webhook_url,
                recipient=recipient,
            )
        except Exception as e:
            logger.error(f"Failed to send failure alert: {e}")


def main() -> None:
    """Main entry point for the agent."""
    parser = argparse.ArgumentParser(
        description="GROWW Weekly Review Pulse Agent - Orchestrator"
    )
    parser.add_argument(
        "--weeks",
        type=int,
        default=8,
        help="Number of weeks to look back for reviews (default: 8)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Skip delivery stages, output pulse to stdout/file only",
    )
    parser.add_argument(
        "--doc-id",
        type=str,
        help="Google Doc ID to update (if omitted, uses GOOGLE_DOC_ID env var)",
    )
    parser.add_argument(
        "--recipient",
        type=str,
        help="Email address for Gmail draft (if omitted, uses GMAIL_RECIPIENT env var)",
    )
    parser.add_argument(
        "--model",
        type=str,
        help="LLM model override",
    )
    parser.add_argument(
        "--token-budget",
        type=int,
        default=50000,
        help="Maximum LLM tokens to use per run (default: 50000)",
    )

    args = parser.parse_args()

    orchestrator = AgentOrchestrator(
        weeks=args.weeks,
        dry_run=args.dry_run,
        doc_id=args.doc_id,
        recipient=args.recipient,
        model=args.model,
        token_budget=args.token_budget,
    )

    run_log = orchestrator.run()

    # Print summary
    print()
    print("=" * 60)
    print("  PIPELINE RUN SUMMARY")
    print("=" * 60)
    print(f"  Run ID: {run_log['run_id']}")
    print(f"  Run mode: {run_log['run_mode']}")
    print(f"  Status: {run_log['status']}")
    print(f"  Duration: {run_log['summary']['duration_seconds']:.2f}s")
    print()
    print(f"  Reviews: {run_log['summary']['review_count']}")
    print(f"  Themes: {run_log['summary']['theme_count']}")
    print(f"  Pulse words: {run_log['summary']['pulse_word_count']}")
    print(f"  Tokens used: {run_log['summary']['tokens_used']}")
    print(f"  Token budget: {run_log['summary']['token_budget']}")
    print()
    print(f"  Docs delivery: {run_log['summary']['docs_delivery_status']}")
    print(f"  Gmail delivery: {run_log['summary']['gmail_delivery_status']}")
    if run_log['summary']['doc_url']:
        print(f"  Doc URL: {run_log['summary']['doc_url']}")
    print()
    if run_log['summary']['errors']:
        print("  Errors:")
        for error in run_log['summary']['errors']:
            print(f"    - {error}")
    print("=" * 60)

    # Exit with error code if pipeline failed
    if run_log['status'] == "partial":
        sys.exit(1)


if __name__ == "__main__":
    main()
