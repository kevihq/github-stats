"""SVG rendering module using Jinja2 templates.

This module provides functionality to render SVG files from JSON data
using Jinja2 templates with proper error handling and validation.
"""

import json
import logging
from pathlib import Path
from typing import Any

from jinja2 import (
    Environment,
    FileSystemLoader,
    TemplateNotFound,
    select_autoescape,
)

logger = logging.getLogger(__name__)


class RenderError(Exception):
    """Base exception for rendering errors."""


class DataLoadError(RenderError):
    """Raised when data cannot be loaded from JSON file."""


class TemplateRenderError(RenderError):
    """Raised when template rendering fails."""


class FileWriteError(RenderError):
    """Raised when output file cannot be written."""


def load_json_data(json_path: Path) -> dict[str, Any]:
    """Load and validate JSON data from file.

    Args:
        json_path: Path to the JSON file

    Returns:
        Parsed JSON data as dictionary

    Raises:
        DataLoadError: If file doesn't exist or JSON is invalid
    """
    if not json_path.exists():
        raise DataLoadError(f"JSON file not found: {json_path}")

    try:
        with json_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise DataLoadError(f"Invalid JSON in {json_path}: {e}") from e
    except OSError as e:
        raise DataLoadError(f"Cannot read file {json_path}: {e}") from e

    if not isinstance(data, dict):
        raise DataLoadError(f"Expected JSON object, got {type(data).__name__}")

    return data


def render_template(
    template_dir: Path,
    template_name: str,
    data: dict[str, Any],
    autoescape: bool = True,
) -> str:
    """Render Jinja2 template with provided data.

    Args:
        template_dir: Directory containing templates
        template_name: Name of the template file
        data: Data to pass to template
        autoescape: Enable autoescaping for security (default: True)

    Returns:
        Rendered template content

    Raises:
        TemplateRenderError: If template cannot be loaded or rendered
    """
    try:
        env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape() if autoescape else False,
            trim_blocks=True,
            lstrip_blocks=True,
        )
        template = env.get_template(template_name)
        return template.render(**data)
    except TemplateNotFound as e:
        raise TemplateRenderError(
            f"Template '{template_name}' not found in {template_dir}"
        ) from e
    except Exception as e:
        raise TemplateRenderError(f"Template rendering failed: {e}") from e


def write_output(output_path: Path, content: str) -> None:
    """Write content to output file.

    Args:
        output_path: Path where content will be written
        content: Content to write

    Raises:
        FileWriteError: If file cannot be written
    """
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as f:
            f.write(content)
    except OSError as e:
        raise FileWriteError(f"Cannot write to {output_path}: {e}") from e


def render_svg(
    json_file: str | Path = "stats.json",
    output_file: str | Path = "stats.svg",
    template_dir: str | Path = "src/templates",
    template_name: str = "modern_artificer.svg.j2",
) -> None:
    """Render SVG from JSON data using Jinja2 template.

    Args:
        json_file: Path to input JSON file (default: 'stats.json')
        output_file: Path to output SVG file (default: 'stats.svg')
        template_dir: Directory containing templates (default: 'src/templates')
        template_name: Template filename (default: 'modern_artificer.svg.j2')

    Raises:
        RenderError: If any step of the rendering process fails
    """
    json_path = Path(json_file)
    output_path = Path(output_file)
    templates_path = Path(template_dir)

    logger.info(f"Loading data from {json_path}")
    data = load_json_data(json_path)

    logger.info(f"Rendering template '{template_name}'")
    svg_content = render_template(templates_path, template_name, data)

    logger.info(f"Writing output to {output_path}")
    write_output(output_path, svg_content)

    logger.info(f"SVG generated successfully: {output_path}")


def main() -> None:
    """Main entry point for CLI execution."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    try:
        render_svg()
    except RenderError as e:
        logger.error(f"❌ {e}")
        raise SystemExit(1) from e


if __name__ == "__main__":
    main()
