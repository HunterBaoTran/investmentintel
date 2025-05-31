# backend/summarizer.py

import openai
import os
from dotenv import load_dotenv

load_dotenv()
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def summarize_text(text: str) -> str:
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": """You're a financial analyst summarizing 10-K reports. Format your response in the following structure using markdown:

1. **Executive Summary**
   - 2-3 bullet points highlighting the most critical information
   - Focus on key performance metrics and major risks

2. **Business Performance**
   | Category | Key Points | Impact | Future Outlook | Trend |
   |----------|------------|---------|----------------|-------|
   [For each metric, use [trend:good], [trend:neutral], [trend:bad] or the emoji 🟢, 🟡, 🔴 in the Trend column to indicate positive, neutral, or negative connotation.]

3. **Risk Analysis**
   | Risk Level | Risk Category | Description | Mitigation |
   |------------|---------------|-------------|------------|
   [Categorize risks as High/Medium/Low, and use [trend:bad], [trend:neutral], [trend:good] or emoji for severity.]

4. **Future Scenarios**
   | Scenario | Probability | Description | Potential Impact | Trend |
   |----------|-------------|-------------|------------------|-------|
   [Include Bull/Base/Bear cases, and use [trend:good], [trend:neutral], [trend:bad] or emoji in the Trend column.]

5. **Action Items**
   - Key metrics to monitor
   - Upcoming catalysts
   - Red flags to watch

Use markdown formatting for tables and emphasis. Keep each section concise and focused on actionable insights. Use [trend:good], [trend:neutral], [trend:bad] tags or emoji (🟢, 🟡, 🔴) for any trend/connotation column. Do not use progress bars."""},
                {"role": "user", "content": f"Analyze this 10-K section and provide a structured summary following the format above:\n\n{text}"}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Error while summarizing: {str(e)}"
