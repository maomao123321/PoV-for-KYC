"""
Streamlit UI for Fireworks AI KYC PoV System
Clean, ChatGPT-inspired interface for document verification
"""
import asyncio
import json
from datetime import date
from io import BytesIO
from pathlib import Path

import streamlit as st
from PIL import Image

from src.config import Settings
from src.exceptions import TechnicalRejectError
from src.main import KYCPipeline

# Page config
st.set_page_config(
    page_title="KYC Document Verification",
    page_icon="🔐",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Custom CSS for ChatGPT-like styling
st.markdown(
    """
<style>
    .main {
        max-width: 800px;
        padding: 2rem 1rem;
    }
    .stAlert {
        border-radius: 0.5rem;
        border: none;
    }
    .upload-section {
        padding: 1rem 0;
        margin: 1rem 0;
    }
    /* Hide default file uploader dashed border */
    [data-testid="stFileUploader"] > div {
        border: none !important;
        padding: 0 !important;
    }
    [data-testid="stFileUploader"] section {
        border: none !important;
        background: transparent !important;
    }
    .result-card {
        background: #f8f9fa;
        border-radius: 1rem;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    .metric-row {
        display: flex;
        gap: 1rem;
        margin: 1rem 0;
    }
    .field-label {
        color: #666;
        font-size: 0.875rem;
        font-weight: 500;
        margin-bottom: 0.25rem;
    }
    .field-value {
        color: #1a1a1a;
        font-size: 1rem;
        font-weight: 400;
    }
    h1 {
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        color: #666;
        font-size: 1rem;
        margin-bottom: 2rem;
    }
</style>
""",
    unsafe_allow_html=True,
)


def render_status_badge(status: str, score: float) -> None:
    """Render status with appropriate styling"""
    status_info = {
        "SUCCESS": {"icon": "🟢", "label": "SUCCESS - Automatic Approval", "color": "#10a37f"},
        "MANUAL_REVIEW": {"icon": "🟡", "label": "MANUAL REVIEW - Human Verification Needed", "color": "#f59e0b"},
        "RETRY_UPLOAD": {"icon": "🔴", "label": "RETRY UPLOAD - Please Retake Photo", "color": "#ef4444"},
        "SYSTEM_ERROR": {"icon": "⚫", "label": "SYSTEM ERROR - Processing Failed", "color": "#6b7280"},
    }
    
    info = status_info.get(status, {"icon": "⚪", "label": status, "color": "#999"})
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, {info['color']}22 0%, {info['color']}11 100%); 
                border-left: 4px solid {info['color']}; 
                padding: 1.5rem; 
                border-radius: 0.5rem; 
                margin: 1rem 0;">
        <h2 style="margin: 0; color: {info['color']};">{info['icon']} {info['label']}</h2>
        <p style="margin: 0.5rem 0 0 0; font-size: 1.5rem; color: #1a1a1a;">
            Overall Confidence: <strong>{score:.1%}</strong>
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_document_fields(doc_data: dict, doc_type: str) -> None:
    """Render extracted document fields in a clean grid"""
    if not doc_data:
        st.warning("No document data extracted")
        return
    
    st.markdown("#### 📄 Extracted Information")
    
    # Key fields mapping
    field_labels = {
        "full_name": "Full Name",
        "birth_date": "Date of Birth",
        "document_number": "Document Number",
        "issue_date": "Issue Date",
        "expiry_date": "Expiry Date",
        "nationality": "Nationality",
        "license_class": "License Class",
        "address": "Address",
    }
    
    # Render in two columns
    col1, col2 = st.columns(2)
    
    for idx, (key, label) in enumerate(field_labels.items()):
        if key in doc_data and doc_data[key]:
            value = doc_data[key]
            # Format dates nicely
            if isinstance(value, (date, str)) and "date" in key.lower():
                try:
                    if isinstance(value, str):
                        value = date.fromisoformat(value)
                    value = value.strftime("%B %d, %Y")
                except:
                    pass
            
            with col1 if idx % 2 == 0 else col2:
                st.markdown(f'<div class="field-label">{label}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="field-value">{value}</div>', unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)


def render_issues(issues: list, flagged_fields: list) -> None:
    """Render validation issues if any"""
    if not issues and not flagged_fields:
        st.success("✅ All validation checks passed")
        return
    
    if issues:
        st.warning("⚠️ **Issues Detected**")
        for issue in issues:
            st.markdown(f"- {issue}")
    
    if flagged_fields:
        st.info(f"🏁 **Flagged Fields**: {', '.join(flagged_fields)}")


def render_metrics(result: dict) -> None:
    """Render confidence metrics"""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        ai_conf = result.get("payload", {}).get("ai_confidence", 0)
        st.metric("AI Confidence", f"{ai_conf:.1%}")
    
    with col2:
        logic_score = result.get("logic_score", 0)
        st.metric("Logic Score", f"{logic_score:.1%}")
    
    with col3:
        ucs = result.get("score", 0)
        st.metric("Overall (UCS)", f"{ucs:.1%}")


async def process_document(image_bytes: bytes, mime_type: str, api_key: str) -> dict:
    """Process document through KYC pipeline"""
    pipeline = KYCPipeline(api_key=api_key)
    result = await pipeline.run(image_bytes, mime_type=mime_type)
    return {
        "status": result.status,
        "score": result.score,
        "logic_score": result.logic_score,
        "phash": result.phash,
        "issues": result.issues,
        "flagged_fields": result.flagged_fields,
        "payload": result.payload,
    }


def main():
    # Header
    st.markdown("# 🔐 KYC Document Verification")
    st.markdown(
        '<p class="subtitle">Powered by Fireworks AI • Secure • Privacy-First</p>',
        unsafe_allow_html=True,
    )
    
    # Status legend
    with st.expander("📋 Status Guide", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("🟢 **SUCCESS** - Automatic approval")
            st.markdown("🟡 **MANUAL REVIEW** - Human verification needed")
        with col2:
            st.markdown("🔴 **RETRY UPLOAD** - Please retake photo")
            st.markdown("⚫ **SYSTEM ERROR** - Processing failed")
    
    # Load API key
    try:
        settings = Settings.from_env()
        api_key = settings.fireworks_api_key
    except Exception as e:
        st.error(f"⚠️ Configuration Error: {e}")
        st.info("Please ensure `.env` file exists with `FIREWORKS_API_KEY` set.")
        st.stop()
    
    # File upload section
    st.markdown('<div class="upload-section">', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "Upload Passport or Driver's License",
        type=["jpg", "jpeg", "png", "gif", "bmp"],
        help="Supported formats: JPG, PNG, GIF, BMP (max 10MB)",
    )
    st.markdown("</div>", unsafe_allow_html=True)
    
    if uploaded_file is not None:
        # Only process if not already processed
        file_key = f"{uploaded_file.name}_{uploaded_file.size}"
        
        if st.session_state.get("last_processed") != file_key:
            # Display uploaded image and process
            col1, col2 = st.columns([1, 2])
            
            with col1:
                image = Image.open(uploaded_file)
                st.image(image, caption="Uploaded Document", width="stretch")
            
            with col2:
                st.markdown("### Processing...")
                with st.spinner("Analyzing document..."):
                    try:
                        # Get image bytes
                        uploaded_file.seek(0)
                        image_bytes = uploaded_file.read()
                        
                        # Determine MIME type
                        mime_type = f"image/{uploaded_file.type.split('/')[-1]}"
                        
                        # Process
                        result = asyncio.run(process_document(image_bytes, mime_type, api_key))
                        
                        # Store in session state
                        st.session_state["result"] = result
                        st.session_state["last_processed"] = file_key
                        st.rerun()
                        
                    except TechnicalRejectError as e:
                        st.error(f"❌ **Image Quality Issue**\n\n{str(e)}")
                        st.info("💡 Please retake the photo with better lighting and focus.")
                        st.session_state.pop("result", None)
                        st.stop()
                        
                    except Exception as e:
                        st.error(f"❌ **Processing Error**\n\n{str(e)}")
                        st.session_state.pop("result", None)
                        st.stop()
    
    # Display results (independent of upload section)
    if "result" in st.session_state and st.session_state.get("result"):
        st.markdown("---")
        
        result = st.session_state["result"]
        
        # Display uploaded image alongside results
        if uploaded_file:
            col_img, col_res = st.columns([1, 3])
            with col_img:
                st.markdown("#### Uploaded Document")
                try:
                    uploaded_file.seek(0)
                    image = Image.open(uploaded_file)
                    st.image(image, width=200)
                except:
                    pass
            with col_res:
                st.markdown("")  # spacing
        
        # Status and overall confidence
        render_status_badge(result["status"], result["score"])
        
        st.markdown("---")
        
        # Detailed confidence metrics
        st.markdown("#### 📊 Confidence Breakdown")
        render_metrics(result)
        
        st.markdown("---")
        
        # Extracted fields
        payload = result["payload"]
        doc_type = payload.get("document_type", "unknown")
        
        if doc_type == "passport" and payload.get("passport"):
            render_document_fields(payload["passport"], "passport")
        elif doc_type == "drivers_license" and payload.get("drivers_license"):
            render_document_fields(payload["drivers_license"], "drivers_license")
        else:
            st.warning("Could not determine document type")
        
        st.markdown("---")
        
        # Issues
        render_issues(result["issues"], result["flagged_fields"])
        
        # Advanced info (collapsible)
        with st.expander("🔍 Advanced Details"):
            st.markdown(f"**Document Type**: {doc_type}")
            st.markdown(f"**Perceptual Hash**: `{result['phash']}`")
            st.markdown(f"**Missing Fields**: {payload.get('missing_fields', [])}")
            
            if st.checkbox("Show Raw JSON"):
                st.json(result)
        
        # Actions
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Process Another Document", type="primary"):
                st.session_state.clear()
                st.rerun()
        
        with col2:
            # Download result
            json_str = json.dumps(result, indent=2, default=str)
            st.download_button(
                label="📥 Download Result",
                data=json_str,
                file_name=f"kyc_result_{result['phash']}.json",
                mime="application/json",
            )
    
    # Footer
    st.markdown("---")
    st.markdown(
        '<p style="text-align: center; color: #999; font-size: 0.875rem;">'
        "🔒 Zero Data Retention • All processing happens in-memory"
        "</p>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()

