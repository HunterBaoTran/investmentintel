import streamlit as st
import requests
import re
from bs4 import BeautifulSoup
import sys
import os

# Enable backend folder imports
sys.path.append("backend")
from summarizer import summarize_text

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
            for i, form in enumerate(recent.get("form", [])):
                if form == "10-K":
                    accession = recent["accessionNumber"][i]
                    accession_raw = accession.replace("-", "")
                    break

            if not accession_raw:
                st.error("❌ No 10-K found.")
            else:
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
                    soup = BeautifulSoup(html, "html.parser")
                    text = soup.get_text(separator="\n")
                    st.text("TEXT DUMP:\n" + text[:10000])


                    # Define function to extract section by item header
                    def extract_section(text, item_label, next_labels):
                        # Clean and normalize
                        text = text.replace('\xa0', ' ').replace('\u200b', ' ')
                        text = re.sub(r'\n+', '\n', text)

                        # Skip first ~6000 characters to avoid TOC
                        body = text[6000:]

                        # Build regex patterns
                        item_pattern = re.compile(rf"{item_label}\s*[\.\-–—:]?\s*", re.IGNORECASE)
                        next_pattern = re.compile(r"|".join([rf"{lbl}\s*[\.\-–—:]?" for lbl in next_labels]), re.IGNORECASE)

                        # Find start
                        start_match = item_pattern.search(body)
                        if not start_match:
                            return None

                        start_idx = start_match.end()

                        # Find end
                        next_match = next_pattern.search(body, start_idx)
                        end_idx = next_match.start() if next_match else len(body)

                        return body[start_idx:end_idx].strip()


                    item_1a_text = extract_section(text, "Item 1A", ["Item 1B", "Item 2"])
                    item_7_text = extract_section(text, "Item 7", ["Item 7A", "Item 8"])


                    st.text("DEBUG: Item 1A Preview:\n" + (item_1a_text[:6000] if item_1a_text else "NOT FOUND"))
                    st.text("DEBUG: Item 7 Preview:\n" + (item_7_text[:6000] if item_7_text else "NOT FOUND"))


                    # Combine and truncate input
                    combined_text = ""
                    if item_1a_text:
                        combined_text += "RISK FACTORS:\n" + item_1a_text + "\n\n"
                    if item_7_text:
                        combined_text += "MD&A:\n" + item_7_text

                    if not combined_text:
                        st.error("❌ Couldn't extract Item 1A or 7 from the 10-K.")
                    else:
                        summary_input = combined_text[:6000]
                        with st.spinner("🤖 Summarizing Items 1A and 7..."):
                            summary = summarize_text(summary_input)
                            st.subheader("🔍 GPT Summary of Risk Factors + MD&A:")
                            st.write(summary)
                            st.markdown(f"[📄 View Full 10-K Filing]({html_url})", unsafe_allow_html=True)




