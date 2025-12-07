"""Resolve XSLT templates with business case override support."""

import os
from pathlib import Path
from typing import List


class TemplateResolver:
    """Resolve template paths with fallback from business case to src."""

    def __init__(self, business_case_root: str, src_root: str):
        """Initialize resolver.

        Args:
            business_case_root: Path to business case (e.g., examples/ponto-de-vendas)
            src_root: Path to src directory
        """
        self.business_case_xslt = os.path.join(business_case_root, "xslt")
        self.src_xslt = os.path.join(src_root, "xslt")

    def resolve(self, template_name: str) -> str:
        """Resolve template path with fallback.

        Priority:
        1. Business case XSLT directory (examples/<case>/xslt/)
        2. Default XSLT directory (src/xslt/)

        Args:
            template_name: Template path relative to xslt/ (e.g., "pages/form.xslt", "fields/select.xslt")

        Returns:
            Absolute path to template file

        Raises:
            FileNotFoundError: If template not found in any location
        """
        # Check business case first
        business_path = os.path.join(self.business_case_xslt, template_name)
        if os.path.exists(business_path):
            return business_path

        # Fallback to src
        src_path = os.path.join(self.src_xslt, template_name)
        if os.path.exists(src_path):
            return src_path

        raise FileNotFoundError(
            f"Template not found: {template_name}\n"
            f"Searched in:\n"
            f"  - {business_path}\n"
            f"  - {src_path}"
        )

    def list_overrides(self) -> List[str]:
        """List all templates overridden by the business case.

        Returns:
            List of template names (relative paths) that exist in business case
        """
        overrides = []

        if not os.path.exists(self.business_case_xslt):
            return overrides

        # Walk business case XSLT directory
        for root, dirs, files in os.walk(self.business_case_xslt):
            for file in files:
                if file.endswith(".xslt"):
                    full_path = os.path.join(root, file)
                    relative_path = os.path.relpath(full_path, self.business_case_xslt)
                    # Normalize path separators to forward slashes
                    relative_path = relative_path.replace(os.sep, "/")
                    overrides.append(relative_path)

        return sorted(overrides)
