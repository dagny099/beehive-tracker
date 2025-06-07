#!/usr/bin/env python3
"""
Beehive Photo Analyzer - Streamlit Demo App
A "Try It Yourself" demo for the beehive data story blog post

Usage: streamlit run beehive_analyzer_app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import plotly.graph_objects as go
import plotly.express as px
from google.cloud import vision
import io
import base64
from datetime import datetime
import json
import time
import os
from pathlib import Path

# Configure page
st.set_page_config(
    page_title="🐝 Beehive Photo Analyzer", 
    page_icon="🐝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #FFD700, #FFA500);
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    .analysis-container {
        border: 2px solid #e1e5e9;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        background-color: #f8f9fa;
    }
    
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #FFD700;
        margin: 0.5rem 0;
    }
    
    .confidence-high { color: #28a745; font-weight: bold; }
    .confidence-medium { color: #ffc107; font-weight: bold; }
    .confidence-low { color: #dc3545; font-weight: bold; }
    
    .sample-images {
        display: flex;
        justify-content: space-around;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None
if 'current_image' not in st.session_state:
    st.session_state.current_image = None

class BeehiveVisionAnalyzer:
    """Simplified version of the BeehiveVisionExplorer for Streamlit"""
    
    def __init__(self):
        """Initialize Vision API client"""
        try:
            self.client = vision.ImageAnnotatorClient()
            self.api_available = True
        except Exception as e:
            st.error(f"⚠️ Google Cloud Vision API not configured: {e}")
            st.info("💡 To use live analysis, set up your GOOGLE_APPLICATION_CREDENTIALS environment variable")
            self.api_available = False
            self.client = None
    
    def analyze_image(self, image_bytes):
        """Run comprehensive Vision API analysis on uploaded image"""
        if not self.api_available:
            return self._generate_mock_results()
        
        try:
            vision_image = vision.Image(content=image_bytes)
            
            # Run all analysis types
            results = {
                'objects': self._detect_objects(vision_image),
                'labels': self._detect_labels(vision_image),
                'colors': self._analyze_colors(vision_image),
                'text': self._detect_text(vision_image),
                'web': self._detect_web_entities(vision_image)
            }
            
            # Add beekeeping insights
            results['beekeeping_insights'] = self._analyze_beekeeping_insights(results)
            
            return results
            
        except Exception as e:
            st.error(f"API Error: {e}")
            return self._generate_mock_results()
    
    def _detect_objects(self, image):
        """Object detection"""
        try:
            response = self.client.object_localization(image=image)
            return [{
                'name': obj.name,
                'confidence': obj.score,
                'bounding_box': [(vertex.x, vertex.y) for vertex in obj.bounding_poly.normalized_vertices]
            } for obj in response.localized_object_annotations]
        except:
            return []
    
    def _detect_labels(self, image):
        """Label detection"""
        try:
            response = self.client.label_detection(image=image)
            return [{
                'description': label.description,
                'confidence': label.score,
                'topicality': label.topicality
            } for label in response.label_annotations[:15]]
        except:
            return []
    
    def _analyze_colors(self, image):
        """Color analysis"""
        try:
            response = self.client.image_properties(image=image)
            return [{
                'color': {
                    'red': color.color.red,
                    'green': color.color.green,
                    'blue': color.color.blue
                },
                'score': color.score,
                'pixel_fraction': color.pixel_fraction
            } for color in response.image_properties_annotation.dominant_colors_annotation.colors]
        except:
            return []
    
    def _detect_text(self, image):
        """Text detection"""
        try:
            response = self.client.text_detection(image=image)
            return [text.description for text in response.text_annotations]
        except:
            return []
    
    def _detect_web_entities(self, image):
        """Web entity detection"""
        try:
            response = self.client.web_detection(image=image)
            return [{
                'description': entity.description,
                'score': entity.score
            } for entity in response.web_detection.web_entities[:10]]
        except:
            return []
    
    def _analyze_beekeeping_insights(self, results):
        """Convert Vision API results to beekeeping insights"""
        insights = {
            'bee_related_confidence': 0,
            'honey_area_estimate': 0,
            'brood_area_estimate': 0,
            'wax_area_estimate': 0,
            'overall_hive_health_score': 0
        }
        
        # Calculate bee-related confidence
        bee_keywords = ['bee', 'honeybee', 'insect', 'hive', 'honey']
        bee_labels = [label for label in results['labels'] 
                     if any(keyword in label['description'].lower() for keyword in bee_keywords)]
        
        if bee_labels:
            insights['bee_related_confidence'] = sum(label['confidence'] for label in bee_labels) / len(bee_labels)
        
        # Analyze colors for hive components
        colors = results['colors']
        for color in colors:
            r, g, b = color['color']['red'], color['color']['green'], color['color']['blue']
            fraction = color['pixel_fraction']
            
            # Honey detection (yellow/amber)
            if r > 200 and g > 150 and b < 100:
                insights['honey_area_estimate'] += fraction
            
            # Brood detection (white/pale)
            elif r > 200 and g > 200 and b > 200:
                insights['brood_area_estimate'] += fraction
            
            # Wax detection (light yellow)
            elif r > 230 and g > 200 and b < 150:
                insights['wax_area_estimate'] += fraction
        
        # Calculate overall health score (0-100)
        health_components = [
            insights['bee_related_confidence'],
            min(insights['honey_area_estimate'] * 2, 1.0),  # Scale up
            min(insights['brood_area_estimate'] * 3, 1.0),  # Scale up
        ]
        insights['overall_hive_health_score'] = sum(health_components) / len(health_components) * 100
        
        return insights
    
    def _generate_mock_results(self):
        """Generate mock results when API is not available"""
        return {
            'objects': [
                {'name': 'Insect', 'confidence': 0.87, 'bounding_box': [(0.2, 0.3), (0.8, 0.7)]},
            ],
            'labels': [
                {'description': 'Honeybee', 'confidence': 0.94, 'topicality': 0.89},
                {'description': 'Insect', 'confidence': 0.87, 'topicality': 0.82},
                {'description': 'Food', 'confidence': 0.73, 'topicality': 0.65},
                {'description': 'Pattern', 'confidence': 0.45, 'topicality': 0.38},
            ],
            'colors': [
                {'color': {'red': 240, 'green': 200, 'blue': 100}, 'score': 0.35, 'pixel_fraction': 0.25},
                {'color': {'red': 220, 'green': 220, 'blue': 220}, 'score': 0.28, 'pixel_fraction': 0.20},
                {'color': {'red': 180, 'green': 140, 'blue': 80}, 'score': 0.22, 'pixel_fraction': 0.15},
            ],
            'text': [],
            'web': [
                {'description': 'Honeybee', 'score': 0.82},
                {'description': 'Beehive', 'score': 0.76},
            ],
            'beekeeping_insights': {
                'bee_related_confidence': 0.85,
                'honey_area_estimate': 0.25,
                'brood_area_estimate': 0.20,
                'wax_area_estimate': 0.15,
                'overall_hive_health_score': 77
            }
        }

def format_confidence(confidence):
    """Format confidence score with color coding"""
    if confidence >= 0.8:
        return f'<span class="confidence-high">{confidence:.2f} (High)</span>'
    elif confidence >= 0.5:
        return f'<span class="confidence-medium">{confidence:.2f} (Medium)</span>'
    else:
        return f'<span class="confidence-low">{confidence:.2f} (Low)</span>'

def create_analysis_visualization(results, image):
    """Create visualizations of analysis results"""
    
    # 1. Confidence scores chart
    labels_data = results['labels'][:8]  # Top 8 labels
    if labels_data:
        fig_labels = px.bar(
            x=[label['confidence'] for label in labels_data],
            y=[label['description'] for label in labels_data],
            orientation='h',
            title="🏷️ Top Detection Labels",
            labels={'x': 'Confidence Score', 'y': 'Label'},
            color=[label['confidence'] for label in labels_data],
            color_continuous_scale='Viridis'
        )
        fig_labels.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_labels, use_container_width=True)
    
    # 2. Color analysis
    colors_data = results['colors'][:6]  # Top 6 colors
    if colors_data:
        color_rgb = [f"rgb({c['color']['red']}, {c['color']['green']}, {c['color']['blue']})" for c in colors_data]
        fig_colors = go.Figure(data=[
            go.Bar(
                x=[f"Color {i+1}" for i in range(len(colors_data))],
                y=[c['pixel_fraction'] for c in colors_data],
                marker_color=color_rgb,
                text=[f"{c['pixel_fraction']:.2f}" for c in colors_data],
                textposition='auto'
            )
        ])
        fig_colors.update_layout(
            title="🎨 Dominant Colors Analysis",
            xaxis_title="Color",
            yaxis_title="Pixel Fraction",
            height=400
        )
        st.plotly_chart(fig_colors, use_container_width=True)
    
    # 3. Beekeeping insights radar chart
    insights = results['beekeeping_insights']
    categories = ['Bee Confidence', 'Honey Area', 'Brood Area', 'Wax Area']
    values = [
        insights['bee_related_confidence'],
        insights['honey_area_estimate'],
        insights['brood_area_estimate'],
        insights['wax_area_estimate']
    ]
    
    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        name='Hive Analysis',
        line_color='orange'
    ))
    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 1])
        ),
        title="🐝 Beekeeping Insights Radar",
        height=400
    )
    st.plotly_chart(fig_radar, use_container_width=True)

def display_sample_images():
    """Display sample images users can try"""
    st.markdown("### 🖼️ Try These Sample Images")
    st.markdown("Click on any sample image to analyze it:")
    
    # # Create sample image data (all images in /assets folder)
    sample_images = [
        {
            "name": "Visible Pollen",
            "description": "Frame with bees and visible pollen",
            "url": "assets/bees_pollen_visible.jpg",
            "analysis_preview": "High bee activity, visible honey caps"
        },
        {
            "name": "Healthy Brood Pattern",
            "description": "Healthy brood development pattern", 
            "url": "assets/capped_brood_top_bar.jpg",
            "analysis_preview": "Geometric patterns, brood cells"
        },
        {
            "name": "New Comb",
            "description": "Fresh wax comb structure", 
            "url": "assets/comb_new.jpg",
            "analysis_preview": "Hexagonal patterns, wax detection"
        },
        {
            "name": "Queen on Frame", 
            "description": "Queen bee surrounded by workers",
            "url": "assets/comb_queen_bee.jpg",
            "analysis_preview": "Queen detection, worker bee cluster"
        },

    ]

    # Create 2 columns
    col1, col2 = st.columns(2)

    # Display images in 2x2 grid
    for i, sample in enumerate(sample_images):
        # Alternate between columns
        current_col = col1 if i % 2 == 0 else col2
        
        with current_col:
            st.image(sample["url"], caption=sample["name"], use_container_width=True)
            st.markdown(f"*{sample['description']}*")
            if st.button(f"Analyze {sample['name']}", key=f"sample_{i}"):
                st.info(f"Would analyze: {sample['analysis_preview']}")
                
            st.markdown("---")  # Add separator between images in same column
def main():
    """Main Streamlit app"""
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🐝 Beehive Photo Analyzer</h1>
        <p>Discover what AI can see in your beehive photos</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 📋 How It Works")
        st.markdown("""
        1. **Upload** a beehive photo
        2. **Analyze** with Google Vision AI
        3. **Explore** the results and insights
        """)
        
        st.markdown("### 🧪 What Gets Analyzed")
        st.markdown("""
        - **Objects**: Bees, frames, equipment
        - **Labels**: Categories and classifications  
        - **Colors**: Honey, brood, wax detection
        - **Patterns**: Hexagonal comb structures
        - **Health**: Overall hive assessment
        """)
        
        st.markdown("### ℹ️ About")
        st.markdown("""
        This demo accompanies the blog post: 
        **"From Owl Box to Data Pipeline"**
        
        Built with Streamlit and Google Cloud Vision API.
        """)
    
    # Main content area
    tab1, tab2, tab3 = st.tabs(["📤 Upload & Analyze", "🖼️ Sample Photos", "📊 About the Analysis"])
    
    with tab1:
        st.markdown("### Upload Your Beehive Photo")
        
        uploaded_file = st.file_uploader(
            "Choose a photo to analyze",
            type=['jpg', 'jpeg', 'png', 'bmp'],
            help="Upload any photo - beehive photos work best, but try anything!"
        )
        
        if uploaded_file is not None:
            # Display uploaded image
            image = Image.open(uploaded_file)
            st.session_state.current_image = image
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.image(image, caption="Uploaded Image", use_container_width=True)
            
            with col2:
                if st.button("🔍 Analyze with AI", type="primary"):
                    with st.spinner("🤖 Running AI analysis..."):
                        # Simulate processing time
                        time.sleep(2)
                        
                        # Convert image to bytes
                        img_bytes = io.BytesIO()
                        image.save(img_bytes, format='JPEG')
                        img_bytes = img_bytes.getvalue()
                        
                        # Initialize analyzer and run analysis
                        analyzer = BeehiveVisionAnalyzer()
                        results = analyzer.analyze_image(img_bytes)
                        st.session_state.analysis_results = results
                        
                        st.success("✅ Analysis complete!")
            
            # Display results if available
            if st.session_state.analysis_results:
                st.markdown("---")
                st.markdown("## 🎯 Analysis Results")
                
                results = st.session_state.analysis_results
                insights = results['beekeeping_insights']
                
                # Key metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
                        "🐝 Bee Confidence", 
                        f"{insights['bee_related_confidence']:.2f}",
                        help="How confident the AI is that this contains bees"
                    )
                
                with col2:
                    st.metric(
                        "🍯 Honey Area", 
                        f"{insights['honey_area_estimate']:.2f}",
                        help="Estimated fraction of image showing honey"
                    )
                
                with col3:
                    st.metric(
                        "👶 Brood Area", 
                        f"{insights['brood_area_estimate']:.2f}",
                        help="Estimated fraction showing brood cells"
                    )
                
                with col4:
                    health_score = insights['overall_hive_health_score']
                    st.metric(
                        "💚 Health Score", 
                        f"{health_score:.0f}/100",
                        help="Overall hive health assessment"
                    )
                
                # Detailed analysis tabs
                detail_tab1, detail_tab2, detail_tab3 = st.tabs(["🏷️ Labels", "🎨 Colors", "📈 Visualizations"])
                
                with detail_tab1:
                    st.markdown("#### Top Detection Labels")
                    labels_df = pd.DataFrame(results['labels'][:10])
                    if not labels_df.empty:
                        for _, label in labels_df.iterrows():
                            conf_html = format_confidence(label['confidence'])
                            st.markdown(f"**{label['description']}**: {conf_html}", unsafe_allow_html=True)
                    else:
                        st.info("No labels detected")
                
                with detail_tab2:
                    st.markdown("#### Dominant Colors")
                    colors = results['colors'][:5]
                    if colors:
                        for i, color in enumerate(colors):
                            rgb = color['color']
                            col_a, col_b = st.columns([1, 3])
                            with col_a:
                                # Color swatch
                                st.markdown(f"""
                                <div style="width: 50px; height: 30px; background-color: rgb({rgb['red']}, {rgb['green']}, {rgb['blue']}); 
                                           border: 1px solid #ccc; border-radius: 4px;"></div>
                                """, unsafe_allow_html=True)
                            with col_b:
                                st.markdown(f"**RGB({rgb['red']}, {rgb['green']}, {rgb['blue']})** - {color['pixel_fraction']:.1%} of image")
                    else:
                        st.info("No color data available")
                
                with detail_tab3:
                    create_analysis_visualization(results, image)
    
    with tab2:
        display_sample_images()
    
    with tab3:
        st.markdown("### 🧠 How the Analysis Works")
        
        st.markdown("""
        This demo uses **Google Cloud Vision API** to analyze your photos through multiple AI models:
        
        #### 🔍 Analysis Types
        
        **Object Detection**: Identifies and locates specific objects (bees, frames, equipment) with bounding boxes
        
        **Label Classification**: Assigns category labels like "Honeybee", "Insect", "Food" with confidence scores
        
        **Color Analysis**: Extracts dominant colors and their pixel distributions
        
        **Text Recognition**: Finds any readable text in the image
        
        **Pattern Detection**: Identifies geometric structures and textures
        
        #### 🐝 Beekeeping Intelligence Layer
        
        Raw AI results get translated into beekeeping insights:
        
        - **Honey Detection**: Yellow/amber colors → honey estimates
        - **Brood Detection**: White/pale regions → brood cell areas  
        - **Wax Analysis**: Light yellow areas → fresh comb detection
        - **Health Scoring**: Composite metric based on multiple factors
        
        #### 📊 Confidence Interpretation
        
        - **High (0.8+)**: Very reliable detection
        - **Medium (0.5-0.8)**: Reasonable confidence, worth investigating
        - **Low (<0.5)**: Uncertain, may be false positive
        """)
        
        st.markdown("### 🔗 Learn More")
        st.markdown("""
        - Read the full blog post: [From Owl Box to Data Pipeline](#)
        - View the code on GitHub: [Beehive Analysis Repository](#) 
        - COMING SOON: An interactive timeline of beekeeping data stories
        """)

if __name__ == "__main__":
    main()
