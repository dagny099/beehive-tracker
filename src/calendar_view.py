# src/calendar_view.py
import streamlit as st
from streamlit_calendar import calendar
import pandas as pd
from datetime import datetime

# Color assignment function
def assign_color(photo_count):
    if photo_count > 5:
        return "#1f77b4"  # Blue - many photos
    elif photo_count >= 2:
        return "#ff7f0e"  # Orange - medium photos
    else:
        return "#888888"  # Default gray - few photos


def main():
    """Render the calendar view for beehive inspections"""
    st.markdown("## 📆 Calendar View - Beehive Inspections")
    
    # Initialize session state if needed
    from src.timeline_component import initialize_session_state
    initialize_session_state()
    
    mode = st.selectbox(
        "Calendar Mode:",
        (
            "daygrid",
            "resource-timegrid",
            "list"
        ),
    )

    # Create events from session state inspections
    events = []
    resources = []
    
    if 'inspections' in st.session_state and st.session_state.inspections:
        # Sort inspections by date
        sorted_inspections = sorted(
            enumerate(st.session_state.inspections), 
            key=lambda x: x[1]['date'] if isinstance(x[1]['date'], datetime) else datetime.strptime(x[1]['date'], "%Y:%m:%d %H:%M:%S")
        )
        
        # Generate events and resources for calendar
        for idx, (i, inspection) in enumerate(sorted_inspections):
            # Create resource ID (A, B, C, etc.)
            resource_id = chr(65 + idx % 26) # A, B, C, ...
            
            # Get date as datetime object
            if isinstance(inspection['date'], datetime):
                date_obj = inspection['date']
            else:
                try:
                    date_obj = datetime.strptime(inspection['date'], "%Y:%m:%d %H:%M:%S")
                except:
                    # Try to parse with a fallback format
                    try:
                        date_obj = datetime.strptime(inspection['date'], "%Y-%m-%d")
                    except:
                        # Skip this inspection if date can't be parsed
                        continue
            
            # Format date for calendar
            date_str = date_obj.strftime("%Y-%m-%d")
            
            # Create event title
            title = f"Inspection {resource_id}: {inspection.get('photo_count', 0)} photos"
            
            # Assign color based on photo count or other criteria
            color = assign_color(inspection.get('photo_count', 0))
            
            # Add event
            events.append({
                "title": title,
                "start": date_str,
                "end": date_str,
                "resourceId": resource_id,
                "color": color,
                "inspection_index": i  # Store the actual inspection index for reference
            })
            
            # Add resource
            resources.append({
                "id": resource_id,
                "title": f"Inspection {resource_id}",
                "color": color
            })

    # Configure calendar options
    calendar_options = {
        "editable": False,
        "navLinks": True,
        "initialView": "dayGridMonth",
    }

    if mode == "daygrid":
        calendar_options = {
            **calendar_options,
            "headerToolbar": {
                "left": "today prev,next",
                "center": "title",
                "right": "dayGridDay,dayGridWeek,dayGridMonth",
            },
            "initialView": "dayGridMonth",
        }
    elif mode == "resource-timegrid":
        calendar_options = {
            **calendar_options,
            "headerToolbar": {
                "left": "today prev,next",
                "center": "title",
                "right": "resourceTimelineDay,resourceTimelineWeek,resourceTimelineMonth",
            },
            "initialView": "resourceTimelineDay",
            "resourceGroupField": "color",
            "resources": resources
        }
    elif mode == "list":
        calendar_options = {
            **calendar_options,
            "initialView": "listMonth",
        }

    # Render the calendar
    response = calendar(
        events=events,
        options=calendar_options,
        custom_css= """
            .fc .fc-daygrid-event {
                background-color: var(--event-color, #1f77b4);
                color: white;
                border: none;
            }
            .fc-event {
                cursor: pointer;
            }
        """,
        callbacks=["eventClick", "dateClick"],
        key=mode,
    )
    
    # Handle calendar interactions
    if response and response.get("eventClick"):
        event_data = response.get("eventClick")
        event_info = event_data.get("event", {}).get("extendedProps", {})
        
        # Extract the real inspection index if available
        if event_info and "inspection_index" in event_info:
            inspection_idx = event_info["inspection_index"]
            st.session_state.selected_inspection = inspection_idx
            
            # Show quick preview and navigation options
            inspection = st.session_state.inspections[inspection_idx]
            
            # Display a preview card
            st.success(f"Selected: Inspection on {inspection['date']}")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Photos", inspection.get('photo_count', 0))
            with col2:
                st.metric("Date", inspection['date'].strftime("%b %d, %Y") if isinstance(inspection['date'], datetime) else inspection['date'])
            
            # Navigate to gallery
            if st.button("📸 View in Gallery"):
                st.session_state.page = "gallery"
                st.rerun()
    
    # Display events below the calendar
    st.markdown("### 📋 Events in View")
    if events:
        for event in events:
            date_str = event['start']
            title = event['title']
            inspection_idx = event.get('inspection_index')
            
            # Create a clickable row for each event
            if st.button(f"{date_str} — {title}", key=f"event_{date_str}_{inspection_idx}"):
                st.session_state.selected_inspection = inspection_idx
                
                # Show navigation option
                if st.button("📸 View in Gallery", key=f"view_gallery_{inspection_idx}"):
                    st.session_state.page = "gallery"
                    st.rerun()
    else:
        st.info("No inspections to display. Start by uploading hive photos.")

if __name__ == "__main__":
    main()