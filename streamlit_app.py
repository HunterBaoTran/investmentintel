import streamlit as st
import requests
import re
from bs4 import BeautifulSoup
import sys
import os
sys.path.append("backend")
from summarizer import summarize_text
from utils.ui_components import info_bar, section_status

def render_progress_bars(summary):
    # Pattern: [progress:VALUE:COLOR] or [progress:VALUE]
    pattern = r"\[progress:(\d{1,3})(?::(good|neutral|bad))?\]"
    color_map = {
        "good": "#21ba45",    # green
        "neutral": "#fbbd08", # yellow
        "bad": "#db2828"      # red
    }
    parts = []
    last_idx = 0
    for match in re.finditer(pattern, summary):
        start, end = match.span()
        value = int(match.group(1))
        color_key = match.group(2) or "good"
        color = color_map.get(color_key, "#21ba45")
        parts.append(summary[last_idx:start])
        bar_html = f'''
        <div style="background: #22232b; border-radius: 6px; width: 100%; height: 18px; margin: 4px 0;">
            <div style="background: {color}; width: {value}%; height: 100%; border-radius: 6px; text-align: right; color: #fff; font-size: 12px; padding-right: 8px;">
                {value}%
            </div>
        </div>
        '''
        parts.append(bar_html)
        last_idx = end
    parts.append(summary[last_idx:])
    return "".join(parts)

def markdown_table_to_html_with_bars(md_text):
    # Pattern to match markdown tables
    table_pattern = re.compile(r'(\|.+\|\n)(\|[-: ]+\|\n)((?:\|.*\|\n?)+)', re.MULTILINE)
    trend_pattern = r"\[trend:(good|neutral|bad)\]"
    emoji_map = {
        "good": ("🟢", "Good", "#21ba45"),
        "neutral": ("🟡", "Neutral", "#fbbd08"),
        "bad": ("🔴", "Bad", "#db2828")
    }
    def trend_html(trend):
        emoji, label, color = emoji_map.get(trend, ("", trend.title(), "#fff"))
        return f'<span style="color:{color};font-weight:bold;">{emoji} {label}</span>'
    def convert_table(md_table):
        lines = [line.strip() for line in md_table.strip().split('\n') if line.strip()]
        if len(lines) < 2:
            return md_table
        headers = [h.strip() for h in lines[0].split('|')[1:-1]]
        rows = [r for r in lines[2:]]
        html = '<table style="width:100%; margin:1em 0; border-collapse:collapse;">'
        html += '<thead><tr>' + ''.join([f'<th style="background:#22232b;color:#fff;padding:8px;">{h}</th>' for h in headers]) + '</tr></thead>'
        html += '<tbody>'
        for row in rows:
            cells = [c.strip() for c in row.split('|')[1:-1]]
            html += '<tr>'
            for cell in cells:
                # Replace [trend:...] tags with colored emoji and text
                match = re.search(trend_pattern, cell)
                if match:
                    cell = trend_html(match.group(1))
                # Also support direct emoji (🟢, 🟡, 🔴) by coloring them
                elif cell in ["🟢", "🟡", "🔴"]:
                    for k, v in emoji_map.items():
                        if cell == v[0]:
                            cell = trend_html(k)
                html += f'<td style="padding:8px;vertical-align:top;">{cell}</td>'
            html += '</tr>'
        html += '</tbody></table>'
        return html
    # Replace all markdown tables with HTML tables
    def table_replacer(match):
        return convert_table(match.group(0))
    html_text = table_pattern.sub(table_replacer, md_text)
    return html_text

st.markdown("""
    <style>
    body, .stApp {
        background-color: #181a1b;
        color: #e6e8ea;
        font-family: 'Segoe UI', 'Roboto', 'Arial', 'Liberation Sans', sans-serif;
        font-size: 1.08rem;
        letter-spacing: 0.01em;
    }
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: #e6e8ea;
        font-weight: 700;
        margin-top: 1.5em;
        margin-bottom: 0.7em;
        letter-spacing: 0.01em;
    }
    .stMarkdown ul, .stMarkdown ol {
        margin-bottom: 1.5em;
    }
    .stMarkdown table {
        background: #1b1c1d;
        border-radius: 8px;
        margin-bottom: 2em;
        border-collapse: separate;
        border-spacing: 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    .stMarkdown th, .stMarkdown td {
        border: none !important;
        padding: 14px 10px;
        font-size: 1.01rem;
    }
    .stMarkdown th {
        background: #232425 !important;
        color: #bfc2c7 !important;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    .stMarkdown td {
        color: #e6e8ea;
        background: #181a1b;
    }
    .stMarkdown tr:nth-child(even) td {
        background: #202124;
    }
    .stMarkdown tr:hover td {
        background: #232425;
    }
    .stMarkdown {
        font-size: 1.08rem;
        line-height: 1.7;
    }
    .stButton>button {
        background: #232425;
        color: #e6e8ea;
        border-radius: 6px;
        font-weight: 600;
        border: 1px solid #232425;
        padding: 0.5em 1.2em;
        transition: background 0.2s, color 0.2s;
    }
    .stButton>button:hover {
        background: #21ba45;
        color: #fff;
        border: 1px solid #21ba45;
    }
    hr, .stDivider {
        border: none;
        border-top: 1px solid #232425;
        margin: 2em 0;
    }
    .stApp, .stMarkdown, .stButton>button, .stTextInput>div>div>input {
        box-shadow: none !important;
    }
    .stTextInput>div>div>input {
        background: #232425;
        color: #e6e8ea;
        border-radius: 6px;
        border: 1px solid #232425;
        font-size: 1.05rem;
        padding: 0.5em 1em;
    }
    .stTextInput>div>div>input:focus {
        border: 1px solid #21ba45;
        outline: none;
    }
    #MainMenu, footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

st.title("📈 InvestorIntel: 10-K MD&A Summarizer")

ticker = st.text_input("Enter Stock Ticker (e.g., AAPL)").upper()

if ticker:
    with st.spinner("🔎 Looking up CIK..."):
        cik_url = f"https://www.sec.gov/cgi-bin/browse-edgar?CIK={ticker}&owner=exclude&action=getcompany&output=atom"
        res = requests.get(cik_url, headers={"User-Agent": "huntertran46@gmail.com"})
        if "CIK=" not in res.text:
            cik = None
        else:
            match = re.search(r"CIK=(\d+)", res.text)
            cik = match.group(1).zfill(10) if match else None

    if not cik:
        st.error("Ticker not found in SEC database.")
    else:
        st.success(f"✅ Found CIK: {cik}")
        with st.spinner("📄 Getting latest 10-K filing..."):
            submission_url = f"https://data.sec.gov/submissions/CIK{cik}.json"
            submission = requests.get(submission_url, headers={"User-Agent": "huntertran46@gmail.com"}).json()
            recent = submission.get("filings", {}).get("recent", {})
            
            accession_raw = None
            filing_date = None
            for i, form in enumerate(recent.get("form", [])):
                if form == "10-K":
                    accession = recent["accessionNumber"][i]
                    accession_raw = accession.replace("-", "")
                    filing_date = recent["filingDate"][i]
                    break

            if not accession_raw:
                st.error("❌ No 10-K found.")
            else:
                st.info(f"📅 Filing Date: {filing_date}")
                # Step 1: Load index.json for the filing 
                index_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession_raw}/index.json"
                index = requests.get(index_url, headers={"User-Agent": "huntertran46@gmail.com"}).json()

                # Step 2: Extract all .htm files
                htm_files = [
                    f["name"] for f in index.get("directory", {}).get("item", [])
                    if f["name"].endswith(".htm")
                ]

                # Step 3: Try to match company name format like aapl-20230930.htm
                html_file = None
                for f in htm_files:
                    if re.match(rf"{ticker.lower()}-\d{{8}}\.htm", f):
                        html_file = f
                        break

                # Step 4: Fallback – choose largest filename if match fails
                if not html_file and htm_files:
                    html_file = max(htm_files, key=len)  # Usually main filing is longest name

                if not html_file:
                    st.error("❌ Couldn't locate main 10-K HTML document.")
                else:
                    html_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession_raw}/{html_file}"
                    html = requests.get(html_url, headers={"User-Agent": "huntertran46@gmail.com"}).text
                    
                    # Improved HTML parsing
                    soup = BeautifulSoup(html, "html.parser")
                    
                    # Remove script and style elements
                    for script in soup(["script", "style"]):
                        script.decompose()
                    
                    # Find the main content div (usually has class 'ix-content')
                    main_content = soup.find('div', class_='ix-content')
                    if not main_content:
                        main_content = soup  # Fallback to entire document
                    
                    # Get text content with better structure handling
                    def get_clean_text(element):
                        # Remove navigation and TOC elements
                        for nav in element.find_all(['nav', 'table']):
                            nav.decompose()
                        
                        # Get text with preserved structure
                        text = element.get_text(separator='\n', strip=True)
                        
                        # Clean up text
                        text = re.sub(r'\n\s*\n', '\n', text)  # Remove multiple newlines
                        text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
                        return text
                    
                    text = get_clean_text(main_content)
                    
                    def find_section_boundaries(text, item_label, next_labels):
                        # First, find all potential section starts
                        potential_starts = []
                        patterns = [
                            rf"Item\s+{item_label}\.",  # Item 1A.
                            rf"Item\s+{item_label}\s*:",  # Item 1A:
                            rf"Item\s+{item_label}\s*-",  # Item 1A -
                            rf"Item\s+{item_label}\s*$",  # Item 1A at end of line
                            rf"Item\s+{item_label}\s*\([^)]+\)",  # Item 1A (Risk Factors)
                        ]
                        
                        for pattern in patterns:
                            for match in re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE):
                                # Get some context around the match
                                start = max(0, match.start() - 100)
                                end = min(len(text), match.end() + 100)
                                context = text[start:end]
                                
                                # Check if this looks like a real section start
                                # Only reject if it's clearly a reference or in a list
                                if not (
                                    # Should not be in a reference
                                    re.search(r'see\s+item\s+' + item_label, context, re.IGNORECASE) or
                                    # Should not be in a list
                                    re.search(r'^\s*[•\-\*]\s*', context)
                                ):
                                    potential_starts.append(match)
                        
                        if not potential_starts:
                            return None, None
                        
                        # Find the most likely start (usually the first one after Part I/II)
                        start_match = potential_starts[0]
                        
                        # Find the end by looking for the next section
                        end_patterns = []
                        for label in next_labels:
                            end_patterns.extend([
                                rf"Item\s+{label}\.",  # Item 1B.
                                rf"Item\s+{label}\s*:",  # Item 1B:
                                rf"Item\s+{label}\s*-",  # Item 1B -
                                rf"Item\s+{label}\s*$",  # Item 1B at end of line
                                rf"PART\s+{label}\s*$",  # PART II at end of line
                            ])
                        
                        next_pattern = re.compile(r"|".join(end_patterns), re.IGNORECASE | re.MULTILINE)
                        next_match = next_pattern.search(text, start_match.end())
                        
                        return start_match.end(), next_match.start() if next_match else len(text)
                    
                    def extract_section(text, item_label, next_labels):
                        start_idx, end_idx = find_section_boundaries(text, item_label, next_labels)
                        if start_idx is None:
                            return None
                        
                        # Extract and clean section
                        section = text[start_idx:end_idx].strip()
                        
                        # Additional cleaning
                        section = re.sub(r'^\s*[A-Za-z\s]+\s*$', '', section, flags=re.MULTILINE)  # Remove single-line headers
                        section = re.sub(r'\n\s*\n', '\n', section)  # Clean up newlines
                        section = re.sub(r'\s+', ' ', section)  # Normalize whitespace
                        
                        # Remove common header patterns
                        section = re.sub(r'^(?:Item|Part)\s+\d+[A-Za-z]?\s*[-–—:.]?\s*', '', section, flags=re.IGNORECASE)
                        section = re.sub(r'^(?:Management\'s Discussion|Risk Factors)\s*[-–—:.]?\s*', '', section, flags=re.IGNORECASE)
                        
                        return section.strip()

                    # Extract sections with improved patterns
                    item_1a_text = extract_section(text, "1A", ["1B", "2", "II"])
                    item_7_text = extract_section(text, "7", ["7A", "8", "III"])

                    # Show section extraction status
                    st.markdown("### Section Extraction Status", unsafe_allow_html=True)
                    if item_1a_text:
                        st.markdown(info_bar(f"Risk Factors found ({len(item_1a_text):,} chars)", "#1b4d3e", "✅"), unsafe_allow_html=True)
                    else:
                        st.markdown(info_bar("Risk Factors not found", "#7c2323", "❌"), unsafe_allow_html=True)

                    if item_7_text:
                        st.markdown(info_bar(f"MD&A found ({len(item_7_text):,} chars)", "#1b4d3e", "✅"), unsafe_allow_html=True)
                    else:
                        st.markdown(info_bar("MD&A not found", "#7c2323", "❌"), unsafe_allow_html=True)

                    # After section extraction status
                    st.markdown("<div style='height: 32px'></div>", unsafe_allow_html=True)

                    # Combine and truncate input
                    combined_text = ""
                    if item_1a_text:
                        combined_text += "RISK FACTORS:\n" + item_1a_text + "\n\n"
                    if item_7_text:
                        combined_text += "MD&A:\n" + item_7_text

                    if not combined_text:
                        st.error("❌ Couldn't extract Item 1A or 7 from the 10-K.")
                    else:
                        # Use a larger limit to capture more content while staying within model limits
                        # Prioritize MD&A content since it's typically more important for analysis
                        summary_input = ""
                        if item_7_text:
                            summary_input += "MD&A:\n" + item_7_text + "\n\n"
                        if item_1a_text:
                            # Take first 40,000 chars of Risk Factors to stay within model limits
                            summary_input += "RISK FACTORS:\n" + item_1a_text[:40000]
                        
                        with st.spinner("🤖 Analyzing 10-K Sections..."):
                            summary = summarize_text(summary_input)
                            # Add spacing before the 10-K summary
                            st.markdown("<div style='height: 32px'></div>", unsafe_allow_html=True)
                            # Use markdown with custom styling
                            st.markdown("""
                            <style>
                            .stMarkdown {
                                font-size: 16px;
                            }
                            .stMarkdown table {
                                width: 100%;
                                margin: 1em 0;
                            }
                            .stMarkdown th {
                                background-color: #22232b !important;
                                color: #fff !important;
                                padding: 8px;
                            }
                            .stMarkdown td {
                                padding: 8px;
                            }
                            </style>
                            """, unsafe_allow_html=True)
                            st.markdown(markdown_table_to_html_with_bars(summary), unsafe_allow_html=True)
                            st.markdown(f"[📄 View Full 10-K Filing]({html_url})", unsafe_allow_html=True)




