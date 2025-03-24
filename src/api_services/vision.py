from google.cloud import vision
from datetime import datetime
import logging
from typing import Dict, Any, Optional
import io

logger = logging.getLogger(__name__)

class BeeVisionAnalyzer:
    """Analyzer class for beehive images using Google Cloud Vision API."""
    
    def __init__(self):
        """Initialize the vision analyzer."""
        self.client = vision.ImageAnnotatorClient()
    
    def analyze_image(self, image_data):
        """
        Analyze an image using Google Cloud Vision API.
        
        Parameters:
            image_data: Image data (bytes) or file path
            
        Returns:
            dict: Analysis results
        """
        try:
            print(f"Analyzing image: {image_data}")
            
            # Handle different input types
            if isinstance(image_data, str):
                print(f"Opening file: {image_data}")
                with open(image_data, 'rb') as image_file:
                    content = image_file.read()
                    print(f"Read {len(content)} bytes from file")
                image = vision.Image(content=content)
            elif isinstance(image_data, bytes):
                print(f"Processing {len(image_data)} bytes of image data")
                image = vision.Image(content=image_data)
            elif isinstance(image_data, io.BytesIO):
                content = image_data.getvalue()
                print(f"Processing {len(content)} bytes from BytesIO")
                image = vision.Image(content=content)
            else:
                error_msg = f"Unsupported image data type: {type(image_data)}"
                print(error_msg)
                raise ValueError(error_msg)
            
            print("Sending request to Vision API")
            # Request multiple feature types in one call
            response = self.client.annotate_image({
                'image': image,
                'features': [
                    {'type_': vision.Feature.Type.LABEL_DETECTION},
                    {'type_': vision.Feature.Type.IMAGE_PROPERTIES},
                    {'type_': vision.Feature.Type.OBJECT_LOCALIZATION}
                ]
            })
            
            print("Processing Vision API response")
            # Process response into structured data
            return self._process_vision_response(response)
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Error in vision analysis: {e}")
            print(error_details)
            return {
                'error': str(e),
                'error_details': error_details,
                'timestamp': datetime.now().isoformat()
            }            

    
    def _process_vision_response(self, response):
        """Process and structure the Vision API response."""
        # Extract labels
        labels = [{'description': label.description, 
                'score': label.score,
                'bee_related': self._is_bee_related(label.description)} 
                for label in response.label_annotations]
        
        # Extract dominant colors - FIX: Convert float color values to integers
        colors = []
        for color in response.image_properties_annotation.dominant_colors.colors[:5]:
            # Convert float color values to integers
            red = int(color.color.red)
            green = int(color.color.green)
            blue = int(color.color.blue)
            
            colors.append({
                'color': f"rgb({red},{green},{blue})",
                'hex': f"#{red:02x}{green:02x}{blue:02x}",
                'score': color.score,
                'pixel_fraction': color.pixel_fraction
            })
        
        # Extract detected objects
        objects = [{'name': obj.name,
                'score': obj.score,
                'bee_related': self._is_bee_related(obj.name),
                'normalized_vertices': [
                    {'x': vertex.x, 'y': vertex.y} 
                    for vertex in obj.bounding_poly.normalized_vertices
                ]}
                for obj in response.localized_object_annotations]
        
        # Structure the analysis results
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'labels': labels,
            'colors': colors,
            'objects': objects,
            'bee_summary': self._generate_bee_summary(labels, objects, colors)
        }
        
        return analysis
    

    def _is_bee_related(self, term):
        """Check if a term is related to bees or beekeeping."""
        bee_terms = [
            'bee', 'honeybee', 'honey bee', 'beehive', 'apiary', 'honeycomb', 
            'queen', 'drone', 'worker bee', 'pollen', 'nectar', 'propolis', 
            'wax', 'brood', 'larva', 'colony', 'swarm', 'frame', 'comb',
            'varroa', 'mite', 'royal jelly', 'apiculture', 'beekeeper'
        ]
        
        # Case-insensitive matching
        term_lower = term.lower()
        for bee_term in bee_terms:
            if bee_term in term_lower:
                return True
        return False
    
    def _generate_bee_summary(self, labels, objects, colors):
        """Generate a beekeeping-focused summary from the analysis."""
        # Extract bee-related labels and objects
        bee_labels = [label for label in labels if label['bee_related']]
        bee_objects = [obj for obj in objects if obj['bee_related']]
        
        # Analyze colors for honey/wax/health indications
        yellows = []
        browns = []
        for color in colors:
            try:
                hex_color = color['hex'].lstrip('#')
                # Convert hex to RGB
                r = int(hex_color[0:2], 16)
                g = int(hex_color[2:4], 16)
                b = int(hex_color[4:6], 16)
                
                # Yellow detection (honey color)
                if r > 180 and g > 150 and b < 100:
                    yellows.append(color)
                
                # Brown detection (brood comb)
                if r > 100 and g > 50 and g < 150 and b < 80:
                    browns.append(color)
            except Exception:
                # Skip this color if there's an error
                continue
        
        # Build summary
        summary = {
            'bee_related_terms_count': len(bee_labels),
            'bee_objects_detected_count': len(bee_objects),
            'honey_colors_detected': len(yellows) > 0,
            'brood_colors_detected': len(browns) > 0,
            'top_bee_terms': [label['description'] for label in bee_labels[:3]],
            'suggested_hive_state': self._suggest_hive_state(bee_labels, bee_objects, colors)
        }
        
        return summary
    
    
    def _suggest_hive_state(self, bee_labels, bee_objects, colors):
        """Suggest a hive state based on the analysis."""
        # This is a simplified implementation - would need refinement with real data
        bee_scores = [label['score'] for label in bee_labels]
        avg_bee_score = sum(bee_scores) / len(bee_scores) if bee_scores else 0
        
        if avg_bee_score > 0.9 and len(bee_objects) > 2:
            return "Active"
        elif avg_bee_score > 0.7:
            return "Moderate Activity"
        elif avg_bee_score > 0.5:
            return "Low Activity"
        else:
            return "Unknown"
        