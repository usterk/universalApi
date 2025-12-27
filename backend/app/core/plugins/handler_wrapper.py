"""Wrapper dla handlerów pluginów - dodaje routing logic."""

from typing import Callable
from app.core.events.types import Event
from app.core.database.session import async_session_factory
from app.core.plugins.registry import PluginRegistry
from app.core.plugins.routing import WorkflowExecutionService
from app.core.documents.models import Document
from app.core.logging import get_logger
from sqlalchemy import select
from sqlalchemy.orm import selectinload

logger = get_logger(__name__)


def create_routing_aware_handler(plugin_name: str, handler_func: Callable):
    """
    Wrapper który sprawdza routing przed wywołaniem handlera.

    Użycie w pluginie:
        def get_event_handlers(self):
            return {
                "document.created": [
                    create_routing_aware_handler(self.name, _my_handler)
                ]
            }
    """
    async def wrapped_handler(event: Event) -> None:
        """
        Wrapper który sprawdza routing przed wywołaniem handlera.
        Assumes EVERY document has source_id (no None handling).
        """
        # Tylko dla document.created
        if event.type != "document.created":
            return await handler_func(event)

        source_id = event.payload.get("source_id")
        document_id = event.payload.get("document_id")

        # Validate required fields
        if not source_id:
            logger.error(f"[{plugin_name}] No source_id in payload! Every document must have source_id.")
            return

        if not document_id:
            logger.warning(f"[{plugin_name}] No document_id in payload")
            return

        logger.debug(f"[{plugin_name}] Workflow routing check for document {document_id}, source_id={source_id}")

        # Sprawdź routing
        async with async_session_factory() as db:
            # Pobierz dokument
            result = await db.execute(
                select(Document)
                .options(selectinload(Document.document_type))
                .where(Document.id == document_id)
            )
            document = result.scalar_one_or_none()
            if not document:
                logger.warning(f"[{plugin_name}] Document {document_id} not found in database")
                return

            doc_type_name = document.document_type.name if document.document_type else None
            logger.debug(f"[{plugin_name}] Document type: {doc_type_name}, source: {source_id}")

            # Sprawdź czy ten plugin powinien przetworzyć
            registry = PluginRegistry()
            routing = WorkflowExecutionService(db, registry)

            plugin = registry.get(plugin_name)
            if not plugin:
                logger.warning(f"[{plugin_name}] Plugin not found in registry")
                return

            workflow = await routing.get_workflow_for_document(document)

            if not workflow:
                logger.info(f"[{plugin_name}] No workflow configured for ({source_id}, {doc_type_name}), skipping")
                return

            logger.debug(f"[{plugin_name}] Workflow has {len(workflow)} steps")

            # Jeśli plugin nie jest na liście → skip
            plugins_in_workflow = [p for _, p, _ in workflow]
            if plugin not in plugins_in_workflow:
                logger.debug(f"[{plugin_name}] Plugin not in workflow, skipping")
                return

            logger.info(f"[{plugin_name}] Workflow routing passed, calling handler")

        # Routing passed → wywołaj handler
        await handler_func(event)

    return wrapped_handler
