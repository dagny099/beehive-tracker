"""
Mock response fixtures for Google Cloud Vision API testing.

This module provides comprehensive mock responses that mirror the actual Vision API
structure, enabling reliable testing without making real API calls.
"""

from datetime import datetime


class MockVisionResponse:
    """Mock Vision API response structure for testing."""
    
    def __init__(self, label_annotations=None, image_properties_annotation=None, 
                 localized_object_annotations=None, error=None):
        self.label_annotations = label_annotations or []
        self.image_properties_annotation = image_properties_annotation
        self.localized_object_annotations = localized_object_annotations or []
        self.error = error


class MockLabel:
    """Mock label annotation from Vision API."""
    
    def __init__(self, description, score):
        self.description = description
        self.score = score


class MockColor:
    """Mock color object from Vision API."""
    
    def __init__(self, red, green, blue):
        self.red = red
        self.green = green
        self.blue = blue


class MockDominantColor:
    """Mock dominant color from Vision API."""
    
    def __init__(self, color, score, pixel_fraction):
        self.color = color
        self.score = score
        self.pixel_fraction = pixel_fraction


class MockDominantColors:
    """Mock dominant colors collection from Vision API."""
    
    def __init__(self, colors):
        self.colors = colors


class MockImageProperties:
    """Mock image properties from Vision API."""
    
    def __init__(self, dominant_colors):
        self.dominant_colors = dominant_colors


class MockVertex:
    """Mock normalized vertex for object bounding boxes."""
    
    def __init__(self, x, y):
        self.x = x
        self.y = y


class MockBoundingPoly:
    """Mock bounding polygon for detected objects."""
    
    def __init__(self, normalized_vertices):
        self.normalized_vertices = normalized_vertices


class MockLocalizedObject:
    """Mock localized object from Vision API."""
    
    def __init__(self, name, score, bounding_poly):
        self.name = name
        self.score = score
        self.bounding_poly = bounding_poly


# Test fixtures for different scenarios

SUCCESSFUL_BEE_RESPONSE = MockVisionResponse(
    label_annotations=[
        MockLabel("Bee", 0.92),
        MockLabel("Honey bee", 0.88),
        MockLabel("Beehive", 0.85),
        MockLabel("Honeycomb", 0.82),
        MockLabel("Insect", 0.79),
        MockLabel("Yellow", 0.75),
        MockLabel("Wax", 0.68)
    ],
    image_properties_annotation=MockImageProperties(
        MockDominantColors([
            MockDominantColor(MockColor(255.0, 193.0, 7.0), 0.35, 0.24),  # Yellow
            MockDominantColor(MockColor(139.0, 69.0, 19.0), 0.28, 0.18),  # Brown
            MockDominantColor(MockColor(210.0, 180.0, 140.0), 0.22, 0.15), # Tan
            MockDominantColor(MockColor(0.0, 0.0, 0.0), 0.15, 0.12),      # Black
        ])
    ),
    localized_object_annotations=[
        MockLocalizedObject(
            "Bee", 0.89,
            MockBoundingPoly([
                MockVertex(0.2, 0.3),
                MockVertex(0.4, 0.3),
                MockVertex(0.4, 0.6),
                MockVertex(0.2, 0.6)
            ])
        ),
        MockLocalizedObject(
            "Honeycomb", 0.76,
            MockBoundingPoly([
                MockVertex(0.1, 0.1),
                MockVertex(0.9, 0.1),
                MockVertex(0.9, 0.9),
                MockVertex(0.1, 0.9)
            ])
        )
    ]
)

NON_BEE_RESPONSE = MockVisionResponse(
    label_annotations=[
        MockLabel("Flower", 0.94),
        MockLabel("Plant", 0.89),
        MockLabel("Garden", 0.83),
        MockLabel("Red", 0.78),
        MockLabel("Petal", 0.72)
    ],
    image_properties_annotation=MockImageProperties(
        MockDominantColors([
            MockDominantColor(MockColor(220.0, 20.0, 60.0), 0.45, 0.32),  # Red
            MockDominantColor(MockColor(34.0, 139.0, 34.0), 0.35, 0.28),  # Green
            MockDominantColor(MockColor(255.0, 255.0, 255.0), 0.20, 0.15) # White
        ])
    ),
    localized_object_annotations=[
        MockLocalizedObject(
            "Flower", 0.91,
            MockBoundingPoly([
                MockVertex(0.3, 0.2),
                MockVertex(0.7, 0.2),
                MockVertex(0.7, 0.8),
                MockVertex(0.3, 0.8)
            ])
        )
    ]
)

EMPTY_RESPONSE = MockVisionResponse(
    label_annotations=[],
    image_properties_annotation=MockImageProperties(MockDominantColors([])),
    localized_object_annotations=[]
)

LOW_CONFIDENCE_RESPONSE = MockVisionResponse(
    label_annotations=[
        MockLabel("Insect", 0.45),
        MockLabel("Yellow", 0.38),
        MockLabel("Flying", 0.32)
    ],
    image_properties_annotation=MockImageProperties(
        MockDominantColors([
            MockDominantColor(MockColor(128.0, 128.0, 128.0), 0.60, 0.45)  # Gray
        ])
    ),
    localized_object_annotations=[]
)

# Expected processed results for testing

EXPECTED_BEE_ANALYSIS = {
    'labels': [
        {'description': 'Bee', 'score': 0.92, 'bee_related': True},
        {'description': 'Honey bee', 'score': 0.88, 'bee_related': True},
        {'description': 'Beehive', 'score': 0.85, 'bee_related': True},
        {'description': 'Honeycomb', 'score': 0.82, 'bee_related': True},
        {'description': 'Insect', 'score': 0.79, 'bee_related': False},
        {'description': 'Yellow', 'score': 0.75, 'bee_related': False},
        {'description': 'Wax', 'score': 0.68, 'bee_related': True}
    ],
    'colors': [
        {
            'color': 'rgb(255,193,7)',
            'hex': '#ffc107',
            'score': 0.35,
            'pixel_fraction': 0.24
        },
        {
            'color': 'rgb(139,69,19)',
            'hex': '#8b4513',
            'score': 0.28,
            'pixel_fraction': 0.18
        },
        {
            'color': 'rgb(210,180,140)',
            'hex': '#d2b48c',
            'score': 0.22,
            'pixel_fraction': 0.15
        },
        {
            'color': 'rgb(0,0,0)',
            'hex': '#000000',
            'score': 0.15,
            'pixel_fraction': 0.12
        }
    ],
    'objects': [
        {
            'name': 'Bee',
            'score': 0.89,
            'bee_related': True,
            'normalized_vertices': [
                {'x': 0.2, 'y': 0.3},
                {'x': 0.4, 'y': 0.3},
                {'x': 0.4, 'y': 0.6},
                {'x': 0.2, 'y': 0.6}
            ]
        },
        {
            'name': 'Honeycomb',
            'score': 0.76,
            'bee_related': True,
            'normalized_vertices': [
                {'x': 0.1, 'y': 0.1},
                {'x': 0.9, 'y': 0.1},
                {'x': 0.9, 'y': 0.9},
                {'x': 0.1, 'y': 0.9}
            ]
        }
    ],
    'bee_summary': {
        'bee_related_terms_count': 5,
        'bee_objects_detected_count': 2,
        'honey_colors_detected': True,
        'brood_colors_detected': True,
        'top_bee_terms': ['Bee', 'Honey bee', 'Beehive'],
        'suggested_hive_state': 'Active'
    }
}

EXPECTED_NON_BEE_ANALYSIS = {
    'labels': [
        {'description': 'Flower', 'score': 0.94, 'bee_related': False},
        {'description': 'Plant', 'score': 0.89, 'bee_related': False},
        {'description': 'Garden', 'score': 0.83, 'bee_related': False},
        {'description': 'Red', 'score': 0.78, 'bee_related': False},
        {'description': 'Petal', 'score': 0.72, 'bee_related': False}
    ],
    'bee_summary': {
        'bee_related_terms_count': 0,
        'bee_objects_detected_count': 0,
        'honey_colors_detected': False,
        'brood_colors_detected': False,
        'top_bee_terms': [],
        'suggested_hive_state': 'Unknown'
    }
}