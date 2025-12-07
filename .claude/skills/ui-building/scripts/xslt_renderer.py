"""
XSLT 3.0 Renderer for VibeCForms

Provides integration between saxonche and VibeCForms for declarative template rendering.
"""

import json
import os
import tempfile
from typing import Dict, Any, Optional
from pathlib import Path
from saxonche import PySaxonProcessor


class XSLTRenderer:
    """Renderer for XSLT 3.0 templates using saxonche."""

    def __init__(self, license: bool = False):
        """
        Initialize the XSLT renderer.

        Args:
            license: Whether to use a Saxon license (default: False for open-source HE version)
        """
        self.processor = PySaxonProcessor(license=license)
        self.xslt_processor = self.processor.new_xslt30_processor()
        self.compiled_templates: Dict[str, Any] = {}

    def load_template(self, template_path: str) -> None:
        """
        Load and compile an XSLT template.

        Args:
            template_path: Path to the XSLT template file
        """
        template_file = Path(template_path)

        if not template_file.exists():
            raise FileNotFoundError(f"XSLT template not found: {template_path}")

        with open(template_file, "r", encoding="utf-8") as f:
            xslt_content = f.read()

        # Compile and cache the template
        self.xslt_processor.compile_stylesheet(stylesheet_text=xslt_content)
        self.compiled_templates[template_path] = xslt_content

    def render(
        self,
        data: Dict[str, Any],
        template_path: Optional[str] = None,
        pretty_print: bool = False,
        indent: int = 2,
        debug: bool = False,
    ) -> str:
        """
        Render data using XSLT transformation.

        Args:
            data: Dictionary containing the data to transform (will be converted to JSON)
            template_path: Path to XSLT template (if different from loaded template)
            pretty_print: Whether to format the output HTML
            indent: Number of spaces for indentation (when pretty_print=True)
            debug: Enable debug output

        Returns:
            Rendered HTML string
        """
        # Load template if specified and not already loaded
        if template_path and template_path not in self.compiled_templates:
            self.load_template(template_path)

        # Convert data to JSON
        json_data = json.dumps(
            data, ensure_ascii=False, indent=indent if pretty_print else None
        )

        # Set XSLT parameters
        params = {}
        if pretty_print:
            params["indent"] = "yes"
        else:
            params["indent"] = "no"

        # Perform transformation
        try:
            # Get the stylesheet (last compiled if template_path not specified)
            if template_path:
                stylesheet_text = self.compiled_templates[template_path]
            else:
                # Use the most recently loaded template
                if not self.compiled_templates:
                    raise ValueError("No template loaded. Call load_template() first.")
                stylesheet_text = list(self.compiled_templates.values())[-1]

            # Compile stylesheet
            executable = self.xslt_processor.compile_stylesheet(
                stylesheet_text=stylesheet_text
            )

            # Write JSON to temporary file
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False
            ) as f:
                f.write(json_data)
                json_file = f.name

            try:
                # Parse JSON into XDM value
                xdm_value = self.processor.parse_json(json_file_name=json_file)

                # Call named template and pass data as parameter (if template supports it)
                # Otherwise use apply_templates with the parsed JSON as context
                executable.set_initial_match_selection(xdm_value=xdm_value)
                result = executable.apply_templates_returning_string()
            finally:
                # Clean up temporary file
                if os.path.exists(json_file):
                    os.unlink(json_file)

            if debug:
                print(f"[XSLT Debug] Input JSON:\n{json_data}")
                print(f"[XSLT Debug] Output HTML length: {len(result)} chars")

            return result

        except Exception as e:
            if debug:
                print(f"[XSLT Error] {e}")
                print(f"[XSLT Error] Input data: {json_data}")
            raise RuntimeError(f"XSLT transformation failed: {e}") from e

    def render_from_spec(
        self, spec: Dict[str, Any], records: list, template_path: str, **kwargs
    ) -> str:
        """
        Convenience method for rendering VibeCForms data.

        Args:
            spec: Form specification dictionary
            records: List of record dictionaries
            template_path: Path to XSLT template
            **kwargs: Additional arguments passed to render()

        Returns:
            Rendered HTML string
        """
        data = {"spec": spec, "records": records}

        return self.render(data, template_path=template_path, **kwargs)

    def clear_cache(self) -> None:
        """Clear all compiled templates from cache."""
        self.compiled_templates.clear()

    def get_version(self) -> str:
        """Get Saxon processor version."""
        return self.processor.version

    def __del__(self):
        """Cleanup processor resources."""
        if hasattr(self, "processor"):
            del self.processor


def create_renderer(**kwargs) -> XSLTRenderer:
    """
    Factory function to create an XSLT renderer.

    Args:
        **kwargs: Arguments passed to XSLTRenderer constructor

    Returns:
        XSLTRenderer instance
    """
    return XSLTRenderer(**kwargs)
