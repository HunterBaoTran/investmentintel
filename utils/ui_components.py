def info_bar(text, color="#1b4d3e", icon="✅"):
    return f'''
    <div style="
        background: {color};
        color: #fff;
        padding: 10px 18px;
        border-radius: 8px;
        margin-bottom: 12px;
        font-weight: 500;
        display: flex;
        align-items: center;
        font-size: 1.05rem;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04);
        border: 1px solid rgba(255,255,255,0.04);
    ">
        <span style="font-size:1.1em;margin-right:10px;line-height:1;">{icon}</span>
        <span style="line-height:1.2;">{text}</span>
    </div>
    '''

def section_status(label, found, size=None):
    if found:
        return f'<span style="color:#21ba45;font-weight:600;">✅ {label} ({size:,} chars)</span>'
    else:
        return f'<span style="color:#db2828;font-weight:600;">❌ {label} (Not Found)</span>' 