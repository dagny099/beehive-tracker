# UI Components API Reference

The UI components module provides reusable Streamlit interface elements, visualization utilities, and user interaction patterns for the beehive tracker application.

!!! warning "🔴 Critical Gap - TODO"
    **This API reference needs complete documentation including:**
    - Complete component parameter specifications and customization options
    - Streamlit session state integration patterns
    - Custom CSS and styling guidelines
    - Responsive design considerations for different screen sizes
    - Component testing and validation patterns

## Overview

The UI system consists of multiple modules that provide consistent interface components:

- `src/ui_components.py`: Core reusable UI elements
- `src/app_components.py`: Specialized beehive analysis components
- `src/timeline_component.py`: Timeline visualization and interaction

### Core UI Components

**Photo Display Components:**
```python
def display_image_with_metadata(
    image: Any,
    filename: str,
    metadata: Dict[str, Any]
) -> None:
    """Display image alongside extracted metadata in organized layout.

    Args:
        image: Image object or file path
        filename: Original filename for display
        metadata: Complete metadata dictionary including EXIF, colors, etc.
    """

def create_photo_gallery(
    photos: List[Dict],
    columns: int = 3,
    show_metadata: bool = True
) -> None:
    """Create responsive photo gallery layout."""
```

**Analysis Display Components:**
```python
def display_color_palette(
    color_data: Dict[str, Any],
    show_percentages: bool = True
) -> None:
    """Display color analysis results with visual swatches.

    Args:
        color_data: Color analysis results from image processing
        show_percentages: Whether to show color distribution percentages
    """

def display_weather_data(
    weather_info: Dict[str, Any],
    compact: bool = False
) -> None:
    """Display weather correlation data in formatted layout."""
```

### Specialized Beehive Components

**Inspection Analysis Components:**
```python
def render_inspection_overview(inspection_data: Dict) -> None:
    """Render complete inspection summary with all analysis results."""

def display_hive_assessment_form() -> Dict[str, Any]:
    """Render interactive form for user assessment and annotations.

    Returns:
        Dictionary containing user input from assessment form
    """

def show_ai_analysis_results(
    analysis_results: Dict,
    confidence_threshold: float = 0.5
) -> None:
    """Display computer vision analysis with confidence indicators."""
```

### Timeline Visualization Components

**Interactive Timeline:**
```python
def render_timeline(
    inspection_data: List[Dict],
    filters: Dict[str, Any] = None
) -> None:
    """Render interactive Plotly timeline of inspections.

    Args:
        inspection_data: List of inspection records
        filters: Optional filters for date ranges, locations, etc.
    """

def create_timeline_filters() -> Dict[str, Any]:
    """Create interactive filter controls for timeline view.

    Returns:
        Dictionary containing user-selected filter values
    """
```

### Data Export Components

**Export Interface Elements:**
```python
def render_export_options(
    available_formats: List[str] = ["JSON", "CSV"]
) -> Tuple[str, Dict[str, Any]]:
    """Render export format selection and configuration options.

    Returns:
        Tuple of (selected_format, export_configuration)
    """

def show_export_progress(
    current: int,
    total: int,
    operation: str = "Exporting"
) -> None:
    """Display progress bar for export operations."""
```

### Form and Input Components

**User Input Forms:**
```python
def create_annotation_form(
    existing_data: Dict = None
) -> Dict[str, Any]:
    """Create form for adding inspection annotations and notes.

    Args:
        existing_data: Pre-populate form with existing annotation data

    Returns:
        Dictionary containing form input values
    """

def render_settings_panel() -> Dict[str, Any]:
    """Render application settings configuration panel."""
```

### Navigation Components

**Sidebar and Navigation:**
```python
def render_sidebar() -> str:
    """Render application sidebar with navigation and status information.

    Returns:
        Selected navigation item
    """

def create_breadcrumb_navigation(current_page: str, context: Dict) -> None:
    """Display breadcrumb navigation showing current location."""
```

### CSS and Styling

**Custom Styling Components:**
```python
# Beehive-themed CSS constants
HONEY_COLORS = {
    "primary": "#FFC300",      # Golden honey
    "secondary": "#D4A017",    # Darker amber
    "accent": "#FFE066",       # Light honey
    "background": "#FFF2B3"    # Cream background
}

COMPONENT_STYLES = {
    "metadata_container": """
        background-color: rgba(30, 30, 30, 0.1);
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
    """,
    "color_swatch": """
        display: inline-block;
        width: 30px;
        height: 30px;
        margin-right: 5px;
        border-radius: 5px;
        border: 1px solid rgba(255, 255, 255, 0.2);
    """
}
```

### Session State Management

**Session Integration Patterns:**
```python
def initialize_session_state() -> None:
    """Initialize all required session state variables for UI components."""

def update_session_with_user_input(form_data: Dict) -> None:
    """Update session state with user form input."""

def get_session_display_preferences() -> Dict[str, Any]:
    """Retrieve user display preferences from session state."""
```

### Component Integration Examples

**Complete Analysis Display Workflow:**
```python
def render_complete_inspection_analysis(inspection_id: str):
    """Render complete inspection analysis interface."""

    # Get inspection data
    inspection = get_inspection_by_id(inspection_id)

    # Create header with inspection info
    render_inspection_header(inspection)

    # Display photos in gallery format
    create_photo_gallery(inspection["photos"])

    # Show analysis results
    col1, col2 = st.columns(2)

    with col1:
        display_color_palette(inspection["color_analysis"])
        display_weather_data(inspection["weather_data"])

    with col2:
        show_ai_analysis_results(inspection["ai_analysis"])
        display_user_annotations(inspection["annotations"])

    # Add export options
    export_format, config = render_export_options()
    if st.button("Export Analysis"):
        export_inspection_data(inspection, export_format, config)
```

### Responsive Design Patterns

**Multi-Column Layouts:**
```python
def create_responsive_layout(
    content_blocks: List[callable],
    breakpoints: Dict[str, int] = None
) -> None:
    """Create responsive layout that adapts to screen size.

    Args:
        content_blocks: List of functions that render content
        breakpoints: Screen width breakpoints for layout changes
    """
```

### Error Handling and User Feedback

**User Feedback Components:**
```python
def show_success_message(message: str, duration: int = 3) -> None:
    """Display success message to user."""

def show_error_message(error: str, details: str = None) -> None:
    """Display error message with optional details."""

def show_loading_spinner(message: str = "Processing...") -> None:
    """Display loading indicator during operations."""
```

### Performance Optimization

**Efficient Rendering Patterns:**
- **Component caching**: Cache expensive component renders
- **Lazy loading**: Load heavy components only when needed
- **Progressive enhancement**: Basic functionality first, enhancements after
- **State optimization**: Minimize unnecessary re-renders

### Configuration and Theming

**Theme Configuration:**
```python
THEME_CONFIG = {
    "colors": HONEY_COLORS,
    "fonts": {
        "primary": "Roboto",
        "code": "Roboto Mono"
    },
    "spacing": {
        "small": "8px",
        "medium": "16px",
        "large": "24px"
    }
}
```

### Testing Patterns

**Component Testing:**
```python
def test_component_render(component_func, test_data):
    """Test component rendering with various input scenarios."""

def validate_user_input(input_data: Dict) -> Tuple[bool, List[str]]:
    """Validate user input from form components."""
```

---

!!! info "🟡 Important Gap - TODO"
    **Missing documentation that needs to be added:**
    - Complete component API reference with all parameters
    - Streamlit session state best practices and patterns
    - Custom CSS styling guidelines and theme customization
    - Responsive design implementation details
    - Component testing frameworks and validation patterns
    - Accessibility considerations and WCAG compliance
    - Performance optimization techniques for complex interfaces
    - Integration patterns with external visualization libraries
    - User experience guidelines and design principles