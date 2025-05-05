"""Template rendering utilities."""
import os
import logging
from jinja2 import Environment, FileSystemLoader

# Configure logging
logger = logging.getLogger(__name__)

# Get the base directory of the templates
template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')

# Create Jinja2 environment
env = Environment(
    loader=FileSystemLoader(template_dir)
)


def render_template(template_name, **context):
    """Render a template with the given context.
    
    Args:
        template_name: Name of the template file
        **context: Variables to pass to the template
        
    Returns:
        str: Rendered template as a string
    """
    try:
        template = env.get_template(template_name)
        return template.render(**context)
    except Exception as e:
        logger.error(f"Failed to render template {template_name}: {str(e)}")
        raise