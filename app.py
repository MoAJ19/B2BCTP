import streamlit as st
import os
import json
import io
from docx import Document
from PyPDF2 import PdfReader
import openai
from dotenv import load_dotenv
from typing import Optional, Dict, Any
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize OpenAI client
openai.api_key = os.getenv("OPENAI_API_KEY")

# Set page config
st.set_page_config(
    page_title="Contract Platform",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        margin: 1rem 0;
    }
    .stExpander {
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

class ContractPlatform:
    def __init__(self):
        # Initialize session state
        if 'step' not in st.session_state:
            st.session_state.step = 'home'
        if 'contract_data' not in st.session_state:
            st.session_state.contract_data = {}
        if 'processing_status' not in st.session_state:
            st.session_state.processing_status = None

    @staticmethod
    def extract_text_from_pdf(file_contents: bytes) -> str:
        """Extract text from PDF file."""
        try:
            pdf = PdfReader(io.BytesIO(file_contents))
            text = ""
            for page in pdf.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            logger.error(f"Error extracting PDF text: {str(e)}")
            raise Exception("Failed to process PDF file. Please ensure the file is not corrupted.")

    @staticmethod
    def extract_text_from_docx(file_contents: bytes) -> str:
        """Extract text from DOCX file."""
        try:
            doc = Document(io.BytesIO(file_contents))
            return "\n".join([para.text for para in doc.paragraphs])
        except Exception as e:
            logger.error(f"Error extracting DOCX text: {str(e)}")
            raise Exception("Failed to process DOCX file. Please ensure the file is not corrupted.")

    def process_uploaded_file(self, uploaded_file) -> Optional[str]:
        """Process uploaded file and extract text."""
        try:
            file_contents = uploaded_file.read()
            file_type = uploaded_file.type

            if file_type == 'application/pdf':
                return self.extract_text_from_pdf(file_contents)
            elif file_type in ['application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
                return self.extract_text_from_docx(file_contents)
            elif file_type == 'text/plain':
                return file_contents.decode('utf-8')
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
            return None

    def home(self):
        """Render home page."""
        st.title("Contract Platform")
        st.write("Welcome to the Contract Platform. Choose an option to get started.")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📄 Upload Documents", key="upload_btn"):
                st.session_state.step = 'upload'
        with col2:
            if st.button("📝 Fill Out Application", key="form_btn"):
                st.session_state.step = 'form'

    def upload_documents(self):
        """Handle document upload."""
        st.header("Upload Documents")
        
        # Add back button
        if st.button("← Back to Home", key="back_upload"):
            st.session_state.step = 'home'
            st.rerun()

        uploaded_file = st.file_uploader(
            "Choose a file (PDF, DOCX, or TXT)",
            type=['pdf', 'doc', 'docx', 'txt'],
            help="Upload your contract document for processing"
        )
        
        if uploaded_file:
            with st.spinner("Processing document..."):
                extracted_text = self.process_uploaded_file(uploaded_file)
                
                if extracted_text:
                    st.session_state.contract_data['extracted_text'] = extracted_text
                    st.success("File processed successfully!")
                    
                    # Show preview of extracted text
                    with st.expander("Preview Extracted Text"):
                        st.text_area(
                            "Extracted Content",
                            value=extracted_text[:1000] + "..." if len(extracted_text) > 1000 else extracted_text,
                            height=200,
                            disabled=True
                        )
                    
                    if st.button("Continue to Application Form"):
                        st.session_state.step = 'form'
                        st.rerun()

    def application_form(self):
        """Render application form."""
        st.header("Contract Application Form")
        
        # Add back button
        if st.button("← Back to Home", key="back_form"):
            st.session_state.step = 'home'
            st.rerun()

        # Form validation
        form_valid = True
        required_fields = {
            'party1': "Party 1 Name",
            'party2': "Party 2 Name",
            'commodity': "Commodity Description",
            'quantity': "Quantity",
            'price': "Price per unit"
        }

        with st.form("contract_form"):
            st.subheader("1. Parties Involved")
            col1, col2 = st.columns(2)
            with col1:
                party1 = st.text_input(
                    "Party 1 Name *",
                    value=st.session_state.contract_data.get('party1', ''),
                    key="party1"
                )
            with col2:
                party2 = st.text_input(
                    "Party 2 Name *",
                    value=st.session_state.contract_data.get('party2', ''),
                    key="party2"
                )

            st.subheader("2. Contract Details")
            commodity = st.text_area(
                "Commodity Description *",
                value=st.session_state.contract_data.get('commodity', ''),
                key="commodity"
            )
            
            col3, col4 = st.columns(2)
            with col3:
                quantity = st.number_input(
                    "Quantity *",
                    min_value=0,
                    value=st.session_state.contract_data.get('quantity', 0),
                    key="quantity"
                )
            with col4:
                price = st.number_input(
                    "Price per unit *",
                    min_value=0.0,
                    value=st.session_state.contract_data.get('price', 0.0),
                    key="price"
                )

            st.subheader("3. Additional Terms")
            currency = st.selectbox(
                "Currency",
                options=["USD", "EUR", "GBP"],
                index=0,
                key="currency"
            )
            
            template = st.selectbox(
                "Contract Template",
                options=["London", "Chicago", "Dubai"],
                index=0,
                key="template"
            )

            submitted = st.form_submit_button("Generate Contract")
            
            if submitted:
                # Update session state
                form_data = {
                    'party1': party1,
                    'party2': party2,
                    'commodity': commodity,
                    'quantity': quantity,
                    'price': price,
                    'currency': currency,
                    'template': template
                }
                
                # Validate required fields
                missing_fields = [field for field, value in form_data.items() 
                                if field in required_fields and not value]
                
                if missing_fields:
                    st.error("Please fill in all required fields: " + 
                            ", ".join(required_fields[field] for field in missing_fields))
                    form_valid = False
                
                if form_valid:
                    st.session_state.contract_data.update(form_data)
                    st.session_state.step = 'generate'
                    st.rerun()

    def generate_contract(self):
        """Generate contract using OpenAI API."""
        st.header("Generate Contract")
        
        # Add back button
        if st.button("← Back to Form", key="back_generate"):
            st.session_state.step = 'form'
            st.rerun()

        try:
            with st.spinner("Generating contract..."):
                # Prepare the prompt
                prompt = f"""
                Generate a legal contract based on the following information:
                
                PARTIES:
                - Party 1: {st.session_state.contract_data.get('party1')}
                - Party 2: {st.session_state.contract_data.get('party2')}
                
                TERMS:
                - Commodity: {st.session_state.contract_data.get('commodity')}
                - Quantity: {st.session_state.contract_data.get('quantity')}
                - Price: {st.session_state.contract_data.get('price')} {st.session_state.contract_data.get('currency')} per unit
                - Template Style: {st.session_state.contract_data.get('template')}
                
                Please generate a complete, professionally formatted, and legally binding contract.
                Include standard clauses for dispute resolution, termination, and force majeure.
                """

                # Make API call
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a legal document generator specializing in commercial contracts."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=2000,
                    temperature=0.7
                )
                
                contract_text = response.choices[0].message.content.strip()
                
                # Display generated contract
                st.markdown("### Generated Contract")
                st.text_area(
                    "Contract Content",
                    value=contract_text,
                    height=400,
                    disabled=True
                )
                
                # Add download options
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        "📥 Download as TXT",
                        data=contract_text,
                        file_name=f"contract_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain"
                    )
                with col2:
                    # Generate PDF version (placeholder - implement PDF generation as needed)
                    st.button("📥 Download as PDF (Coming Soon)", disabled=True)

        except Exception as e:
            logger.error(f"Error generating contract: {str(e)}")
            st.error("An error occurred while generating the contract. Please try again or contact support.")

def main():
    """Main application entry point."""
    platform = ContractPlatform()
    
    # Display navigation breadcrumb
    steps = {
        'home': '🏠 Home',
        'upload': '📄 Upload',
        'form': '📝 Form',
        'generate': '⚙️ Generate'
    }
    st.sidebar.markdown("### Navigation")
    st.sidebar.text(f"Current Step: {steps[st.session_state.step]}")
    
    # Route to appropriate page
    if st.session_state.step == 'home':
        platform.home()
    elif st.session_state.step == 'upload':
        platform.upload_documents()
    elif st.session_state.step == 'form':
        platform.application_form()
    elif st.session_state.step == 'generate':
        platform.generate_contract()

if __name__ == "__main__":
    main()
