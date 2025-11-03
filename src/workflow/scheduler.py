"""
WorkflowScheduler - Background jobs para workflow automation

Background jobs:
1. Auto-transitions (a cada 5 minutos)
2. Anomaly detection (a cada 1 hora)
3. ML model retraining (diário às 2 AM)
4. Notification queue processing (a cada 30 segundos) - quando implementado

Usage:
    from workflow.scheduler import start_scheduler, stop_scheduler

    # Start scheduler
    start_scheduler(
        auto_transition_engine,
        workflow_repo,
        anomaly_detector,
        workflow_ml_model,
        kanban_registry
    )

    # Stop scheduler (on app shutdown)
    stop_scheduler()
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global scheduler instance
_scheduler = None


def start_scheduler(
    auto_transition_engine,
    workflow_repo,
    anomaly_detector,
    workflow_ml_model,
    kanban_registry,
    notification_manager=None,  # Optional - when implemented
):
    """
    Start background scheduler with all workflow jobs

    Args:
        auto_transition_engine: AutoTransitionEngine instance
        workflow_repo: WorkflowRepository instance
        anomaly_detector: AnomalyDetector instance
        workflow_ml_model: WorkflowMLModel instance
        kanban_registry: KanbanRegistry instance
        notification_manager: NotificationManager instance (optional)
    """
    global _scheduler

    if _scheduler is not None:
        logger.warning("⚠️  Scheduler already running, skipping start")
        return

    logger.info("🚀 Starting Workflow Background Scheduler...")

    _scheduler = BackgroundScheduler()

    # ========== Job 1: Auto-Transitions (every 5 minutes) ==========
    def run_auto_transitions():
        """Check and execute automatic transitions"""
        try:
            logger.info("⏰ Running auto-transitions check...")
            stats = auto_transition_engine.process_all_auto_transitions(workflow_repo)

            if stats.get("transitions_executed", 0) > 0:
                logger.info(
                    f"✅ Auto-transitions: {stats['transitions_executed']} executed, "
                    f"{stats.get('transitions_failed', 0)} failed"
                )
            else:
                logger.debug("No auto-transitions executed")

        except Exception as e:
            logger.error(f"❌ Error in auto-transitions job: {e}")

    _scheduler.add_job(
        run_auto_transitions,
        trigger=IntervalTrigger(minutes=5),
        id="auto_transitions",
        name="Auto-Transitions Check",
        replace_existing=True,
    )

    # ========== Job 2: Anomaly Detection (every 1 hour) ==========
    def run_anomaly_detection():
        """Detect anomalies in all kanbans"""
        try:
            logger.info("🔍 Running anomaly detection...")

            all_kanbans = kanban_registry.list_kanbans()
            total_anomalies = 0

            for kanban in all_kanbans:
                kanban_id = kanban.get("id")
                report = anomaly_detector.generate_anomaly_report(kanban_id)

                summary = report.get("summary", {})
                kanban_anomalies = (
                    summary.get("stuck_count", 0)
                    + summary.get("duration_anomaly_count", 0)
                    + summary.get("loop_count", 0)
                    + summary.get("unusual_path_count", 0)
                )

                if kanban_anomalies > 0:
                    total_anomalies += kanban_anomalies
                    logger.warning(
                        f"⚠️  Kanban '{kanban_id}': {kanban_anomalies} anomalies detected"
                    )

                    # TODO: Send notification when notification_manager is implemented
                    # if notification_manager and kanban_anomalies > 10:
                    #     notification_manager.send_anomaly_alert(kanban_id, 'stuck', report)

            if total_anomalies > 0:
                logger.info(
                    f"✅ Anomaly detection: {total_anomalies} total anomalies found"
                )
            else:
                logger.debug("No anomalies detected")

        except Exception as e:
            logger.error(f"❌ Error in anomaly detection job: {e}")

    _scheduler.add_job(
        run_anomaly_detection,
        trigger=IntervalTrigger(hours=1),
        id="anomaly_detection",
        name="Anomaly Detection",
        replace_existing=True,
    )

    # ========== Job 3: ML Model Retraining (daily at 2 AM) ==========
    def run_ml_retraining():
        """Retrain ML models for all kanbans"""
        try:
            logger.info("🤖 Running ML model retraining...")

            all_kanbans = kanban_registry.list_kanbans()
            retrained_count = 0

            for kanban in all_kanbans:
                kanban_id = kanban.get("id")

                # Check if retraining is needed (100+ new completed processes)
                try:
                    workflow_ml_model.auto_retrain_if_needed(kanban_id)
                    retrained_count += 1
                except Exception as e:
                    logger.warning(f"⚠️  Failed to retrain model for '{kanban_id}': {e}")

            logger.info(
                f"✅ ML retraining: {retrained_count}/{len(all_kanbans)} models processed"
            )

        except Exception as e:
            logger.error(f"❌ Error in ML retraining job: {e}")

    _scheduler.add_job(
        run_ml_retraining,
        trigger=CronTrigger(hour=2, minute=0),  # 2:00 AM daily
        id="ml_retraining",
        name="ML Model Retraining",
        replace_existing=True,
    )

    # ========== Job 4: Notification Queue (every 30 seconds) - OPTIONAL ==========
    if notification_manager:

        def process_notifications():
            """Process pending notifications"""
            try:
                notification_manager.process_notification_queue()
            except Exception as e:
                logger.error(f"❌ Error processing notifications: {e}")

        _scheduler.add_job(
            process_notifications,
            trigger=IntervalTrigger(seconds=30),
            id="notifications",
            name="Notification Queue Processing",
            replace_existing=True,
        )

        logger.info("📧 Notification queue processing enabled")
    else:
        logger.info("📧 Notification queue processing disabled (not implemented yet)")

    # Start the scheduler
    _scheduler.start()

    logger.info(
        "✅ Workflow Background Scheduler started with {} jobs".format(
            len(_scheduler.get_jobs())
        )
    )
    logger.info("   - Auto-transitions: every 5 minutes")
    logger.info("   - Anomaly detection: every 1 hour")
    logger.info("   - ML retraining: daily at 2:00 AM")
    if notification_manager:
        logger.info("   - Notifications: every 30 seconds")


def stop_scheduler():
    """Stop the background scheduler"""
    global _scheduler

    if _scheduler is None:
        logger.warning("⚠️  Scheduler not running, nothing to stop")
        return

    logger.info("🛑 Stopping Workflow Background Scheduler...")
    _scheduler.shutdown(wait=True)
    _scheduler = None
    logger.info("✅ Scheduler stopped")


def is_running():
    """Check if scheduler is currently running"""
    return _scheduler is not None and _scheduler.running


def get_jobs():
    """Get list of currently scheduled jobs"""
    if _scheduler is None:
        return []

    return [
        {
            "id": job.id,
            "name": job.name,
            "next_run_time": (
                job.next_run_time.isoformat() if job.next_run_time else None
            ),
        }
        for job in _scheduler.get_jobs()
    ]
