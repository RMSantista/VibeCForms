"""XSLT rendering engine for VibeCForms."""

import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from saxonche import PySaxonProcessor
import xml.etree.ElementTree as ET

from .xml_builder import XMLBuilder
from .template_resolver import TemplateResolver
from .cache_manager import CacheManager


class XSLTRenderer:
    """Render VibeCForms pages using XSLT 3.0 transformations."""

    def __init__(self, business_case_root: str, src_root: str):
        """Initialize renderer.

        Args:
            business_case_root: Path to business case directory (e.g., examples/ponto-de-vendas)
            src_root: Path to src directory
        """
        self.business_case_root = business_case_root
        self.src_root = src_root

        # Template resolver handles override logic
        self.resolver = TemplateResolver(business_case_root, src_root)

        # Cache compiled stylesheets
        self.cache = CacheManager()

        # Initialize Saxon processor
        self.processor = PySaxonProcessor(license=False)
        self.xslt_processor = self.processor.new_xslt30_processor()

    def render_form_page(
        self,
        spec: Dict[str, Any],
        form_name: str,
        records: List[Dict[str, Any]],
        menu_items: List[Dict[str, Any]],
        error: str = "",
        new_record_id: str = "",
        form_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Render the main form page.

        Args:
            spec: Form specification
            form_name: Form path (e.g., "contatos", "financeiro/contas")
            records: List of existing records
            menu_items: Menu structure
            error: Error message to display
            new_record_id: Pre-generated UUID for new record
            form_data: Form data to pre-populate (validation errors)

        Returns:
            Rendered HTML string
        """
        # Build XML from data
        xml_elem = XMLBuilder.build_form_page_xml(
            spec=spec,
            form_name=form_name,
            records=records,
            menu_items=menu_items,
            error=error,
            new_record_id=new_record_id,
            form_data=form_data,
        )

        # Transform using XSLT
        return self._transform(xml_elem, "pages/form.xslt")

    def render_index_page(
        self, forms: List[Dict[str, Any]], menu_items: List[Dict[str, Any]]
    ) -> str:
        """Render the landing page with form cards.

        Args:
            forms: List of all forms with title, path, icon, category
            menu_items: Menu structure

        Returns:
            Rendered HTML string
        """
        xml_elem = XMLBuilder.build_index_page_xml(forms, menu_items)
        return self._transform(xml_elem, "pages/index.xslt")

    def render_edit_page(
        self,
        spec: Dict[str, Any],
        form_name: str,
        record: Dict[str, Any],
        menu_items: List[Dict[str, Any]],
        record_tags: List,
        error: str = "",
    ) -> str:
        """Render the edit page for a record.

        Args:
            spec: Form specification
            form_name: Form path
            record: Record data to edit
            menu_items: Menu structure
            record_tags: Tags applied to this record
            error: Error message to display

        Returns:
            Rendered HTML string
        """
        xml_elem = XMLBuilder.build_edit_page_xml(
            spec=spec,
            form_name=form_name,
            record=record,
            menu_items=menu_items,
            record_tags=record_tags,
            error=error,
        )
        return self._transform(xml_elem, "pages/edit.xslt")

    def render_kanban(
        self,
        board_name: str,
        board_config: Dict[str, Any],
        cards: Dict[str, List[Dict[str, Any]]],
        menu_items: List[Dict[str, Any]],
    ) -> str:
        """Render the kanban board page.

        Args:
            board_name: Board name (e.g., "sales_pipeline")
            board_config: Board configuration dict
            cards: Cards organized by column tag
            menu_items: Menu structure

        Returns:
            Rendered HTML string
        """
        xml_elem = XMLBuilder.build_kanban_xml(
            board_name=board_name,
            board_config=board_config,
            cards=cards,
            menu_items=menu_items,
        )
        return self._transform(xml_elem, "pages/kanban.xslt")

    def render_tags_manager(
        self,
        forms: List[Dict[str, Any]],
        menu_items: List[Dict[str, Any]],
    ) -> str:
        """Render the tags manager page.

        Args:
            forms: List of all forms with title, path, icon, category
            menu_items: Menu structure

        Returns:
            Rendered HTML string
        """
        xml_elem = XMLBuilder.build_tags_manager_xml(forms, menu_items)
        return self._transform(xml_elem, "pages/tags-manager.xslt")

    def render_migration_confirm(
        self,
        form_path: str,
        form_title: str,
        record_count: int,
        schema_change: Optional[Any],
        backend_change: Optional[Any],
        has_destructive_changes: bool,
        has_warnings: bool,
        menu_items: List[Dict[str, Any]],
    ) -> str:
        """Render the migration confirmation page.

        Args:
            form_path: Form path (e.g., "contatos")
            form_title: Form title for display
            record_count: Number of records that will be affected
            schema_change: SchemaChange object or None
            backend_change: BackendChange object or None
            has_destructive_changes: Whether there are destructive operations
            has_warnings: Whether there are warnings
            menu_items: Menu structure

        Returns:
            Rendered HTML string
        """
        xml_elem = XMLBuilder.build_migration_confirm_xml(
            form_path=form_path,
            form_title=form_title,
            record_count=record_count,
            schema_change=schema_change,
            backend_change=backend_change,
            has_destructive_changes=has_destructive_changes,
            has_warnings=has_warnings,
            menu_items=menu_items,
        )
        return self._transform(xml_elem, "pages/migration-confirm.xslt")

    def _transform(self, xml_elem: ET.Element, template_name: str) -> str:
        """Transform XML using XSLT template.

        Args:
            xml_elem: XML element to transform
            template_name: Template path relative to xslt/ directory

        Returns:
            Transformed HTML string
        """
        # Resolve template path (business case override or default)
        template_path = self.resolver.resolve(template_name)

        # Get or compile stylesheet
        stylesheet = self._get_stylesheet(template_path)

        # Transform
        xml_string = XMLBuilder.element_to_string(xml_elem)

        try:
            result = stylesheet.transform_to_string(
                xdm_node=self.processor.parse_xml(xml_text=xml_string)
            )
            return result
        except Exception as e:
            # Include helpful error information
            raise RuntimeError(
                f"XSLT transformation failed for template: {template_name}\n"
                f"Template path: {template_path}\n"
                f"Error: {str(e)}"
            ) from e

    def _get_stylesheet(self, template_path: str):
        """Get compiled stylesheet from cache or compile it.

        Args:
            template_path: Absolute path to XSLT file

        Returns:
            Compiled stylesheet object
        """
        # Check cache
        cached = self.cache.get(template_path)
        if cached:
            return cached

        # Compile and cache
        try:
            stylesheet = self.xslt_processor.compile_stylesheet(
                stylesheet_file=template_path
            )
            self.cache.set(template_path, stylesheet)
            return stylesheet
        except Exception as e:
            raise RuntimeError(
                f"Failed to compile XSLT stylesheet: {template_path}\n"
                f"Error: {str(e)}"
            ) from e

    def clear_cache(self):
        """Clear stylesheet cache (useful during development)."""
        self.cache.clear()

    def list_overrides(self) -> List[str]:
        """List all templates overridden by business case."""
        return self.resolver.list_overrides()
