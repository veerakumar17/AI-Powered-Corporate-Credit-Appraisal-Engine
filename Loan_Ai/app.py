"""
AI Credit Decision System - PRODUCTION VERSION
Streamlit application with optimized performance and professional UI
"""
import streamlit as st
import os
from pathlib import Path

# Import modules
from modules.pdf_extractor import extract_text_from_pdf
from modules.text_cleaner import clean_text
from modules.financial_extractor import (
    extract_financial_data, 
    format_indian_currency, 
    format_crores,
    validate_financial_data
)
from modules.ratio_analyzer import calculate_financial_ratios, interpret_ratios, get_ratio_benchmarks
from core.risk_analyzer import analyze_credit_risk, get_risk_emoji, get_decision_emoji
from modules.loan_engine import get_loan_summary, calculate_max_loan_capacity
from modules.research_agent import research_company, get_sentiment_emoji
from core.utils import ensure_directory_exists, save_text_to_file, count_words
from modules.dataframe_utils import safe_numeric_convert

# Page configuration
st.set_page_config(
    page_title="AI Credit Decision System",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .success-box {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #28a745;
    }
    .warning-box {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ffc107;
    }
    .danger-box {
        background-color: #f8d7da;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #dc3545;
    }
</style>
""", unsafe_allow_html=True)

# Caching functions
@st.cache_data(ttl=3600, show_spinner=False)
def cached_research_company(company_name, base_credit_score):
    """Cached research to avoid repeated API calls"""
    return research_company(company_name, base_credit_score)

@st.cache_data(show_spinner=False)
def process_pdf_cached(pdf_file):
    """Cache PDF processing"""
    return extract_text_from_pdf(pdf_file)

def main():
    # Header
    st.markdown('<div class="main-header">💼 AI Credit Decision System</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.header("📋 About")
        st.info("""
        This system extracts and analyzes text from financial PDFs to support credit decision-making.
        
        **Features:**
        - Multi-PDF upload
        - Financial data extraction
        - AI credit risk analysis
        - External intelligence research
        - Loan recommendations
        """)
        
        st.header("🔬 Research Options")
        enable_research = st.checkbox("Enable External Research", value=False)
        company_name = ""
        if enable_research:
            company_name = st.text_input("Company Name", placeholder="e.g., Infosys")
        
        st.header("📊 Statistics")
        if 'stats' in st.session_state:
            stats = st.session_state.stats
            st.metric("Files Processed", stats.get('files', 0))
            st.metric("Total Pages", stats.get('pages', 0))
            st.metric("Total Words", stats.get('words', 0))
    
    # File upload
    st.header("📁 Upload Financial Documents")
    uploaded_files = st.file_uploader(
        "Choose PDF files",
        type=['pdf'],
        accept_multiple_files=True,
        help="Upload one or more financial PDF documents"
    )
    
    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} file(s) uploaded successfully")
        
        # Display uploaded files
        with st.expander("📄 Uploaded Files", expanded=False):
            for file in uploaded_files:
                st.write(f"• {file.name} ({file.size / 1024:.2f} KB)")
        
        # Analyze button
        if st.button("🚀 Analyze Documents", type="primary", use_container_width=True):
            analyze_documents(uploaded_files, enable_research, company_name)
    else:
        st.info("👆 Please upload PDF files to begin analysis")

def analyze_documents(uploaded_files, enable_research, company_name):
    """Main analysis workflow"""
    
    # Initialize progress
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Step 1: Extract text from PDFs
    status_text.text("📄 Extracting text from PDFs...")
    all_text = ""
    total_pages = 0
    
    for idx, file in enumerate(uploaded_files):
        extracted_text = process_pdf_cached(file)
        all_text += extracted_text + "\n\n"
        progress_bar.progress((idx + 1) / (len(uploaded_files) + 4))
    
    # Step 2: Clean text
    status_text.text("🧹 Cleaning extracted text...")
    cleaned_text = clean_text(all_text)
    progress_bar.progress(0.4)
    
    # Step 3: Extract financial data
    status_text.text("💰 Extracting financial metrics...")
    financial_data = extract_financial_data(cleaned_text)
    validation = validate_financial_data(financial_data)
    progress_bar.progress(0.6)
    
    # Step 4: Analyze credit risk
    status_text.text("🎯 Analyzing credit risk...")
    risk_analysis = analyze_credit_risk(financial_data)
    progress_bar.progress(0.8)
    
    # Step 5: External research (if enabled)
    research_data = None
    if enable_research and company_name:
        status_text.text(f"🔍 Researching {company_name}...")
        try:
            research_data = cached_research_company(company_name, risk_analysis['credit_score'])
            # Update credit score with research adjustment
            if research_data.get('adjusted_risk_score'):
                risk_analysis['credit_score'] = research_data['adjusted_risk_score']
        except Exception as e:
            st.warning(f"⚠️ Research failed: {str(e)}")
    
    progress_bar.progress(1.0)
    status_text.text("✅ Analysis complete!")
    
    # Update statistics
    st.session_state.stats = {
        'files': len(uploaded_files),
        'pages': total_pages,
        'words': count_words(cleaned_text)
    }
    
    # Display results
    display_results(financial_data, validation, risk_analysis, research_data, cleaned_text)

def display_results(financial_data, validation, risk_analysis, research_data, cleaned_text):
    """Display analysis results in organized tabs"""
    
    st.markdown("---")
    st.header("📊 Analysis Results")
    
    # Create tabs
    tabs = st.tabs([
        "🎯 Credit Risk Analysis",
        "💰 Financial Dashboard",
        "📈 Financial Ratios",
        "🔍 External Intelligence",
        "📄 Extracted Text"
    ])
    
    # Tab 1: Credit Risk Analysis
    with tabs[0]:
        display_credit_risk_analysis(risk_analysis, validation)
    
    # Tab 2: Financial Dashboard
    with tabs[1]:
        display_financial_dashboard(financial_data, validation)
    
    # Tab 3: Financial Ratios
    with tabs[2]:
        display_financial_ratios(risk_analysis.get('ratios', {}), risk_analysis.get('ratio_interpretations', {}))
    
    # Tab 4: External Intelligence
    with tabs[3]:
        if research_data:
            display_research_intelligence(research_data)
        else:
            st.info("🔍 External research not enabled. Enable it in the sidebar to see company intelligence.")
    
    # Tab 5: Extracted Text
    with tabs[4]:
        display_extracted_text(cleaned_text)

def display_credit_risk_analysis(risk_analysis, validation):
    """Display credit risk analysis results"""
    
    st.subheader("🎯 Credit Risk Assessment")
    
    # Risk Level and Credit Score
    col1, col2, col3 = st.columns(3)
    
    with col1:
        risk_emoji = get_risk_emoji(risk_analysis['risk_level'])
        st.metric(
            "Risk Level",
            f"{risk_emoji} {risk_analysis['risk_level']}",
            help="Overall credit risk assessment"
        )
    
    with col2:
        score = risk_analysis['credit_score']
        score_color = "🟢" if score >= 70 else "🟡" if score >= 50 else "🔴"
        st.metric(
            "Credit Score",
            f"{score_color} {score}/100",
            help="AI-calculated credit score"
        )
    
    with col3:
        st.metric(
            "Data Completeness",
            f"{validation['completeness']:.0f}%",
            help="Percentage of financial metrics found"
        )
    
    st.markdown("---")
    
    # Loan Recommendation
    st.subheader("💳 Loan Recommendation")
    loan_rec = risk_analysis['loan_recommendation']
    decision_emoji = get_decision_emoji(loan_rec['decision'])
    
    # Decision box
    decision_class = "success-box" if loan_rec['decision'] == "APPROVED" else "warning-box" if loan_rec['decision'] == "CONDITIONAL" else "danger-box"
    
    st.markdown(f'<div class="{decision_class}">', unsafe_allow_html=True)
    st.markdown(f"### {decision_emoji} {loan_rec['decision']}")
    st.markdown(loan_rec['explanation'])
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Loan details
    if loan_rec['loan_amount'] > 0:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Loan Amount", format_indian_currency(loan_rec['loan_amount']))
        with col2:
            st.metric("Interest Rate", f"{loan_rec['interest_rate']}% p.a.")
        with col3:
            st.metric("Tenure", f"{loan_rec['tenure_months']} months")
    
    # Conditions
    if loan_rec.get('conditions'):
        st.markdown("**Conditions:**")
        for condition in loan_rec['conditions']:
            st.write(f"• {condition}")
    
    st.markdown("---")
    
    # Risk Factors
    st.subheader("⚠️ Risk Factors")
    for factor in risk_analysis['risk_factors']:
        st.write(f"• {factor}")
    
    # Validation Warnings
    if validation.get('warnings'):
        st.markdown("---")
        st.subheader("⚠️ Data Warnings")
        for warning in validation['warnings']:
            st.warning(warning)

def display_financial_dashboard(financial_data, validation):
    """Display financial metrics dashboard"""
    
    st.subheader("💰 Financial Metrics Dashboard")
    
    # Key metrics in columns
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.markdown("**💵 Revenue**")
        st.markdown(f"### {format_crores(financial_data.get('revenue'))}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.markdown("**💰 Net Profit**")
        st.markdown(f"### {format_crores(financial_data.get('net_profit'))}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.markdown("**🏦 Total Assets**")
        st.markdown(f"### {format_crores(financial_data.get('assets'))}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("")
    
    col4, col5, col6 = st.columns(3)
    
    with col4:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.markdown("**📊 Total Liabilities**")
        st.markdown(f"### {format_crores(financial_data.get('liabilities'))}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col5:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.markdown("**💳 Total Debt**")
        st.markdown(f"### {format_crores(financial_data.get('debt'))}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col6:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.markdown("**💸 Operating Cash Flow**")
        st.markdown(f"### {format_crores(financial_data.get('cash_flow'))}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Financial Summary Table
    st.subheader("📋 Financial Summary Table")
    import pandas as pd
    
    # Use safe numeric conversion to prevent overflow
    summary_data = {
        "Metric": ["Revenue", "Net Profit", "Total Assets", "Total Liabilities", "Total Debt", "Operating Cash Flow"],
        "Value (₹)": [
            safe_numeric_convert(financial_data.get('revenue')),
            safe_numeric_convert(financial_data.get('net_profit')),
            safe_numeric_convert(financial_data.get('assets')),
            safe_numeric_convert(financial_data.get('liabilities')),
            safe_numeric_convert(financial_data.get('debt')),
            safe_numeric_convert(financial_data.get('cash_flow'))
        ],
        "Formatted": [
            format_crores(financial_data.get('revenue')),
            format_crores(financial_data.get('net_profit')),
            format_crores(financial_data.get('assets')),
            format_crores(financial_data.get('liabilities')),
            format_crores(financial_data.get('debt')),
            format_crores(financial_data.get('cash_flow'))
        ]
    }
    
    try:
        df = pd.DataFrame(summary_data)
        # Ensure Value column is float64 to prevent overflow
        df['Value (₹)'] = df['Value (₹)'].astype('float64')
        st.dataframe(df, use_container_width=True, hide_index=True)
    except Exception as e:
        st.error(f"⚠️ Error displaying dataframe: {str(e)}")
        # Fallback: display as text
        for i, metric in enumerate(summary_data["Metric"]):
            st.write(f"**{metric}:** {summary_data['Formatted'][i]}")

def display_financial_ratios(ratios, interpretations):
    """Display financial ratios analysis"""
    
    st.subheader("📈 Key Financial Ratios")
    
    ratio_names = {
        'profit_margin': 'Profit Margin',
        'debt_to_asset_ratio': 'Debt-to-Asset Ratio',
        'asset_to_liability_ratio': 'Asset-to-Liability Ratio',
        'cash_flow_to_debt_ratio': 'Cash Flow to Debt Ratio',
        'return_on_assets': 'Return on Assets (ROA)',
        'current_ratio': 'Current Ratio'
    }
    
    for key, name in ratio_names.items():
        value = ratios.get(key)
        interpretation = interpretations.get(key, "⚪ Not Available")
        
        col1, col2, col3 = st.columns([2, 1, 2])
        with col1:
            st.write(f"**{name}**")
        with col2:
            if value is not None:
                display_value = f"{value}%" if 'margin' in key or 'return' in key else f"{value}"
                st.write(display_value)
            else:
                st.write("N/A")
        with col3:
            st.write(interpretation)
        
        st.markdown("---")
    
    # Benchmarks
    with st.expander("📊 Industry Benchmarks", expanded=False):
        benchmarks = get_ratio_benchmarks()
        for ratio_name, levels in benchmarks.items():
            st.write(f"**{ratio_name.replace('_', ' ').title()}:**")
            for level, value in levels.items():
                st.write(f"  • {level.title()}: {value}")

def display_research_intelligence(research_data):
    """Display external research intelligence"""
    
    st.subheader("🔍 External Intelligence Analysis")
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        sentiment_emoji = get_sentiment_emoji(research_data['sentiment'])
        st.metric(
            "News Sentiment",
            f"{sentiment_emoji} {research_data['sentiment']}",
            help="Overall sentiment from news analysis"
        )
    
    with col2:
        st.metric(
            "Risk Signals",
            len(research_data['risk_signals']),
            help="Number of risk keywords detected"
        )
    
    with col3:
        st.metric(
            "Articles Analyzed",
            research_data['articles_analyzed'],
            help="Number of news articles analyzed"
        )
    
    st.markdown("---")
    
    # Research Summary
    st.subheader("📝 Research Summary")
    st.info(research_data['research_summary'])
    
    # Risk Signals
    if research_data['risk_signals']:
        st.subheader("⚠️ Risk Signals Detected")
        for signal in research_data['risk_signals']:
            st.warning(f"• {signal}")
    else:
        st.success("✅ No major risk signals detected")
    
    # News Articles
    if research_data['news_articles']:
        st.subheader("📰 Recent News Articles")
        for article in research_data['news_articles'][:5]:
            with st.container():
                sentiment_emoji = get_sentiment_emoji(article.get('sentiment', 'Neutral'))
                st.markdown(f"**{sentiment_emoji} {article['headline']}**")
                st.caption(f"Source: {article.get('source', 'Unknown')} | Sentiment: {article.get('sentiment', 'Neutral')}")
                if article.get('summary'):
                    st.write(article['summary'][:200] + "...")
                if article.get('link'):
                    st.markdown(f"[Read more]({article['link']})")
                st.markdown("---")

def display_extracted_text(cleaned_text):
    """Display extracted text"""
    
    st.subheader("📄 Extracted Text")
    
    word_count = count_words(cleaned_text)
    char_count = len(cleaned_text)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Word Count", f"{word_count:,}")
    with col2:
        st.metric("Character Count", f"{char_count:,}")
    
    st.markdown("---")
    
    # Text preview
    with st.expander("👁️ Text Preview (First 2000 characters)", expanded=False):
        st.text(cleaned_text[:2000])
    
    # Full text
    with st.expander("📜 Full Extracted Text", expanded=False):
        st.text_area("", cleaned_text, height=400)
    
    # Download button
    st.download_button(
        label="⬇️ Download Extracted Text",
        data=cleaned_text,
        file_name="extracted_text.txt",
        mime="text/plain"
    )

if __name__ == "__main__":
    # Initialize session state
    if 'stats' not in st.session_state:
        st.session_state.stats = {'files': 0, 'pages': 0, 'words': 0}
    
    main()
