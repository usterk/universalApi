"""Plugin routing service - wykonuje workflow przetwarzania dokumentów."""

from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.plugins.models import SourceWorkflowStep, UserWorkflowStep
from app.core.plugins.registry import PluginRegistry
from app.core.documents.models import Document
from app.core.plugins.base import BasePlugin
from app.core.logging import get_logger

logger = get_logger(__name__)


class WorkflowExecutionService:
    """Serwis wykonywania workflow przetwarzania."""

    def __init__(self, db: AsyncSession, registry: PluginRegistry):
        self.db = db
        self.registry = registry

    async def get_workflow_for_document(
        self,
        document: Document
    ) -> list[tuple[int, BasePlugin, dict]]:
        """
        Zwraca workflow dla dokumentu jako listę kroków.

        Priority:
        1. Source workflow (if source_id exists)
        2. User default workflow
        3. Empty list (no workflow)

        Returns:
            List[(sequence_number, plugin, settings)]
            Przykład: [(1, audio_transcription, {}), (2, sentiment_analysis, {})]
        """
        doc_type = document.document_type.name if document.document_type else None
        if not doc_type:
            return []

        # Priority 1: Source-based workflow
        if document.source_id:
            workflow = await self._get_workflow_for_source(document.source_id, doc_type)
            if workflow:
                logger.debug(f"Using source workflow for {doc_type}: {len(workflow)} steps")
                return workflow

        # Priority 2: User default workflow
        workflow = await self._get_workflow_for_user(document.owner_id, doc_type)
        if workflow:
            logger.debug(f"Using user default workflow for {doc_type}: {len(workflow)} steps")
            return workflow

        # No workflow configured
        logger.warning(
            f"No workflow configured for document type {doc_type} "
            f"(source_id={document.source_id}, owner_id={document.owner_id})"
        )
        return []

    async def _get_workflow_for_source(
        self,
        source_id: UUID,
        doc_type: str
    ) -> list[tuple[int, BasePlugin, dict]]:
        """
        Pobierz workflow dla (source_id, document_type).

        WAŻNE: Wspiera równoległe wykonanie pluginów:
        - Steps z tym samym sequence_number wykonują się równolegle
        - Steps z tym samym sequence_number muszą mieć ten sam input_type
        - Walidacja typu: każdy step musi obsługiwać odpowiedni input_type
        """
        result = await self.db.execute(
            select(SourceWorkflowStep)
            .where(
                SourceWorkflowStep.source_id == source_id,
                SourceWorkflowStep.document_type == doc_type,
                SourceWorkflowStep.is_enabled == True
            )
            .order_by(SourceWorkflowStep.sequence_number)
        )
        steps = result.scalars().all()

        if not steps:
            logger.debug(f"No workflow for source {source_id}, doc_type {doc_type}")
            return []

        # Group steps by sequence_number (parallel execution)
        from collections import defaultdict
        steps_by_seq: dict[int, list] = defaultdict(list)
        for step in steps:
            steps_by_seq[step.sequence_number].append(step)

        # Buduj workflow z walidacją
        workflow = []
        expected_input_type = doc_type  # Pierwszy krok musi przyjmować typ dokumentu

        for seq_num in sorted(steps_by_seq.keys()):
            parallel_steps = steps_by_seq[seq_num]
            parallel_outputs = []

            for step in parallel_steps:
                plugin = self.registry.get(step.plugin_name)
                if not plugin:
                    logger.warning(f"Plugin {step.plugin_name} not found, skipping step {step.sequence_number}")
                    continue

                # Walidacja: plugin musi obsługiwać oczekiwany typ
                if expected_input_type not in plugin.metadata.input_types:
                    logger.error(
                        f"Workflow validation error: Step {step.sequence_number} "
                        f"({plugin.name}) expects {plugin.metadata.input_types}, "
                        f"but previous step outputs {expected_input_type}"
                    )
                    continue  # Skip this plugin but continue with others

                workflow.append((step.sequence_number, plugin, step.settings or {}))
                parallel_outputs.append(plugin.metadata.output_type or doc_type)

            # For sequential steps: if only one output, use it
            # For parallel steps: keep original input type (parallel plugins don't chain)
            if len(parallel_outputs) == 1:
                expected_input_type = parallel_outputs[0]
            # If multiple parallel outputs, next step would need to handle multiple types
            # For now, we don't chain from parallel steps

        return workflow

    async def _get_workflow_for_user(
        self,
        user_id: UUID,
        doc_type: str
    ) -> list[tuple[int, BasePlugin, dict]]:
        """
        Pobierz user default workflow dla (user_id, document_type).

        WAŻNE: Wspiera równoległe wykonanie pluginów:
        - Steps z tym samym sequence_number wykonują się równolegle
        - Steps z tym samym sequence_number muszą mieć ten sam input_type
        - Walidacja typu: każdy step musi obsługiwać odpowiedni input_type
        """
        result = await self.db.execute(
            select(UserWorkflowStep)
            .where(
                UserWorkflowStep.user_id == user_id,
                UserWorkflowStep.document_type == doc_type,
                UserWorkflowStep.is_enabled == True
            )
            .order_by(UserWorkflowStep.sequence_number)
        )
        steps = result.scalars().all()

        if not steps:
            logger.debug(f"No user workflow for user {user_id}, doc_type {doc_type}")
            return []

        # Group steps by sequence_number (parallel execution)
        from collections import defaultdict
        steps_by_seq: dict[int, list] = defaultdict(list)
        for step in steps:
            steps_by_seq[step.sequence_number].append(step)

        # Buduj workflow z walidacją
        workflow = []
        expected_input_type = doc_type  # Pierwszy krok musi przyjmować typ dokumentu

        for seq_num in sorted(steps_by_seq.keys()):
            parallel_steps = steps_by_seq[seq_num]
            parallel_outputs = []

            for step in parallel_steps:
                plugin = self.registry.get(step.plugin_name)
                if not plugin:
                    logger.warning(f"Plugin {step.plugin_name} not found, skipping step {step.sequence_number}")
                    continue

                # Walidacja: plugin musi obsługiwać oczekiwany typ
                if expected_input_type not in plugin.metadata.input_types:
                    logger.error(
                        f"User workflow validation error: Step {step.sequence_number} "
                        f"({plugin.name}) expects {plugin.metadata.input_types}, "
                        f"but previous step outputs {expected_input_type}"
                    )
                    continue  # Skip this plugin but continue with others

                workflow.append((step.sequence_number, plugin, step.settings or {}))
                parallel_outputs.append(plugin.metadata.output_type or doc_type)

            # For sequential steps: if only one output, use it
            # For parallel steps: keep original input type (parallel plugins don't chain)
            if len(parallel_outputs) == 1:
                expected_input_type = parallel_outputs[0]
            # If multiple parallel outputs, next step would need to handle multiple types
            # For now, we don't chain from parallel steps

        return workflow
