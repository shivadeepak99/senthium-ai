"""
Image Annotator - Add visual overlays to security snapshots

Draw bounding boxes, labels, and metadata on images! 🎨📸
"""

import cv2
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Tuple, Dict
import logging

logger = logging.getLogger(__name__)


class ImageAnnotator:
    """
    Annotate security snapshots with detection results and metadata.
    
    Draws bounding boxes, face labels, confidence scores, and timestamps! 🎨
    """
    
    # Color palette (BGR format for OpenCV)
    COLOR_AUTHORIZED = (0, 255, 0)      # Green for authorized faces
    COLOR_UNAUTHORIZED = (0, 0, 255)    # Red for unauthorized/intruders
    COLOR_UNKNOWN = (0, 165, 255)       # Orange for low-confidence detections
    COLOR_TEXT_BG = (0, 0, 0)           # Black background for text
    COLOR_TEXT_FG = (255, 255, 255)     # White text
    COLOR_WATERMARK = (200, 200, 200)   # Light gray for watermark
    
    # Font settings
    FONT = cv2.FONT_HERSHEY_SIMPLEX
    FONT_SCALE_LARGE = 0.8
    FONT_SCALE_MEDIUM = 0.6
    FONT_SCALE_SMALL = 0.5
    FONT_THICKNESS = 2
    FONT_THICKNESS_THIN = 1
    
    def __init__(self, logo_path: Optional[str] = None):
        """
        Initialize annotator.
        
        Args:
            logo_path: Optional path to logo image to overlay (PNG with transparency)
        """
        self.logo_path = logo_path
        self.logo = None
        
        if logo_path and Path(logo_path).exists():
            try:
                self.logo = cv2.imread(logo_path, cv2.IMREAD_UNCHANGED)
                logger.debug(f"📸 Loaded logo: {logo_path}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to load logo: {e}")
    
    def annotate_frame(
        self,
        frame: np.ndarray,
        face_locations: List[Tuple[int, int, int, int]],
        face_labels: List[Dict],
        alert_type: str = "UNAUTHORIZED",
        include_timestamp: bool = True,
        include_logo: bool = True,
        include_severity_banner: bool = True
    ) -> np.ndarray:
        """
        Annotate a frame with detection results and metadata.
        
        Args:
            frame: Original image (numpy array)
            face_locations: List of face bounding boxes (top, right, bottom, left)
            face_labels: List of dicts with keys: 'name', 'distance', 'is_authorized'
            alert_type: Type of alert ("AUTHORIZED", "UNAUTHORIZED", "MULTIPLE_FACES")
            include_timestamp: Add timestamp watermark to bottom-right
            include_logo: Add logo to top-left (if available)
            include_severity_banner: Add colored banner at top
            
        Returns:
            Annotated frame (numpy array)
        """
        # Create a copy to avoid modifying original
        annotated = frame.copy()
        height, width = annotated.shape[:2]
        
        # Draw severity banner at top
        if include_severity_banner:
            annotated = self._draw_severity_banner(annotated, alert_type)
        
        # Draw bounding boxes and labels for each face
        for location, label in zip(face_locations, face_labels):
            annotated = self._draw_face_box(annotated, location, label)
        
        # Add timestamp watermark
        if include_timestamp:
            annotated = self._draw_timestamp(annotated)
        
        # Add logo
        if include_logo and self.logo is not None:
            annotated = self._overlay_logo(annotated)
        
        return annotated
    
    def _draw_severity_banner(self, frame: np.ndarray, alert_type: str) -> np.ndarray:
        """
        Draw colored banner at top of image based on alert severity.
        
        Args:
            frame: Input frame
            alert_type: "AUTHORIZED", "UNAUTHORIZED", "MULTIPLE_FACES", etc.
            
        Returns:
            Frame with banner overlay
        """
        height, width = frame.shape[:2]
        banner_height = 60
        
        # Determine color and text based on alert type
        if alert_type == "AUTHORIZED":
            color = (34, 139, 34)  # Forest green (BGR)
            text = "✓ AUTHORIZED USER"
            icon = "✓"
        elif alert_type == "UNAUTHORIZED":
            color = (0, 0, 220)  # Red (BGR)
            text = "⚠ INTRUDER DETECTED"
            icon = "⚠"
        elif alert_type == "MULTIPLE_FACES":
            color = (0, 140, 255)  # Orange (BGR)
            text = "⚠ MULTIPLE FACES DETECTED"
            icon = "⚠"
        else:
            color = (100, 100, 100)  # Gray
            text = f"• {alert_type}"
            icon = "•"
        
        # Draw semi-transparent banner
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (width, banner_height), color, -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        # Draw text
        text_size = cv2.getTextSize(text, self.FONT, self.FONT_SCALE_LARGE, self.FONT_THICKNESS)[0]
        text_x = (width - text_size[0]) // 2
        text_y = (banner_height + text_size[1]) // 2
        
        cv2.putText(
            frame,
            text,
            (text_x, text_y),
            self.FONT,
            self.FONT_SCALE_LARGE,
            self.COLOR_TEXT_FG,
            self.FONT_THICKNESS,
            cv2.LINE_AA
        )
        
        return frame
    
    def _draw_face_box(
        self,
        frame: np.ndarray,
        location: Tuple[int, int, int, int],
        label: Dict
    ) -> np.ndarray:
        """
        Draw bounding box and label for a single face.
        
        Args:
            frame: Input frame
            location: (top, right, bottom, left) coordinates
            label: Dict with 'name', 'distance', 'is_authorized'
            
        Returns:
            Frame with face box drawn
        """
        top, right, bottom, left = location
        
        # Determine color based on authorization status
        is_authorized = label.get('is_authorized', False)
        distance = label.get('distance', 0.0)
        name = label.get('name', 'Unknown')
        
        if is_authorized:
            box_color = self.COLOR_AUTHORIZED
            status_text = f"✓ {name}"
        else:
            box_color = self.COLOR_UNAUTHORIZED
            status_text = f"⚠ {name}"
        
        # Draw main bounding box (thick)
        cv2.rectangle(frame, (left, top), (right, bottom), box_color, 3)
        
        # Draw corner accents (extra flair!)
        corner_length = 20
        corner_thickness = 4
        
        # Top-left corner
        cv2.line(frame, (left, top), (left + corner_length, top), box_color, corner_thickness)
        cv2.line(frame, (left, top), (left, top + corner_length), box_color, corner_thickness)
        
        # Top-right corner
        cv2.line(frame, (right, top), (right - corner_length, top), box_color, corner_thickness)
        cv2.line(frame, (right, top), (right, top + corner_length), box_color, corner_thickness)
        
        # Bottom-left corner
        cv2.line(frame, (left, bottom), (left + corner_length, bottom), box_color, corner_thickness)
        cv2.line(frame, (left, bottom), (left, bottom - corner_length), box_color, corner_thickness)
        
        # Bottom-right corner
        cv2.line(frame, (right, bottom), (right - corner_length, bottom), box_color, corner_thickness)
        cv2.line(frame, (right, bottom), (right, bottom - corner_length), box_color, corner_thickness)
        
        # Draw label background (below the face box)
        label_margin = 5
        label_height = 55
        label_y_start = bottom + label_margin
        label_y_end = label_y_start + label_height
        
        cv2.rectangle(
            frame,
            (left, label_y_start),
            (right, label_y_end),
            self.COLOR_TEXT_BG,
            -1
        )
        
        # Draw border around label
        cv2.rectangle(
            frame,
            (left, label_y_start),
            (right, label_y_end),
            box_color,
            2
        )
        
        # Draw status text (name + checkmark/warning)
        status_y = label_y_start + 20
        cv2.putText(
            frame,
            status_text,
            (left + 5, status_y),
            self.FONT,
            self.FONT_SCALE_SMALL,
            self.COLOR_TEXT_FG,
            self.FONT_THICKNESS_THIN,
            cv2.LINE_AA
        )
        
        # Draw distance score
        distance_text = f"Distance: {distance:.2f}"
        distance_y = status_y + 20
        cv2.putText(
            frame,
            distance_text,
            (left + 5, distance_y),
            self.FONT,
            self.FONT_SCALE_SMALL,
            self.COLOR_TEXT_FG,
            self.FONT_THICKNESS_THIN,
            cv2.LINE_AA
        )
        
        # Draw confidence indicator (if distance available)
        if distance > 0:
            # Lower distance = higher confidence
            # Assume threshold ~10.0, so invert scale
            confidence_pct = max(0, min(100, int((1 - min(distance / 15.0, 1.0)) * 100)))
            confidence_text = f"Confidence: {confidence_pct}%"
            confidence_y = distance_y + 20
            
            # Color code confidence
            if confidence_pct >= 80:
                conf_color = self.COLOR_AUTHORIZED
            elif confidence_pct >= 50:
                conf_color = self.COLOR_UNKNOWN
            else:
                conf_color = self.COLOR_UNAUTHORIZED
            
            cv2.putText(
                frame,
                confidence_text,
                (left + 5, confidence_y),
                self.FONT,
                self.FONT_SCALE_SMALL,
                conf_color,
                self.FONT_THICKNESS_THIN,
                cv2.LINE_AA
            )
        
        return frame
    
    def _draw_timestamp(self, frame: np.ndarray) -> np.ndarray:
        """
        Draw timestamp watermark in bottom-right corner.
        
        Args:
            frame: Input frame
            
        Returns:
            Frame with timestamp
        """
        height, width = frame.shape[:2]
        
        # Generate timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Calculate text position (bottom-right with padding)
        text_size = cv2.getTextSize(timestamp, self.FONT, self.FONT_SCALE_SMALL, self.FONT_THICKNESS_THIN)[0]
        padding = 10
        text_x = width - text_size[0] - padding
        text_y = height - padding
        
        # Draw semi-transparent background
        bg_margin = 5
        cv2.rectangle(
            frame,
            (text_x - bg_margin, text_y - text_size[1] - bg_margin),
            (text_x + text_size[0] + bg_margin, text_y + bg_margin),
            (0, 0, 0),
            -1
        )
        
        # Draw timestamp text
        cv2.putText(
            frame,
            timestamp,
            (text_x, text_y),
            self.FONT,
            self.FONT_SCALE_SMALL,
            self.COLOR_WATERMARK,
            self.FONT_THICKNESS_THIN,
            cv2.LINE_AA
        )
        
        return frame
    
    def _overlay_logo(self, frame: np.ndarray) -> np.ndarray:
        """
        Overlay logo in top-left corner (if available).
        
        Args:
            frame: Input frame
            
        Returns:
            Frame with logo overlay
        """
        if self.logo is None:
            return frame
        
        try:
            # Resize logo to reasonable size (max 100x100)
            logo_h, logo_w = self.logo.shape[:2]
            max_size = 80
            
            if logo_h > max_size or logo_w > max_size:
                scale = max_size / max(logo_h, logo_w)
                new_w = int(logo_w * scale)
                new_h = int(logo_h * scale)
                logo_resized = cv2.resize(self.logo, (new_w, new_h))
            else:
                logo_resized = self.logo
            
            # Position in top-left with padding
            padding = 15
            x_offset = padding
            y_offset = 70  # Below severity banner
            
            logo_h, logo_w = logo_resized.shape[:2]
            
            # Overlay logo (handle transparency if PNG has alpha channel)
            if logo_resized.shape[2] == 4:  # Has alpha channel
                # Extract alpha channel
                alpha = logo_resized[:, :, 3] / 255.0
                
                # Overlay each color channel
                for c in range(3):
                    frame[y_offset:y_offset+logo_h, x_offset:x_offset+logo_w, c] = \
                        (alpha * logo_resized[:, :, c] + 
                         (1 - alpha) * frame[y_offset:y_offset+logo_h, x_offset:x_offset+logo_w, c])
            else:
                # No transparency, just paste
                frame[y_offset:y_offset+logo_h, x_offset:x_offset+logo_w] = logo_resized[:, :, :3]
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to overlay logo: {e}")
        
        return frame
    
    def save_annotated(
        self,
        frame: np.ndarray,
        output_path: str,
        quality: int = 95
    ) -> bool:
        """
        Save annotated frame to disk.
        
        Args:
            frame: Annotated frame
            output_path: Where to save (JPEG)
            quality: JPEG quality (0-100)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            cv2.imwrite(output_path, frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
            logger.debug(f"💾 Saved annotated image: {output_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to save annotated image: {e}")
            return False
    
    def create_annotated_snapshot(
        self,
        original_snapshot_path: str,
        face_locations: List[Tuple[int, int, int, int]],
        face_labels: List[Dict],
        alert_type: str = "UNAUTHORIZED"
    ) -> Optional[str]:
        """
        Load an existing snapshot, annotate it, and save as new file.
        
        Args:
            original_snapshot_path: Path to original snapshot
            face_locations: Face bounding boxes
            face_labels: Face label data
            alert_type: Alert severity level
            
        Returns:
            Path to annotated snapshot, or None if failed
        """
        try:
            # Load original
            frame = cv2.imread(original_snapshot_path)
            if frame is None:
                logger.error(f"❌ Failed to load snapshot: {original_snapshot_path}")
                return None
            
            # Annotate
            annotated = self.annotate_frame(frame, face_locations, face_labels, alert_type)
            
            # Generate output path (add "_annotated" suffix)
            original_path = Path(original_snapshot_path)
            output_path = original_path.parent / f"{original_path.stem}_annotated{original_path.suffix}"
            
            # Save
            if self.save_annotated(annotated, str(output_path)):
                return str(output_path)
            else:
                return None
            
        except Exception as e:
            logger.error(f"❌ Failed to create annotated snapshot: {e}")
            return None
