#!/usr/bin/env python3
"""
Jinja2 to XSLT 3.0 Conversion Helper

Analyzes Jinja2 templates and suggests equivalent XSLT 3.0 pattern-matching rules.
"""

import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple


class Jinja2Analyzer:
    """Analyzes Jinja2 templates to extract structure."""

    def __init__(self, template_content: str):
        self.content = template_content
        self.loops: List[Dict] = []
        self.conditionals: List[Dict] = []
        self.variables: List[str] = []

    def analyze(self) -> Dict:
        """Analyze the Jinja2 template."""
        self._extract_loops()
        self._extract_conditionals()
        self._extract_variables()

        return {
            "loops": self.loops,
            "conditionals": self.conditionals,
            "variables": self.variables,
        }

    def _extract_loops(self):
        """Extract for loops from template."""
        pattern = r"{%\s*for\s+(\w+)\s+in\s+([\w.]+)\s*%}(.*?){%\s*endfor\s*%}"
        matches = re.finditer(pattern, self.content, re.DOTALL)

        for match in matches:
            var_name = match.group(1)
            iterable = match.group(2)
            body = match.group(3)

            self.loops.append(
                {"variable": var_name, "iterable": iterable, "body": body}
            )

    def _extract_conditionals(self):
        """Extract if statements from template."""
        pattern = r"{%\s*if\s+(.+?)\s*%}(.*?)(?:{%\s*elif\s+(.+?)\s*%}(.*?))*(?:{%\s*else\s*%}(.*?)){%\s*endif\s*%}"
        matches = re.finditer(pattern, self.content, re.DOTALL)

        for match in matches:
            condition = match.group(1)
            body = match.group(2)

            self.conditionals.append({"condition": condition, "body": body})

    def _extract_variables(self):
        """Extract variable references."""
        pattern = r"{{\s*([\w.]+)\s*}}"
        matches = re.finditer(pattern, self.content)

        self.variables = list(set(match.group(1) for match in matches))


class XSLTGenerator:
    """Generates XSLT 3.0 templates from Jinja2 analysis."""

    def __init__(self, analysis: Dict):
        self.analysis = analysis

    def generate_suggestions(self) -> str:
        """Generate XSLT suggestions based on analysis."""
        output = []

        output.append("<!-- XSLT 3.0 Pattern Suggestions -->")
        output.append("")

        # Suggest templates for loops
        if self.analysis["loops"]:
            output.append("<!-- Loop Patterns -->")
            for loop in self.analysis["loops"]:
                suggestion = self._convert_loop(loop)
                output.append(suggestion)
                output.append("")

        # Suggest templates for conditionals
        if self.analysis["conditionals"]:
            output.append("<!-- Conditional Patterns -->")
            for cond in self.analysis["conditionals"]:
                suggestion = self._convert_conditional(cond)
                output.append(suggestion)
                output.append("")

        # Show variable access conversions
        if self.analysis["variables"]:
            output.append("<!-- Variable Access Conversions -->")
            for var in self.analysis["variables"]:
                jinja_syntax = f"{{{{ {var} }}}}"
                xslt_syntax = self._convert_variable(var)
                output.append(f"<!-- {jinja_syntax} -> {xslt_syntax} -->")
            output.append("")

        return "\n".join(output)

    def _convert_loop(self, loop: Dict) -> str:
        """Convert Jinja2 loop to XSLT template suggestion."""
        var_name = loop["variable"]
        iterable = loop["iterable"]

        # Suggest pattern matching instead of explicit iteration
        suggestion = f"""<!-- Jinja2: {{% for {var_name} in {iterable} %}} -->
<!-- XSLT: Define template rules that match array items -->
<xsl:template match="array(*)" mode="{iterable}">
  <xsl:apply-templates select="?*"/>
</xsl:template>

<!-- Or match individual items with specific patterns -->
<xsl:template match="map(*)[?type]">
  <!-- Process item based on its properties -->
  <!-- Access properties: ?name, ?type, ?value, etc. -->
</xsl:template>"""

        return suggestion

    def _convert_conditional(self, cond: Dict) -> str:
        """Convert Jinja2 conditional to XSLT pattern suggestion."""
        condition = cond["condition"]

        # Try to extract type checks
        type_match = re.search(r'(\w+)\.type\s*==\s*["\'](\w+)["\']', condition)

        if type_match:
            var_name = type_match.group(1)
            type_value = type_match.group(2)

            suggestion = f"""<!-- Jinja2: {{% if {condition} %}} -->
<!-- XSLT: Use pattern matching instead of conditionals -->
<xsl:template match="map(*)[?type = '{type_value}']">
  <!-- Template automatically applies only when type='{type_value}' -->
</xsl:template>"""
        else:
            suggestion = f"""<!-- Jinja2: {{% if {condition} %}} -->
<!-- XSLT: Use pattern matching or xsl:choose -->
<xsl:template match="map(*)[{self._jinja_to_xpath(condition)}]">
  <!-- Pattern-based approach (preferred) -->
</xsl:template>

<!-- Or use xsl:choose for complex logic -->
<xsl:choose>
  <xsl:when test="{self._jinja_to_xpath(condition)}">
    <!-- condition true -->
  </xsl:when>
  <xsl:otherwise>
    <!-- condition false -->
  </xsl:otherwise>
</xsl:choose>"""

        return suggestion

    def _convert_variable(self, var: str) -> str:
        """Convert Jinja2 variable access to XSLT."""
        # Handle dot notation
        parts = var.split(".")

        if len(parts) == 1:
            # Simple variable
            return f"{{?{var}}}"  # Attribute value template
        else:
            # Nested access
            xpath = "?" + "?".join(parts)
            return f"{{{xpath}}}"

    def _jinja_to_xpath(self, condition: str) -> str:
        """Convert Jinja2 condition to XPath (basic conversion)."""
        # Replace common patterns
        xpath = condition
        xpath = re.sub(r"(\w+)\.(\w+)", r"?\1?\2", xpath)  # dot notation
        xpath = xpath.replace("==", "=")  # equality
        xpath = xpath.replace("!=", "!=")  # inequality (same)
        xpath = xpath.replace(" and ", " and ")  # logical and
        xpath = xpath.replace(" or ", " or ")  # logical or

        return xpath


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python3 convert_jinja_to_xslt.py <template_file>")
        sys.exit(1)

    template_path = Path(sys.argv[1])

    if not template_path.exists():
        print(f"Error: Template file not found: {template_path}")
        sys.exit(1)

    # Read template
    with open(template_path, "r", encoding="utf-8") as f:
        template_content = f.read()

    print(f"Analyzing Jinja2 template: {template_path}")
    print("=" * 60)
    print()

    # Analyze
    analyzer = Jinja2Analyzer(template_content)
    analysis = analyzer.analyze()

    # Generate XSLT suggestions
    generator = XSLTGenerator(analysis)
    suggestions = generator.generate_suggestions()

    print(suggestions)
    print()
    print("=" * 60)
    print("\nNext steps:")
    print("1. Review the suggested XSLT patterns above")
    print("2. Adapt patterns to your specific data structure")
    print("3. Test transformations with sample data")
    print("4. See assets/form_template.xslt for complete examples")


if __name__ == "__main__":
    main()
