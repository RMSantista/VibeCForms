"""Convert VibeCForms data structures to XML for XSLT processing."""

import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional


class XMLBuilder:
    """Build XML documents from VibeCForms JSON specs and data."""

    @staticmethod
    def build_form_page_xml(
        spec: Dict[str, Any],
        form_name: str,
        records: List[Dict[str, Any]],
        menu_items: List[Dict[str, Any]],
        error: str = "",
        new_record_id: str = "",
        form_data: Optional[Dict[str, Any]] = None,
    ) -> ET.Element:
        """Build XML for form page rendering.

        Returns XML structure like:
        <form-page form-name="contatos" error="" new-record-id="uuid-123">
            <spec title="Contatos" icon="fa-address-book">
                <fields>
                    <field name="nome" label="Nome" type="text" required="true" value=""/>
                </fields>
                <default-tags>
                    <tag>lead</tag>
                </default-tags>
            </spec>
            <records>
                <record id="uuid-1">
                    <field name="nome">João Silva</field>
                </record>
            </records>
            <menu>...</menu>
        </form-page>
        """
        root = ET.Element("form-page")
        root.set("form-name", form_name)
        root.set("error", error)
        root.set("new-record-id", new_record_id)

        # Spec section
        spec_elem = ET.SubElement(root, "spec")
        spec_elem.set("title", spec.get("title", ""))
        spec_elem.set("icon", spec.get("icon", "fa-file-alt"))

        # Fields
        fields_elem = ET.SubElement(spec_elem, "fields")
        for field in spec.get("fields", []):
            field_elem = XMLBuilder._build_field_element(fields_elem, field, form_data)

        # Default tags
        if "default_tags" in spec and spec["default_tags"]:
            tags_elem = ET.SubElement(spec_elem, "default-tags")
            for tag in spec["default_tags"]:
                tag_elem = ET.SubElement(tags_elem, "tag")
                tag_elem.text = str(tag)

        # Records
        records_elem = ET.SubElement(root, "records")
        for record in records:
            XMLBuilder._build_record_element(records_elem, record, spec)

        # Menu
        menu_elem = ET.SubElement(root, "menu")
        XMLBuilder._build_menu_items(menu_elem, menu_items, form_name)

        return root

    @staticmethod
    def _build_field_element(
        parent: ET.Element,
        field: Dict[str, Any],
        form_data: Optional[Dict[str, Any]] = None,
    ) -> ET.Element:
        """Build a field element with all attributes."""
        field_elem = ET.SubElement(parent, "field")
        field_elem.set("name", field["name"])
        field_elem.set("label", field["label"])
        field_elem.set("type", field["type"])
        field_elem.set("required", str(field.get("required", False)).lower())

        # Value from form_data if available
        value = ""
        if form_data and field["name"] in form_data:
            value = str(form_data[field["name"]])
        field_elem.set("value", value)

        # Options for select/radio
        if "options" in field and field["options"]:
            options_elem = ET.SubElement(field_elem, "options")
            for option in field["options"]:
                opt_elem = ET.SubElement(options_elem, "option")
                opt_elem.set("value", option["value"])
                opt_elem.set("label", option["label"])

        # Min/max/step for range
        if field["type"] == "range":
            field_elem.set("min", str(field.get("min", 0)))
            field_elem.set("max", str(field.get("max", 100)))
            field_elem.set("step", str(field.get("step", 1)))

        # Datasource for search
        if "datasource" in field:
            field_elem.set("datasource", field["datasource"])

        return field_elem

    @staticmethod
    def _build_record_element(
        parent: ET.Element, record: Dict[str, Any], spec: Dict[str, Any]
    ):
        """Build a record element with all field values."""
        record_elem = ET.SubElement(parent, "record")
        record_elem.set("id", record.get("_record_id", ""))

        for field in spec.get("fields", []):
            field_name = field["name"]
            field_elem = ET.SubElement(record_elem, "field")
            field_elem.set("name", field_name)
            field_elem.set("type", field["type"])

            # Get value
            value = record.get(field_name, "")

            # Add options for select/radio (for label lookup in table mode)
            if "options" in field and field["options"]:
                options_elem = ET.SubElement(field_elem, "options")
                for option in field["options"]:
                    opt_elem = ET.SubElement(options_elem, "option")
                    opt_elem.set("value", option["value"])
                    opt_elem.set("label", option["label"])
                field_elem.set("value", str(value))
            else:
                # For non-select fields, set value as text or attribute
                if field["type"] == "checkbox":
                    field_elem.set("value", str(value).lower())
                else:
                    field_elem.text = str(value) if value else ""

    @staticmethod
    def _build_menu_items(
        parent: ET.Element, items: List[Dict[str, Any]], current_path: str
    ):
        """Recursively build menu items."""
        for item in items:
            item_elem = ET.SubElement(parent, "item")
            item_elem.set("type", item["type"])
            item_elem.set("path", item["path"])

            if item["type"] == "form":
                item_elem.set("title", item["title"])
                item_elem.set("icon", item.get("icon", "fa-file-alt"))
                item_elem.set("active", str(item["path"] == current_path).lower())
            else:  # folder
                item_elem.set("title", item["name"])
                item_elem.set("icon", item.get("icon", "fa-folder"))
                item_elem.set(
                    "active-path", str(current_path.startswith(item["path"])).lower()
                )

                # Recursively add children
                if "children" in item and item["children"]:
                    XMLBuilder._build_menu_items(
                        item_elem, item["children"], current_path
                    )

    @staticmethod
    def build_index_page_xml(
        forms: List[Dict[str, Any]], menu_items: List[Dict[str, Any]]
    ) -> ET.Element:
        """Build XML for index/landing page."""
        root = ET.Element("index-page")

        # Add forms
        for form in forms:
            form_elem = ET.SubElement(root, "form")
            form_elem.set("title", form["title"])
            form_elem.set("path", form["path"])
            form_elem.set("icon", form.get("icon", "fa-file-alt"))
            form_elem.set("category", form.get("category", "Geral"))

        # Add menu
        menu_elem = ET.SubElement(root, "menu")
        XMLBuilder._build_menu_items(menu_elem, menu_items, "")

        return root

    @staticmethod
    def build_edit_page_xml(
        spec: Dict[str, Any],
        form_name: str,
        record: Dict[str, Any],
        menu_items: List[Dict[str, Any]],
        record_tags: List,
        error: str = "",
    ) -> ET.Element:
        """Build XML for edit page rendering."""
        root = ET.Element("edit-page")
        root.set("form-name", form_name)
        root.set("error", error)
        root.set("record-id", record.get("_record_id", ""))

        # Spec section
        spec_elem = ET.SubElement(root, "spec")
        spec_elem.set("title", spec.get("title", ""))
        spec_elem.set("icon", spec.get("icon", "fa-file-alt"))

        # Fields with current values
        fields_elem = ET.SubElement(spec_elem, "fields")
        for field in spec.get("fields", []):
            XMLBuilder._build_field_element(fields_elem, field, record)

        # Record tags
        tags_elem = ET.SubElement(root, "tags")
        for tag in record_tags:
            tag_elem = ET.SubElement(tags_elem, "tag")
            if isinstance(tag, dict):
                tag_elem.text = tag.get("tag", "")
            else:
                tag_elem.text = str(tag)

        # Menu
        menu_elem = ET.SubElement(root, "menu")
        XMLBuilder._build_menu_items(menu_elem, menu_items, form_name)

        return root

    @staticmethod
    def build_kanban_xml(
        board_name: str,
        board_config: Dict[str, Any],
        cards: Dict[str, List[Dict[str, Any]]],
        menu_items: List[Dict[str, Any]],
    ) -> ET.Element:
        """Build XML for kanban board rendering.

        Args:
            board_name: Board name (e.g., "sales_pipeline")
            board_config: Board configuration dict with title, form, columns
            cards: Cards organized by column tag (from kanban_service.get_all_board_cards())
            menu_items: Menu structure

        Returns:
            XML element for kanban page

        Example XML structure:
            <kanban-page board-name="sales_pipeline">
                <board title="Pipeline de Vendas" form="contatos">
                    <columns>
                        <column tag="lead" label="Leads" color="blue" icon="fa-circle">
                            <card id="uuid-1">
                                <field name="nome">João Silva</field>
                            </card>
                        </column>
                    </columns>
                </board>
                <menu>...</menu>
            </kanban-page>
        """
        root = ET.Element("kanban-page")
        root.set("board-name", board_name)

        # Board section
        board_elem = ET.SubElement(root, "board")
        board_elem.set("title", board_config.get("title", ""))
        board_elem.set("form", board_config.get("form", ""))

        # Columns
        columns_elem = ET.SubElement(board_elem, "columns")
        for column in board_config.get("columns", []):
            col_elem = ET.SubElement(columns_elem, "column")
            col_elem.set("tag", column.get("tag", ""))
            col_elem.set("label", column.get("label", ""))
            col_elem.set("color", column.get("color", "gray"))
            col_elem.set("icon", column.get("icon", "fa-circle"))

            # Cards for this column
            tag = column.get("tag")
            column_cards = cards.get(tag, [])

            for card in column_cards:
                card_elem = ET.SubElement(col_elem, "card")
                card_elem.set("id", card.get("_record_id", ""))

                # Add all fields as child elements
                for field_name, field_value in card.items():
                    if field_name != "_record_id":
                        field_elem = ET.SubElement(card_elem, "field")
                        field_elem.set("name", field_name)
                        field_elem.text = str(field_value) if field_value else ""

        # Menu
        menu_elem = ET.SubElement(root, "menu")
        XMLBuilder._build_menu_items(menu_elem, menu_items, "")

        return root

    @staticmethod
    def build_tags_manager_xml(
        forms: List[Dict[str, Any]],
        menu_items: List[Dict[str, Any]],
    ) -> ET.Element:
        """Build XML for tags manager page.

        Args:
            forms: List of all forms with title, path, icon, category
            menu_items: Menu structure

        Returns:
            XML element for tags manager page

        Example XML structure:
            <tags-manager-page>
                <forms>
                    <form path="contatos" title="Contatos" icon="fa-address-book" category="Geral"/>
                </forms>
                <menu>...</menu>
            </tags-manager-page>
        """
        root = ET.Element("tags-manager-page")

        # Forms section
        forms_elem = ET.SubElement(root, "forms")
        for form in forms:
            form_elem = ET.SubElement(forms_elem, "form")
            form_elem.set("path", form["path"])
            form_elem.set("title", form["title"])
            form_elem.set("icon", form.get("icon", "fa-file-alt"))
            form_elem.set("category", form.get("category", "Geral"))

        # Menu
        menu_elem = ET.SubElement(root, "menu")
        XMLBuilder._build_menu_items(menu_elem, menu_items, "")

        return root

    @staticmethod
    def build_migration_confirm_xml(
        form_path: str,
        form_title: str,
        record_count: int,
        schema_change: Optional[Any],
        backend_change: Optional[Any],
        has_destructive_changes: bool,
        has_warnings: bool,
        menu_items: List[Dict[str, Any]],
    ) -> ET.Element:
        """Build XML for migration confirmation page.

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
            XML element for migration confirmation page

        Example XML structure:
            <migration-confirm-page form-path="contatos" form-title="Contatos" record-count="23">
                <schema-changes>
                    <change type="ADD_FIELD" field-name="cpf" field-type="text"/>
                </schema-changes>
                <backend-change old-backend="txt" new-backend="sqlite"/>
                <flags destructive="true" warnings="true"/>
                <menu>...</menu>
            </migration-confirm-page>
        """
        root = ET.Element("migration-confirm-page")
        root.set("form-path", form_path)
        root.set("form-title", form_title)
        root.set("record-count", str(record_count))

        # Schema changes
        if schema_change and hasattr(schema_change, "changes"):
            changes_elem = ET.SubElement(root, "schema-changes")
            for change in schema_change.changes:
                change_elem = ET.SubElement(changes_elem, "change")

                # Get change type (handle enum)
                change_type = (
                    change.change_type.value
                    if hasattr(change.change_type, "value")
                    else str(change.change_type)
                )
                change_elem.set("type", change_type)

                # Add change-specific attributes
                if hasattr(change, "field_name"):
                    change_elem.set("field-name", change.field_name)
                if hasattr(change, "field_type"):
                    change_elem.set("field-type", change.field_type)
                if hasattr(change, "old_name"):
                    change_elem.set("old-name", change.old_name)
                if hasattr(change, "new_name"):
                    change_elem.set("new-name", change.new_name)
                if hasattr(change, "old_type"):
                    change_elem.set("old-type", change.old_type)
                if hasattr(change, "new_type"):
                    change_elem.set("new-type", change.new_type)

        # Backend change
        if backend_change:
            backend_elem = ET.SubElement(root, "backend-change")
            backend_elem.set("old-backend", backend_change.old_backend)
            backend_elem.set("new-backend", backend_change.new_backend)

        # Flags
        flags_elem = ET.SubElement(root, "flags")
        flags_elem.set("destructive", str(has_destructive_changes).lower())
        flags_elem.set("warnings", str(has_warnings).lower())

        # Menu
        menu_elem = ET.SubElement(root, "menu")
        XMLBuilder._build_menu_items(menu_elem, menu_items, "")

        return root

    @staticmethod
    def element_to_string(elem: ET.Element) -> str:
        """Convert XML element to string."""
        ET.indent(elem, space="  ")  # Pretty print
        return ET.tostring(elem, encoding="unicode", method="xml")
