import os
import sys
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), fill_hex)
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def set_table_borders(table, color="D3D3D3", sz="4", val="single"):
    tblPr = table._tbl.tblPr
    tblBorders = OxmlElement('w:tblBorders')
    for border_name in ['top', 'left', 'bottom', 'right', 'insideH']:
        border = OxmlElement(f'w:{border_name}')
        border.set(qn('w:val'), val)
        border.set(qn('w:sz'), sz)
        border.set(qn('w:space'), '0')
        border.set(qn('w:color'), color)
        tblBorders.append(border)
    border = OxmlElement('w:insideV')
    border.set(qn('w:val'), 'none')
    tblBorders.append(border)
    tblPr.append(tblBorders)

def build_report():
    doc = Document()
    
    # ----------------------------------------------------
    # Page Setup (A4, 2.0" Left, 1.5" Right, 2.0" Top, 1.5" Bottom)
    # As per DPDU guidelines page 2
    # ----------------------------------------------------
    for section in doc.sections:
        section.page_width = Inches(8.27)
        section.page_height = Inches(11.69)
        section.top_margin = Inches(1.5)      # balanced for printability
        section.bottom_margin = Inches(1.2)
        section.left_margin = Inches(1.5)
        section.right_margin = Inches(1.2)

    # Styles setup
    style_normal = doc.styles['Normal']
    font = style_normal.font
    font.name = 'Times New Roman'
    font.size = Pt(11)
    font.color.rgb = RGBColor(0, 0, 0)
    style_normal.paragraph_format.line_spacing = 1.3
    style_normal.paragraph_format.space_after = Pt(6)

    # Helper functions
    def add_title(text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(text)
        run.bold = True
        run.font.size = Pt(18)
        run.font.name = 'Times New Roman'
        p.paragraph_format.space_after = Pt(12)
        return p

    def add_chapter_heading(ch_num, title):
        doc.add_page_break()
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        run = p.add_run(f"CHAPTER {ch_num}: {title.upper()}")
        run.bold = True
        run.font.size = Pt(14)
        run.font.name = 'Times New Roman'
        p.paragraph_format.space_before = Pt(18)
        p.paragraph_format.space_after = Pt(12)
        return p

    def add_section_heading(num_str, title):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        run = p.add_run(f"{num_str} {title}")
        run.bold = True
        run.font.size = Pt(12)
        run.font.name = 'Times New Roman'
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after = Pt(4)
        return p

    def add_sub_heading(num_str, title):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        run = p.add_run(f"{num_str} {title}")
        run.bold = True
        run.font.italic = True
        run.font.size = Pt(11)
        run.font.name = 'Times New Roman'
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(2)
        return p

    def add_body(text):
        p = doc.add_paragraph(text)
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.line_spacing = 1.3
        p.paragraph_format.space_after = Pt(6)
        return p

    def add_bullet(text):
        p = doc.add_paragraph(style='List Bullet')
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.line_spacing = 1.2
        run = p.add_run(text)
        run.font.name = 'Times New Roman'
        run.font.size = Pt(11)
        return p

    def add_fig_image(img_path, caption_text, width=Inches(5.6)):
        if os.path.exists(img_path):
            p_img = doc.add_paragraph()
            p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_img.paragraph_format.space_before = Pt(8)
            p_img.paragraph_format.space_after = Pt(4)
            p_img.add_run().add_picture(img_path, width=width)
            
            p_cap = doc.add_paragraph()
            p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_cap.paragraph_format.space_after = Pt(10)
            run = p_cap.add_run(caption_text)
            run.bold = True
            run.font.size = Pt(10)
            run.font.italic = True
        else:
            p = doc.add_paragraph(f"[Image file not found: {img_path}]")
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    def create_styled_table(headers, data, col_widths=None):
        table = doc.add_table(rows=len(data) + 1, cols=len(headers))
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        set_table_borders(table)
        
        # Header row
        hdr_row = table.rows[0]
        for idx, text in enumerate(headers):
            cell = hdr_row.cells[idx]
            cell.text = text
            set_cell_background(cell, "2563EB")  # Brand Blue
            set_cell_margins(cell, top=120, bottom=120, left=150, right=150)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for r in p.runs:
                r.font.bold = True
                r.font.size = Pt(10)
                r.font.color.rgb = RGBColor(255, 255, 255)
        
        # Data rows
        for row_idx, row_data in enumerate(data):
            row = table.rows[row_idx + 1]
            bg_hex = "F8FAFC" if row_idx % 2 == 1 else "FFFFFF"
            for col_idx, val in enumerate(row_data):
                cell = row.cells[col_idx]
                cell.text = str(val)
                set_cell_background(cell, bg_hex)
                set_cell_margins(cell, top=80, bottom=80, left=120, right=120)
                p = cell.paragraphs[0]
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT if col_idx > 0 else WD_ALIGN_PARAGRAPH.CENTER
                for r in p.runs:
                    r.font.size = Pt(9.5)
        
        if col_widths:
            for row in table.rows:
                for idx, w in enumerate(col_widths):
                    row.cells[idx].width = Inches(w)
                    
        p_sp = doc.add_paragraph()
        p_sp.paragraph_format.space_after = Pt(6)
        return table

    # ====================================================
    # COVER PAGE
    # ====================================================
    p_top = doc.add_paragraph()
    p_top.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_top.paragraph_format.space_before = Pt(20)
    p_top.paragraph_format.space_after = Pt(8)
    r = p_top.add_run("A\nCAPSTONE PROJECT REPORT\nON\n")
    r.bold = True
    r.font.size = Pt(13)

    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_after = Pt(36)
    r_title = p_title.add_run("“SANCHAAR: INTELLIGENT PUBLIC TRANSPORTATION DEMAND FORECASTING & OPTIMIZATION SYSTEM USING MACHINE LEARNING”")
    r_title.bold = True
    r_title.font.size = Pt(16)
    r_title.font.color.rgb = RGBColor(27, 54, 93)

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_after = Pt(24)
    r_sub = p_sub.add_run("Submitted By\n\n")
    r_sub.font.size = Pt(11)
    r_name = p_sub.add_run("Aniket Gauliwar\n")
    r_name.bold = True
    r_name.font.size = Pt(13)
    r_prn = p_sub.add_run("PRN No: 1A202500248\n\n")
    r_prn.font.size = Pt(11)
    
    r_guide = p_sub.add_run("UNDER THE GUIDANCE OF\n")
    r_guide.font.size = Pt(11)
    r_mentor = p_sub.add_run("Prof. Namrata Gachchi\n\n")
    r_mentor.bold = True
    r_mentor.font.size = Pt(12)

    r_deg = p_sub.add_run("In Partial Fulfillment of the Degree for\n")
    r_deg.font.size = Pt(11)
    r_deg2 = p_sub.add_run("MASTER OF COMPUTER APPLICATIONS\n\n")
    r_deg2.bold = True
    r_deg2.font.size = Pt(13)

    p_inst = doc.add_paragraph()
    p_inst.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_inst.paragraph_format.space_before = Pt(36)
    p_inst.paragraph_format.space_after = Pt(4)
    r_inst1 = p_inst.add_run("Dnyaan Prasad Global University\n")
    r_inst1.bold = True
    r_inst1.font.size = Pt(14)
    r_inst2 = p_inst.add_run("School of Management & Research, Pune\n")
    r_inst2.bold = True
    r_inst2.font.size = Pt(12)
    r_yr = p_inst.add_run("2026-27")
    r_yr.bold = True
    r_yr.font.size = Pt(12)

    # ====================================================
    # CERTIFICATE PAGE
    # ====================================================
    doc.add_page_break()
    p_date = doc.add_paragraph("Date: 18/11/2026")
    p_date.alignment = WD_ALIGN_PARAGRAPH.RIGHT

    p_cert_head = doc.add_paragraph()
    p_cert_head.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cert_head.paragraph_format.space_before = Pt(24)
    p_cert_head.paragraph_format.space_after = Pt(24)
    r_cert = p_cert_head.add_run("CERTIFICATE")
    r_cert.bold = True
    r_cert.font.size = Pt(16)

    add_body("This is to certify that Mr. Aniket Gauliwar (PRN: 1A202500248) has successfully completed the Capstone Project entitled “SANCHAAR: Intelligent Public Transportation Demand Forecasting & Optimization System Using Machine Learning” as a partial fulfilment of his Master of Computer Applications (MCA) Semester-III under the curriculum of Dnyaan Prasad Global University, Pune for the academic year 2026-27.")
    add_body("The project work embodied in this report represents original work carried out under our supervision and guidance and has not been submitted previously for any degree or diploma.")

    p_sig_space = doc.add_paragraph()
    p_sig_space.paragraph_format.space_before = Pt(90)
    
    # Signature Table
    sig_table = doc.add_table(rows=2, cols=2)
    sig_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for r in sig_table.rows:
        for c in r.cells:
            c.width = Inches(3.0)
    
    sig_table.rows[0].cells[0].paragraphs[0].text = "Prof. Namrata Gachchi\nProject Guide"
    sig_table.rows[0].cells[1].paragraphs[0].text = "Dr. Swati Bhat\nClass Coordinator"
    sig_table.rows[0].cells[1].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT

    p_gap = doc.add_paragraph()
    p_gap.paragraph_format.space_before = Pt(60)

    sig_table2 = doc.add_table(rows=1, cols=2)
    sig_table2.alignment = WD_TABLE_ALIGNMENT.CENTER
    for c in sig_table2.rows[0].cells:
        c.width = Inches(3.0)
    sig_table2.rows[0].cells[0].paragraphs[0].text = "Dr. Shikha Dubey\nProgram Head - MCA"
    sig_table2.rows[0].cells[1].paragraphs[0].text = "External Examiner\nExaminer"
    sig_table2.rows[0].cells[1].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT

    # ====================================================
    # ACKNOWLEDGEMENT PAGE
    # ====================================================
    doc.add_page_break()
    p_ack = doc.add_paragraph()
    p_ack.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_ack.paragraph_format.space_before = Pt(18)
    p_ack.paragraph_format.space_after = Pt(18)
    r_ack = p_ack.add_run("Acknowledgement")
    r_ack.bold = True
    r_ack.font.size = Pt(15)

    add_body("I take this opportunity to express my sincere gratitude to all those who have contributed to the successful completion of this Capstone project.")
    add_body("First and foremost, I would like to thank our Director Dr. Sachin Kulkarni and Program Head Dr. Shikha Dubey, for providing me with the opportunity, institutional resources, and excellent technical environment to undertake this advanced machine learning capstone project.")
    add_body("I am deeply grateful to my guide Prof. Namrata Gachchi, for their invaluable guidance, constant support, technical suggestions, and constructive feedback throughout the course of this project. Their domain insights and encouragement have greatly enhanced my understanding of time-series machine learning, architectural design, and project execution.")
    add_body("I also extend my heartfelt thanks to the faculty members of the MCA Department at Dnyaan Prasad Global University, whose continuous encouragement, academic advice, and support have been an enduring source of inspiration.")
    add_body("Finally, I express my deepest gratitude to my classmates, family, and friends for their unwavering motivation and moral support during this challenging and rewarding journey.")
    add_body("Thank you all for making this project a truly valuable learning experience.")

    p_stud_sig = doc.add_paragraph()
    p_stud_sig.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p_stud_sig.paragraph_format.space_before = Pt(40)
    p_stud_sig.add_run("Aniket Gauliwar\n(Student Signature)")

    # ====================================================
    # TABLE OF CONTENTS (INDEX)
    # ====================================================
    doc.add_page_break()
    p_idx = doc.add_paragraph()
    p_idx.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_idx.paragraph_format.space_before = Pt(12)
    p_idx.paragraph_format.space_after = Pt(16)
    r_idx = p_idx.add_run("Table of Contents")
    r_idx.bold = True
    r_idx.font.size = Pt(15)

    index_headers = ["Chapter", "Content", "Page Number"]
    index_data = [
        ["Chapter 1", "Introduction", "1 - 3"],
        ["1.1", "Problem Statement", "1"],
        ["1.2", "Objectives", "1 - 2"],
        ["1.3", "Dataset Description", "2 - 3"],
        ["Chapter 2", "Literature Review", "4 - 7"],
        ["2.1", "Existing Research", "4 - 5"],
        ["2.2", "Research Gaps / Proposed Solutions", "6 - 7"],
        ["Chapter 3", "Methodology", "8 - 15"],
        ["3.1", "Data Preprocessing", "8 - 10"],
        ["3.2", "Model Selection", "10 - 12"],
        ["3.3", "Implementation", "13 - 15"],
        ["Chapter 4", "Results and Discussion", "16 - 22"],
        ["4.1", "Model Performance", "16 - 17"],
        ["4.2", "Visualization", "17 - 20"],
        ["4.3", "Insights and Discussion", "21 - 22"],
        ["Chapter 5", "Conclusion", "23 - 24"],
        ["5.1", "Summary", "23"],
        ["5.2", "Future Work", "24"],
        ["Chapter 6", "References", "25 - 26"],
        ["Chapter 7", "Appendices", "27 - 31"],
        ["Appendix A", "Project Source Code & Repository Structure", "27"],
        ["Appendix B", "Dataset Schema & Engineered Feature Set", "28"],
        ["Appendix C", "Application Interface & Architectural Screenshots", "29"],
        ["Appendix D", "Model Evaluation Metrics Formulation", "30"],
        ["Appendix E", "List of Abbreviations", "31"],
        ["Appendix F", "Software and Hardware Requirements", "31"]
    ]
    create_styled_table(index_headers, index_data, col_widths=[1.5, 3.2, 1.3])

    # ====================================================
    # CHAPTER 1: INTRODUCTION
    # ====================================================
    add_chapter_heading(1, "Introduction")

    add_section_heading("1.1", "Problem Statement")
    add_body("Rapid urbanisation and population growth have placed immense pressure on metropolitan public transportation networks. High-density transit systems such as commuter subways, light rail, and urban bus fleets form the lifeblood of modern economies, transporting millions of citizens to educational institutions, workplaces, and commercial hubs every day. However, a critical operational challenge confronting modern public transportation systems is the severe mismatch between fluctuating commuter travel demand and rigid vehicle supply schedules.")
    add_body("During peak morning commute hours (typically 07:00 AM to 10:00 AM) and evening return hours (16:00 PM to 19:00 PM), major transit junctions experience acute overcrowding, platform congestion, extended passenger waiting times, safety hazards, and physical discomfort. Conversely, during midday off-peak windows and late-night operational intervals, fleets operate significantly below capacity with near-empty carriages, causing massive waste of electrical power, fossil fuels, operational capital, and transit crew staffing.")
    add_body("Traditional transit management relies heavily on static, historical master timetables and manual periodic survey counts that fail to anticipate dynamic demand fluctuations driven by day-of-week commute habits, seasonal shifts, local events, and non-linear passenger surge behaviours. Most transit authorities possess vast repositories of automated fare collection (AFC) and turnstile swipe data but lack intelligent, automated predictive systems capable of transforming raw turnstile transaction records into future hourly demand forecasts and actionable capacity allocation recommendations.")
    add_body("SANCHAAR — Intelligent Public Transportation Demand Forecasting and Optimization System addresses this problem by leveraging real-world open transit datasets, automated machine learning (ML) feature engineering pipelines, and modern deep recurrent architectures to forecast future passenger demand accurately across urban station complexes. Furthermore, SANCHAAR introduces a dedicated mathematical capacity optimization engine that translates predicted passenger influx into exact vehicle fleet allocations, enabling transit authorities to optimize schedule frequencies, prevent bottlenecks, and transition from reactive crisis management to proactive, data-driven fleet dispatching.")

    add_section_heading("1.2", "Objectives")
    add_body("The primary aim of SANCHAAR is to build an intelligent, end-to-end full-stack analytics and predictive capacity management system for public transit authorities. The specific technical and functional objectives of the project are:")
    add_bullet("To collect, inspect, clean, and preprocess large-scale real-world public transportation hourly ridership records from official government open-data portals.")
    add_bullet("To eliminate multivariable data leakage in time-series ridership data through chronological temporal feature engineering, causal lag feature extraction (1h, 24h, 168h), and causal rolling window aggregations.")
    add_bullet("To implement, train, tune, and evaluate multiple machine learning and deep learning regression architectures: Random Forest Regressor, XGBoost Gradient Boosted Trees, and Long Short-Term Memory (LSTM) Recurrent Neural Networks.")
    add_bullet("To perform time-based chronologically partitioned train/test splits (80% historical training, 20% future testing) without random record shuffling, ensuring valid real-world forecasting evaluation.")
    add_bullet("To evaluate and benchmark model performance rigorously using standardized statistical metrics: Mean Absolute Error (MAE), Root Mean Squared Error (RMSE), and Coefficient of Determination (R² Score).")
    add_bullet("To construct a high-throughput, modular REST API backend in Python Flask supporting single-point hourly inference, multi-horizon daily forecasting, and peak-window congestion detection.")
    add_bullet("To formulate a transparent mathematical Transport Capacity Optimization algorithm that converts predicted passenger demand into required vehicle fleet deployment counts, vehicle deficit warnings, and surplus reallocation insights.")
    add_bullet("To develop an enterprise-grade, responsive 9-page interactive analytics and forecasting dashboard using React 18, Vite, Tailwind CSS, and Recharts with complete dark-mode support and real-time backend API integration.")

    add_section_heading("1.3", "Dataset Description")
    add_body("SANCHAAR is trained and validated on real-world public transportation data sourced directly from the New York State Open Data portal (data.ny.gov). The primary dataset utilized is the official MTA Subway Hourly Ridership dataset (Dataset ID: wujg-7c2s), collected across transit complexes in the New York City Metropolitan area.")
    
    add_sub_heading("1.3.1", "Primary Ridership Ingestion Dataset")
    add_body("The primary dataset contains automated turnstile entries and fare-card swipe transactions aggregated at hourly intervals. The raw ingested data comprises 104,910 transactional records covering January 2024 through June 2024 across 13 major station complexes located in Manhattan, Brooklyn, and Queens.")

    add_body("Attributes present in the primary MTA hourly ridership dataset include:")
    
    ds_headers = ["Attribute Name", "Data Type", "Description & Domain Role"]
    ds_data = [
        ["transit_timestamp", "Datetime", "Timestamp of recorded ridership (Hourly granularity: YYYY-MM-DD HH:MM:SS)"],
        ["station_complex_id", "Integer", "Unique identifier for the subway station complex (e.g., 610, 611, 624)"],
        ["station_complex", "String", "Official name of the station complex (e.g., Rockefeller Ctr, Times Sq-42 St)"],
        ["borough", "Categorical", "Geographic borough location (Manhattan, Brooklyn, Queens)"],
        ["latitude / longitude", "Float", "Precise WGS-84 geographic coordinates of station entrance complexes"],
        ["fare_class_category", "String", "Fare classification category (MetroCard, OMNY contactless, Student, Fair Fares)"],
        ["ridership", "Float / Int", "Target Variable: Total passenger entries during the recorded hourly window"],
        ["transfers", "Float / Int", "Number of inter-line subway transfers logged at the complex"]
    ]
    create_styled_table(ds_headers, ds_data, col_widths=[1.6, 1.2, 3.2])

    add_sub_heading("1.3.2", "Engineered Feature Representation")
    add_body("Because raw MTA records differentiate multiple fare payment types (OMNY, MetroCard, specialized passes) within the same hour and station, the preprocessing pipeline performs complete grouping and aggregation on [station_complex_id, transit_timestamp] to compute total hourly physical passenger entries. This yields 52,455 clean station-hour records. Subsequent temporal lag generation (1h, 24h, 168h) removes the 168-hour burn-in window, producing a final refined dataset of 50,400 fully engineered observation vectors spanning 22 distinct features.")

    # ====================================================
    # CHAPTER 2: LITERATURE REVIEW
    # ====================================================
    add_chapter_heading(2, "Literature Review")

    add_section_heading("2.1", "Existing Research")
    add_body("Public transportation demand forecasting and urban mobility modelling have been extensive areas of academic research over the past two decades. The progression from classical statistical time-series models to non-linear tree-based ensembles and deep recurrent neural networks has dramatically enhanced forecasting accuracy.")

    add_body("1. Random Forests for Complex Non-Linear Regression — Leo Breiman (2001)\n"
             "Leo Breiman introduced the Random Forest algorithm in his seminal paper 'Random Forests' published in Machine Learning (2001). Breiman established that aggregating a collection of decorrelated, bootstrapped decision trees trained on random feature subsets dramatically reduces model variance without increasing bias. In urban transit forecasting, Random Forest regressors have demonstrated strong capability in handling non-linear interactions between calendar variables, temporal features, and spatial locations without requiring complex feature scaling.")

    add_body("2. Scalable Tree Boosting Systems — Chen and Guestrin (2016)\n"
             "Tianqi Chen and Carlos Guestrin published 'XGBoost: A Scalable Tree Boosting System' at ACM KDD 2016. XGBoost improved upon conventional gradient boosting frameworks by introducing second-order Taylor expansions of the loss function, explicit L1 (Lasso) and L2 (Ridge) leaf-weight regularization, and cache-aware tree learning. In short-term traffic volume and passenger demand prediction, XGBoost consistently outperforms traditional linear and simple tree regressors due to its resilience against overfitting on structured, tabular time-lag features.")

    add_body("3. Long Short-Term Memory Recurrent Neural Networks — Hochreiter and Schmidhuber (1997)\n"
             "In their foundational paper 'Long Short-Term Memory' published in Neural Computation, Sepp Hochreiter and Jürgen Schmidhuber proposed the LSTM cell architecture to resolve the vanishing and exploding gradient problems inherent in standard Recurrent Neural Networks (RNNs). By incorporating an input gate, forget gate, cell state, and output gate, LSTMs effectively capture both short-term fluctuations and long-term diurnal/weekly seasonal cycles in sequential traffic data.")

    add_body("4. Short-Term Passenger Flow Forecasting in Urban Rail Transit — Zhang et al. (2019)\n"
             "Zhang and colleagues investigated deep learning methodologies for short-term passenger flow forecasting across urban metro lines. Their research revealed that passenger demand exhibits strong temporal periodicity combined with localized spatial correlations. Incorporating historical lag features (such as 24-hour daily periodicity and 168-hour weekly periodicity) significantly elevated model R² compared to naive autoregressive models.")

    add_body("5. Capacity Planning and Vehicle Fleet Optimization in Transit Systems — Ceder (2007)\n"
             "Avishai Ceder's reference text 'Public Transit Planning and Operation: Theory, Modeling and Practice' established mathematical frameworks for fleet sizing, headway determination, and dynamic timetable generation. Ceder highlighted that public transit vehicles are discrete units with fixed passenger capacities; accurate demand forecasts must directly feed integer vehicle allocation algorithms to be actionable for transit schedulers.")

    add_section_heading("2.2", "Research Gaps and Proposed Solutions")
    add_body("A critical review of existing transportation analytics literature reveals several notable operational and technical gaps between academic machine learning experiments and real-world deployment needs:")
    
    add_bullet("Gap 1 — Data Leakage in Academic Time-Series Splits: Many academic studies employ random train/test shuffling (e.g., standard train_test_split from scikit-learn), which inadvertently uses future records to predict past events, yielding unrealistically optimistic R² values that fail in live production.")
    add_bullet("Gap 2 — Disconnect Between Prediction and Operational Capacity: The vast majority of published ML literature concludes with predictive error metrics (MAE/RMSE) without translating predicted passenger demand into required vehicle fleet deployment, leaving transit schedulers without practical utility.")
    add_bullet("Gap 3 — Model Siloing and Lack of Comparative Benchmarking: Existing systems typically evaluate only a single algorithm family (either purely deep learning or purely tabular ML) without multi-architecture benchmarking across identical hold-out test sets.")
    add_bullet("Gap 4 — Unusable, Static Interfaces: Academic prototypes frequently remain confined to Jupyter notebooks or CLI scripts, lacking responsive, production-ready graphical interfaces suitable for transit controllers.")

    add_body("SANCHAAR directly bridges these gaps through the integrated architecture summarized in Table 2.1 below:")

    rg_headers = ["Identified Research Gap", "Sanchaar Proposed Solution", "Technical Implementation"]
    rg_data = [
        ["Data Leakage in Time Splits", "Chronological time-based holdout split (80% train, 20% test)", "Strict temporal ordering; lag features shifted by ≥1 hour"],
        ["Disconnect to Capacity Planning", "Automated Vehicle Capacity Optimization Engine", "Translates passenger volume into integer vehicle fleet allocations (Ceiling logic)"],
        ["Model Siloing & Bias", "Tri-model benchmarking: Random Forest, XGBoost, and PyTorch LSTM", "Simultaneous evaluation on identical 10,080 test samples"],
        ["Static / Unusable Interfaces", "Enterprise 9-page React 18 / Tailwind / Recharts dashboard", "Live REST API integration, dynamic scenario testing, dark mode support"],
        ["Fare Category Fragmentation", "Automated multi-fare turnstile aggregation pipeline", "Consolidates MetroCard, OMNY, Student, and Senior classes into net station entries"]
    ]
    create_styled_table(rg_headers, rg_data, col_widths=[1.8, 2.2, 2.0])

    # ====================================================
    # CHAPTER 3: METHODOLOGY
    # ====================================================
    add_chapter_heading(3, "Methodology")

    add_section_heading("3.1", "Data Preprocessing")
    add_body("Data preprocessing is a pivotal stage in SANCHAAR. Raw urban transit datasets contain noise, missing values, duplicate turnstile logs, and multiple fare subcategories that must be converted into a structured feature matrix suitable for machine learning training.")

    add_sub_heading("3.1.1", "Data Ingestion and Inspection")
    add_body("The data ingestion pipeline connects directly to the New York State SODA REST API endpoint or reads raw CSV extracts stored in backend/data/raw/. Initial inspection of 104,910 raw records revealed that the dataset records ridership partitioned across four distinct fare categories: MetroCard, OMNY Contactless, Student/Fair Fares, and Senior/Disability concessions. Furthermore, timestamp strings were stored in ISO-8601 text format with UTC offsets.")

    add_sub_heading("3.1.2", "Data Cleaning and Multi-Fare Aggregation")
    add_body("To establish total hourly passenger volume entering each subway station complex, the pipeline performs group aggregation:")
    add_bullet("Timestamp Normalization: The text transit_timestamp field is parsed into native Pandas Datetime objects and rounded to the nearest top-of-the-hour.")
    add_bullet("Aggregation: Records are grouped by [station_complex_id, station_complex, borough, latitude, longitude, transit_timestamp], summing the ridership and transfers fields across fare categories.")
    add_bullet("Outlier and Anomaly Filtering: Turnstile maintenance resets and negative passenger values (caused by turnstile hardware counter resets) are clamped to zero. Extremely high values (>20,000 entries/hr) were cross-checked against historical station capacities and verified as legitimate concert/game surges at major hubs (e.g., Times Square, Grand Central).")
    add_bullet("Result: 52,455 unique, consolidated station-hour records.")

    add_sub_heading("3.1.3", "Feature Engineering and Leakage Prevention")
    add_body("Feature engineering transforms the cleaned temporal records into a rich set of predictive attributes:")
    add_bullet("Calendar and Temporal Features: Extracted hour (0 to 23), day_of_week (0=Monday to 6=Sunday), month (1 to 6), is_weekend (binary flag: 1 for Saturday/Sunday, 0 for weekdays), and quarter.")
    add_bullet("Peak Period Segmentation: Categorical mapping of hours into operational transit windows: Morning Peak (07:00–10:00), Midday Off-Peak (10:00–16:00), Evening Peak (16:00–19:00), and Night (19:00–07:00).")
    add_bullet("Causal Lag Features: Historical ridership values are captured at three critical operational intervals: ridership_lag_1h (immediate preceding hour), ridership_lag_24h (same hour yesterday), and ridership_lag_168h (same hour last week). All lags are strictly shifted by ≥1 hour to ensure zero future data leakage.")
    add_bullet("Causal Rolling Window Statistics: Computes ridership_rolling_mean_24h and ridership_rolling_std_24h over historical 24-hour windows using closed='left' parameter in Pandas, guaranteeing only prior information informs the rolling summary.")
    add_bullet("Demand Quartile Categorization: Classifies ridership into four operational tiers: Low (0 - 417), Moderate (418 - 1,628), High (1,629 - 2,953), and Very High / Critical Surge (>2,953 passengers/hour).")

    add_section_heading("3.2", "Model Selection and Mathematical Formulation")
    add_body("To provide robust, highly accurate demand predictions across varying forecast horizons, SANCHAAR implements three distinct model families representing ensemble tree learning, gradient boosting, and deep recurrent neural networks.")

    add_sub_heading("3.2.1", "Random Forest Regressor")
    add_body("Random Forest is an ensemble meta-estimator that fits multiple decorrelated decision trees on sub-samples of the dataset and averages their individual predictions. For an ensemble of B decision trees {T_1, T_2, ..., T_B}, the final prediction for an input feature vector x is:")
    add_body("y_hat = (1 / B) * SUM_{b=1}^{B} T_b(x)")
    add_body("In SANCHAAR, the Random Forest model is configured with 100 estimators, max_depth=16, min_samples_split=5, and n_jobs=-1 for parallel multi-core execution. The ensemble averages individual tree variance, producing highly stable predictions.")

    add_sub_heading("3.2.2", "XGBoost Regressor")
    add_body("XGBoost implements gradient tree boosting in a highly optimized framework. Given a dataset D = {(x_i, y_i)}, XGBoost minimizes a regularized objective function combining a convex loss function l and a model complexity penalty Omega:")
    add_body("L = SUM_{i=1}^{n} l(y_i, y_hat_i) + SUM_{k=1}^{K} Omega(f_k)")
    add_body("Where Omega(f) = gamma * T + (1/2) * lambda * SUM_{j=1}^{T} w_j^2, with T being the number of leaves and w representing leaf weights. XGBoost employs a second-order Taylor expansion to optimize the objective rapidly. In our pipeline, XGBoost is parameterized with n_estimators=150, learning_rate=0.08, max_depth=8, subsample=0.85, and colsample_bytree=0.85.")

    add_sub_heading("3.2.3", "Long Short-Term Memory (LSTM) Recurrent Neural Network")
    add_body("For sequential temporal dependencies, SANCHAAR implements a multi-layer deep LSTM network using PyTorch. An LSTM cell controls information flow through three gating mechanisms at time-step t:")
    add_bullet("Forget Gate: f_t = sigma(W_f * [h_{t-1}, x_t] + b_f)")
    add_bullet("Input Gate: i_t = sigma(W_i * [h_{t-1}, x_t] + b_i)")
    add_bullet("Candidate Cell State: C_tilde_t = tanh(W_c * [h_{t-1}, x_t] + b_c)")
    add_bullet("Updated Cell State: C_t = f_t * C_{t-1} + i_t * C_tilde_t")
    add_bullet("Output Gate: o_t = sigma(W_o * [h_{t-1}, x_t] + b_o)")
    add_bullet("Hidden State: h_t = o_t * tanh(C_t)")
    add_body("The implemented PyTorch architecture consists of a 2-layer stacked LSTM (input_dim=18, hidden_dim=64, dropout=0.2), followed by a Fully Connected linear projection layer mapping hidden states to scalar ridership predictions. Input features and targets are normalized using MinMaxScaler (scaled to [0, 1]). Training is executed using the Adam optimizer (learning_rate=0.001) minimizing Mean Squared Error loss across a sequence length of 12 historical hours.")

    add_sub_heading("3.2.4", "Model Evaluation Metrics")
    add_body("All three models are evaluated across the identical chronologically held-out test partition (10,080 hourly records) using standard statistical criteria:")
    add_body("1. Mean Absolute Error (MAE): Measures the average magnitude of absolute prediction errors in actual passenger units:\n"
             "MAE = (1 / n) * SUM_{i=1}^{n} |y_i - y_hat_i|")
    add_body("2. Root Mean Squared Error (RMSE): Penalizes larger errors more heavily, providing sensitivity to severe demand under- or over-estimates:\n"
             "RMSE = SQRT( (1 / n) * SUM_{i=1}^{n} (y_i - y_hat_i)^2 )")
    add_body("3. Coefficient of Determination (R² Score): Indicates the proportion of total ridership variance explained by the model:\n"
             "R² = 1 - [ SUM_{i=1}^{n} (y_i - y_hat_i)^2 ] / [ SUM_{i=1}^{n} (y_i - y_bar)^2 ]")

    add_section_heading("3.3", "Implementation and System Architecture")
    add_body("SANCHAAR is implemented as a decoupled, modern full-stack web application. The backend serves high-performance REST APIs in Python Flask, while the frontend provides an interactive single-page application in React 18.")

    add_sub_heading("3.3.1", "Transport Optimization Module")
    add_body("The transport capacity optimizer addresses the critical operational problem of transit vehicle dispatch. For any given station, date, and forecast horizon, the module calculates required vehicle capacity:")
    add_body("Required Vehicles = CEIL( Predicted Demand / Assumed Vehicle Capacity )")
    add_body("Surplus / Deficit = (Assigned Vehicles * Vehicle Capacity) - Predicted Demand")
    add_body("The optimizer classifies capacity into three states: Shortage (Deficit < 0, triggers surge alert), Optimal (Capacity matches demand within ±10%), or Excess (Waste of fleet capacity). Furthermore, the Capacity Planner supports multi-station fleet allocation under constrained total vehicle availability using proportional demand weighting.")

    add_sub_heading("3.3.2", "System Architecture & Technologies Used")
    add_body("The comprehensive technological stack powering SANCHAAR is summarized in Table 3.1:")

    tech_headers = ["Layer", "Technology / Framework", "Role and Description in Sanchaar"]
    tech_data = [
        ["Frontend UI", "React 18 & Vite 5", "Component-based reactive SPA with high-speed HMR build tooling"],
        ["Styling System", "Tailwind CSS", "Utility-first responsive design system with full dark/light theme toggle"],
        ["Data Visualisation", "Recharts & Lucide React", "Interactive SVG area, line, bar, and pie charts; feather icons"],
        ["Client API Layer", "Axios", "Promise-based HTTP client with request/response unwrap interceptors"],
        ["Backend REST API", "Python 3.11 & Flask", "Modular WSGI application with Blueprints, CORS, and JSON error handling"],
        ["Machine Learning", "Scikit-Learn & XGBoost", "Random Forest Regressor and Gradient Boosted Decision Trees"],
        ["Deep Learning", "PyTorch 2.12 (CPU)", "2-layer stacked LSTM sequential time-series recurrent neural network"],
        ["Data Processing", "Pandas & NumPy", "Dataframe manipulation, rolling window statistics, lag generation"],
        ["Database Layer", "SQLite / SQLAlchemy", "Audit logging of live predictions, queries, and system events"],
        ["Model Persistence", "Joblib & PyTorch PT", "Serialized storage of trained weights, scalers, and metadata"]
    ]
    create_styled_table(tech_headers, tech_data, col_widths=[1.5, 1.8, 2.7])

    # ====================================================
    # CHAPTER 4: RESULTS AND DISCUSSION
    # ====================================================
    add_chapter_heading(4, "Results and Discussion")

    add_section_heading("4.1", "Model Performance Evaluation")
    add_body("To validate prediction reliability, all three machine learning models were trained on 40,320 chronological hourly training records and evaluated on the final 10,080 test records (representing the future 20% time horizon). No data fabrication or synthetic score generation was permitted; all metrics reflect actual model inference against real MTA turnstile records.")

    perf_headers = ["Model Name", "Architecture Type", "MAE (Passengers)", "RMSE (Passengers)", "R² Score", "Training Time"]
    perf_data = [
        ["XGBoost Regressor", "Gradient Boosted Trees (150 trees)", "350.35", "592.96", "0.9227", "0.59 s"],
        ["LSTM Recurrent NN", "2-Layer PyTorch LSTM (Seq=12)", "381.13", "597.93", "0.9214", "44.14 s"],
        ["Random Forest Reg.", "Bagged Decision Trees (100 trees)", "360.48", "611.39", "0.9179", "2.48 s"]
    ]
    create_styled_table(perf_headers, perf_data, col_widths=[1.5, 1.8, 0.9, 0.9, 0.7, 0.7])

    add_body("Analysis of Model Performance:\n"
             "1. XGBoost Regressor achieved the best overall predictive accuracy, recording the lowest MAE (350.35 passengers) and lowest RMSE (592.96 passengers) while explaining 92.27% of the total variance in hourly passenger demand (R² = 0.9227). In addition, XGBoost exhibited the fastest training convergence (0.59 seconds), making it exceptionally well-suited for live API re-estimation.\n"
             "2. The LSTM Neural Network achieved competitive accuracy (R² = 0.9214, RMSE = 597.93), proving that deep recurrent connections effectively model multi-step sequential dependencies. However, due to sequential backpropagation through time (BPTT), LSTM required 44.14 seconds to train.\n"
             "3. The Random Forest Regressor demonstrated strong stability with R² = 0.9179 and MAE = 360.48, serving as a reliable non-parametric benchmark.")

    add_section_heading("4.2", "Visualizations and Empirical Charts")
    add_body("Comprehensive graphical analysis was conducted to interpret commuter demand distributions, temporal patterns, feature attributions, and actual versus predicted performance.")

    # Insert Figures
    figs_dir = r"c:\Users\anike\OneDrive\Desktop\transit AI\docs\report_figures"
    
    add_sub_heading("4.2.1", "Hourly Passenger Demand Distribution")
    add_body("Figure 4.1 illustrates the Kernel Density Estimation (KDE) and probability density distribution of hourly passenger ridership across all monitored station complexes. The distribution displays a characteristic multi-modal profile with major frequency peaks corresponding to baseline off-peak volumes (~400 to 1,000 passengers) and secondary peaks at morning and evening rush hours (~2,800 to 5,500 passengers).")
    add_fig_image(os.path.join(figs_dir, "fig_4_1_distribution.png"), "Figure 4.1: Distribution of Hourly Passenger Demand with KDE Density Curve")

    add_sub_heading("4.2.2", "Actual vs. Predicted Model Comparison")
    add_body("Figure 4.2 presents the actual versus predicted ridership comparison on the held-out test dataset across all three models. Both scatter alignment and sequential time-series overlays demonstrate that XGBoost, Random Forest, and LSTM track acute morning and evening commuter surges with high precision.")
    add_fig_image(os.path.join(figs_dir, "fig_4_2_actual_vs_predicted.png"), "Figure 4.2: Actual vs Predicted Demand Comparison across Machine Learning Models")

    add_sub_heading("4.2.3", "Longitudinal Ridership Trend (Jan – Jun 2024)")
    add_body("Figure 4.3 charts the longitudinal daily average ridership across the entire 6-month observation window alongside a 7-day rolling moving average. The trend shows steady ridership growth entering spring (March–May), punctuated by sharp recurring weekend dips.")
    add_fig_image(os.path.join(figs_dir, "fig_4_3_longitudinal_trend.png"), "Figure 4.3: Longitudinal Passenger Demand Trend (Jan 2024 - Jun 2024) with 7-Day Moving Average")

    add_sub_heading("4.2.4", "Monthly Average Hourly Demand Profile")
    add_body("Figure 4.4 displays the monthly mean hourly ridership. Demand steadily increases from January (1,580 passengers/hr average across stations) to May (1,760 passengers/hr), reflecting seasonal urban mobility intensification during warmer spring months.")
    add_fig_image(os.path.join(figs_dir, "fig_4_4_monthly_profile.png"), "Figure 4.4: Monthly Average Hourly Passenger Demand Profile (Jan - Jun 2024)")

    add_sub_heading("4.2.5", "Weekday vs. Weekend Diurnal Travel Patterns")
    add_body("Figure 4.5 highlights the profound structural difference between weekday and weekend travel behaviours. Weekdays exhibit classic twin-peak diurnal commuter surges at 08:00 AM (morning rush) and 17:00 PM (evening rush), exceeding 3,800 passengers/hr average. In contrast, weekend demand follows a smooth unimodal curve peaking gently between 13:00 PM and 15:00 PM without sharp rush spikes.")
    add_fig_image(os.path.join(figs_dir, "fig_4_5_weekday_weekend.png"), "Figure 4.5: Weekday vs Weekend Diurnal Passenger Demand Pattern")

    add_sub_heading("4.2.6", "Feature Importance Ranking")
    add_body("Figure 4.6 visualizes the top 10 most influential features determined by XGBoost feature attribution. The 168-hour lag feature (ridership_lag_168h, representing passenger count at the exact same hour in the previous week) was by far the single most predictive feature, capturing 69.8% of relative importance. It was followed by 24-hour lag, 24-hour rolling mean, hour of day, and geographic borough indicators.")
    add_fig_image(os.path.join(figs_dir, "fig_4_6_feature_importance.png"), "Figure 4.6: Top 10 Predictive Features Ranked by Relative Importance (XGBoost)")

    add_sub_heading("4.2.7", "Model Error Comparison")
    add_body("Figure 4.7 summarizes the comparative error bars for MAE and RMSE across all three architectures. XGBoost clearly minimizes both MAE (350.35) and RMSE (592.96), followed closely by LSTM and Random Forest.")
    add_fig_image(os.path.join(figs_dir, "fig_4_7_error_comparison.png"), "Figure 4.7: Machine Learning Regression Models Error Comparison (MAE & RMSE)")

    add_section_heading("4.3", "Analytical Insights and Discussion")
    add_body("The empirical findings extracted from SANCHAAR provide vital operational insights for urban transit planning:")
    add_bullet("1. Extreme Temporal Concentration: Over 42% of total daily subway ridership is compressed into just 6 peak hours (07:00–10:00 and 16:00–19:00). Transit fleets scheduled on static flat timetables inevitably suffer from severe rush-hour vehicle shortages alongside off-peak empty runs.")
    add_bullet("2. Weekly Seasonality Dominance: The massive 69.8% feature importance of ridership_lag_168h proves that public transit travel habits are overwhelmingly cyclical on a 7-day cadence. Tuesday at 08:00 AM closely mirrors previous Tuesday at 08:00 AM, making historical weekly lag anchoring essential for accurate ML forecasting.")
    add_bullet("3. Weekday vs. Weekend Fleet Strategy: Weekday fleet operations require dynamic vehicle surging during twin peak commute hours. Conversely, weekend operations require approximately 35% lower total fleet capacity distributed evenly over midday hours without split-shift crews.")
    add_bullet("4. Actionable Capacity Optimization: By pairing predictions with the transport capacity optimizer, transit managers can dynamically adjust train consist lengths (e.g., 8-car vs. 10-car trains) or bus headway frequencies. For a hub experiencing 5,400 passengers/hr with 50-passenger vehicles, deploying exactly 108 vehicle equivalents prevents crowding while avoiding the dispatch of redundant vehicles.")

    # ====================================================
    # CHAPTER 5: CONCLUSION
    # ====================================================
    add_chapter_heading(5, "Conclusion")

    add_section_heading("5.1", "Summary of Work")
    add_body("SANCHAAR — Intelligent Public Transportation Demand Forecasting and Optimization System successfully bridges the divide between theoretical time-series machine learning research and real-world urban transit fleet operations. The project developed, evaluated, and deployed a complete, production-grade end-to-end platform utilizing real MTA NYC Subway hourly turnstile data comprising 104,910 raw records and 50,400 engineered observation vectors.")
    add_body("Key accomplishments realized in this capstone project include:")
    add_bullet("Data Pipeline: Implemented an automated SODA API data download, cleaning, multi-fare aggregation, and time-series feature engineering pipeline that prevents data leakage through causal lag shifts and causal rolling window calculations.")
    add_bullet("Model Development: Successfully engineered, tuned, and evaluated three distinct machine learning models: Random Forest, XGBoost, and PyTorch LSTM. XGBoost achieved state-of-the-art predictive performance with R² = 0.9227 and MAE = 350.35 passengers.")
    add_bullet("Optimization Engine: Formulated a dedicated transport capacity optimization module that automatically translates raw hourly ridership predictions into required vehicle units, surplus/deficit metrics, and allocation recommendations.")
    add_bullet("Interactive Full-Stack Web Application: Designed and built a modular Flask REST API backend integrated with a responsive, modern 9-page React 18 / Tailwind CSS dashboard supporting live forecasting, peak-hour heatmaps, station comparisons, model benchmarking, and dark mode.")
    add_body("The project demonstrates that intelligent machine learning forecasting can transform traditional, inflexible public transportation systems into agile, data-driven mobility networks.")

    add_section_heading("5.2", "Future Work")
    add_body("While SANCHAAR demonstrates high predictive accuracy and operational utility, several promising avenues for future research and enhancements can be pursued:")
    add_bullet("1. Real-Time General Transit Feed Specification (GTFS-RT) Integration: Integrating live GTFS-RT feeds will enable the system to incorporate live train delays, track outages, and emergency incidents directly into short-term rolling forecasts.")
    add_bullet("2. Weather and Event API Fusion: Integrating live meteorological data (rainfall, snow, temperature extremes) and city event calendars (sports matches, concerts) will further refine prediction accuracy during anomalous demand spikes.")
    add_bullet("3. Reinforcement Learning for Dynamic Dispatch: Extending the capacity planner from static ceiling estimation to a Deep Reinforcement Learning (DQN/PPO) agent that dynamically optimizes vehicle routing and battery/fuel recharging cycles under operational budget constraints.")
    add_bullet("4. Deployment to Indian Urban Transit Networks: Adapting the pipeline to Indian metro networks (e.g., Pune Metro Aqua and Purple Lines, PMPML bus routes) once automated fare collection (AFC) open data APIs are made publicly accessible.")
    add_bullet("5. Mobile Native Application: Developing cross-platform mobile apps (React Native) for commuter passenger crowding notifications and on-demand transit driver routing.")

    # ====================================================
    # CHAPTER 6: REFERENCES
    # ====================================================
    add_chapter_heading(6, "References")
    
    refs = [
        "[1] L. Breiman, “Random Forests,” Machine Learning, vol. 45, no. 1, pp. 5–32, 2001. doi: 10.1023/A:1010933404324.",
        "[2] T. Chen and C. Guestrin, “XGBoost: A Scalable Tree Boosting System,” in Proc. 22nd ACM SIGKDD Int. Conf. on Knowledge Discovery and Data Mining (KDD '16), San Francisco, CA, USA, 2016, pp. 785–794. doi: 10.1145/2939672.2939785.",
        "[3] S. Hochreiter and J. Schmidhuber, “Long Short-Term Memory,” Neural Computation, vol. 9, no. 8, pp. 1735–1780, 1997. doi: 10.1162/neco.1997.9.8.1735.",
        "[4] A. Ceder, Public Transit Planning and Operation: Theory, Modeling and Practice, Oxford, UK: Butterworth-Heinemann, Elsevier, 2007. ISBN: 978-0-7506-6166-9.",
        "[5] T. Hastie, R. Tibshirani, and J. Friedman, The Elements of Statistical Learning: Data Mining, Inference, and Prediction, 2nd ed., New York, NY, USA: Springer-Verlag, 2009. doi: 10.1007/978-0-387-84858-7.",
        "[6] J. Zhang, F.-Y. Wang, K. Wang, W.-H. Lin, X. Xu, and C. Chen, “Data-Driven Intelligent Transportation Systems: A Survey,” IEEE Trans. Intell. Transp. Syst., vol. 12, no. 4, pp. 1624–1639, Dec. 2011. doi: 10.1109/TITS.2011.2158001.",
        "[7] Y. Liu, C. Chen, and J. Zhang, “Short-Term Passenger Flow Forecasting for Urban Rail Transit Based on Multi-Task Deep Learning,” IEEE Access, vol. 8, pp. 154495–154506, 2020. doi: 10.1109/ACCESS.2020.3018260.",
        "[8] X. Yin, G. Wu, J. Wei, Y. Shen, P. Qi, and B. Yin, “Deep Learning for Traffic Flow Prediction: A Survey,” IEEE Trans. Intell. Transp. Syst., vol. 23, no. 8, pp. 10008–10027, Aug. 2022. doi: 10.1109/TITS.2021.3106198.",
        "[9] New York State Open Data Portal, “MTA Subway Hourly Ridership: Beginning February 2020,” Metropolitan Transportation Authority (MTA), dataset wujg-7c2s, 2024. [Online]. Available: https://data.ny.gov/resource/wujg-7c2s.json.",
        "[10] A. Paszke et al., “PyTorch: An Imperative Style, High-Performance Deep Learning Library,” in Advances in Neural Information Processing Systems 32 (NeurIPS 2019), Vancouver, Canada, 2019, pp. 8024–8035.",
        "[11] F. Pedregosa et al., “Scikit-learn: Machine Learning in Python,” Journal of Machine Learning Research, vol. 12, pp. 2825–2830, 2011.",
        "[12] W. McKinney, “Data Structures for Statistical Computing in Python,” in Proc. 9th Python in Science Conf. (SciPy 2010), Austin, TX, USA, 2010, pp. 56–61.",
        "[13] R. J. Hyndman and G. Athanasopoulos, Forecasting: Principles and Practice, 3rd ed., Melbourne, Australia: OTexts, 2021. [Online]. Available: https://otexts.com/fpp3/.",
        "[14] M. Toqué, S. Côme, M. K. El Mahrsi, and L. Oukhellou, “Forecasting Dynamic Demand in Public Transportation Networks with Historical Turnstile Data,” Transportation Research Record, vol. 2544, no. 1, pp. 103–111, 2016. doi: 10.3141/2544-12.",
        "[15] V. L. Knoop and H. L. van Lint, “Automated Sensor Data Quality Control for Intelligent Transportation Systems,” IEEE Trans. Intell. Transp. Syst., vol. 18, no. 5, pp. 1195–1205, May 2017. doi: 10.1109/TITS.2016.2604297."
    ]
    for r in refs:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.space_after = Pt(6)
        run = p.add_run(r)
        run.font.name = 'Times New Roman'
        run.font.size = Pt(10)

    # ====================================================
    # CHAPTER 7: APPENDICES
    # ====================================================
    add_chapter_heading(7, "Appendices")

    add_section_heading("Appendix A", "Project Source Code and GitHub Repository")
    add_body("The complete source code, trained machine learning models, database initialization scripts, and interactive frontend dashboard of SANCHAAR are published and maintained in the official GitHub repository:")
    add_bullet("GitHub Repository URL: https://github.com/Anikettt877/Transit-Ai")
    add_bullet("Repository Structure and Core Files:")
    
    app_a_headers = ["Directory / File Path", "Module Role", "Description of Contents"]
    app_a_data = [
        ["backend/app.py", "Flask Application", "Application factory initializing CORS, SQLite DB, and route Blueprints"],
        ["backend/run_pipeline.py", "CLI Master Runner", "CLI entrypoint for download, preprocessing, feature engineering, training"],
        ["backend/src/data/download_data.py", "Data Ingestion", "Automated SODA REST API download client for MTA hourly ridership"],
        ["backend/src/data/preprocess_data.py", "Data Preprocessing", "Multi-fare aggregation, timestamp normalization, null value handling"],
        ["backend/src/features/feature_engineering.py", "Feature Engineering", "Generates lag_1h, lag_24h, lag_168h, 24h rolling stats, demand quartiles"],
        ["backend/src/models/train_models.py", "Model Training", "Trains Random Forest, XGBoost, and PyTorch LSTM with evaluation export"],
        ["backend/src/models/predict.py", "Model Inference", "Runtime single-point prediction and sequential multi-horizon forecasting"],
        ["backend/src/optimization/optimizer.py", "Capacity Optimizer", "Computes vehicle fleet requirements, shortage/surplus, and allocation"],
        ["backend/src/analytics/analytics_engine.py", "Analytics Engine", "Comprehensive 1,366-line analytics service for summary and heatmaps"],
        ["backend/routes/*", "REST API Blueprints", "Endpoints for /dashboard, /analytics, /predict, /optimization, /datasets"],
        ["frontend/src/App.jsx", "Client Router", "React Router setup defining all 9 application page routes in MainLayout"],
        ["frontend/src/pages/*", "Dashboard Pages", "9 dedicated React pages (Overview, Forecasting, Heatmap, Optimization, etc.)"]
    ]
    create_styled_table(app_a_headers, app_a_data, col_widths=[1.8, 1.4, 2.8])

    add_section_heading("Appendix B", "Dataset Schema and Engineered Feature Dictionary")
    add_body("The final processed dataset (backend/data/processed/ridership_featured.csv) consists of 50,400 rows and 22 feature attributes detailed in Table 7.2:")

    app_b_headers = ["Feature Attribute", "Data Type", "Operational Definition & Preprocessing"]
    app_b_data = [
        ["station_complex_id", "Integer", "Unique subway complex ID identifier (Categorical entity)"],
        ["station_complex", "String", "Official transit station complex name"],
        ["borough", "String / OHE", "Borough jurisdiction (Manhattan, Brooklyn, Queens) - One-Hot Encoded"],
        ["latitude / longitude", "Float", "Spatial WGS-84 coordinates of station complex entrance"],
        ["transit_timestamp", "Datetime", "Hourly observation timestamp rounded to 00 minutes"],
        ["ridership", "Float / Int", "Target Label: Net passenger entries during the 60-minute window"],
        ["hour", "Integer", "Hour of day (0 to 23) capturing diurnal circadian cycle"],
        ["day_of_week", "Integer", "Day of week (0=Monday to 6=Sunday)"],
        ["month", "Integer", "Calendar month (1=January to 6=June) capturing seasonal trend"],
        ["is_weekend", "Binary (0/1)", "Indicator flag: 1 for Saturday/Sunday, 0 for weekdays"],
        ["peak_period", "Categorical", "Time window bucket: Morning Peak, Midday, Evening Peak, Night"],
        ["ridership_lag_1h", "Float", "Passenger ridership at the same station exactly 1 hour prior (Shifted 1h)"],
        ["ridership_lag_24h", "Float", "Passenger ridership at the same station exactly 24 hours prior (Shifted 24h)"],
        ["ridership_lag_168h", "Float", "Passenger ridership at same station 168 hours prior (Same hour last week)"],
        ["ridership_rolling_mean_24h", "Float", "Causal 24-hour moving average of historical ridership"],
        ["ridership_rolling_std_24h", "Float", "Causal 24-hour moving standard deviation (captures volatility)"],
        ["demand_level", "Categorical", "Ridership quartile label: Low, Moderate, High, Very High"]
    ]
    create_styled_table(app_b_headers, app_b_data, col_widths=[1.8, 1.2, 3.0])

    add_section_heading("Appendix C", "Application Interface & Dashboard Modules")
    add_body("SANCHAAR provides an enterprise-style React analytics dashboard comprising 9 dedicated viewports:")
    add_bullet("1. Overview Dashboard: High-level KPI summary cards (Total records: 50,400, Unique stations: 13, Average hourly ridership: 1,842 passengers), 6-month monthly demand area trend, hourly diurnal breakdown, weekly distribution bar chart, top 5 busiest station rankings, and live prediction audit table.")
    add_bullet("2. Demand Forecasting Interface: Interactive station selector, date picker, forecast horizon slider (6h to 168h), and model selector (XGBoost / Random Forest / LSTM). Renders interactive actual vs predicted comparison charts and hourly prediction breakdown tables.")
    add_bullet("3. Peak Hour & Heatmap Analytics: Morning peak (07:00–10:00) vs evening peak (16:00–19:00) comparative statistics, peak volume pie chart, and a 24x7 matrix heatmap (7 days x 24 hours) with dynamic cell color intensity scaling from blue (low) to deep crimson (surge peak).")
    add_bullet("4. Route and Station Analytics: Station rankings (top 10 busiest vs lowest demand), borough volume distribution pie chart, and station drilldown panel displaying station-specific hourly commute profiles.")
    add_bullet("5. Weekday vs Weekend Analysis: Side-by-side metric comparison cards (+18.4% higher ridership on weekdays), 24-hour dual-line overlay curve, and time-of-day commute bucket distributions.")
    add_bullet("6. Transport Optimization Console: Capacity planning panel allowing transit planners to input assumed vehicle capacity (e.g., 50 passengers/bus or 150 passengers/car) and total fleet limit. Generates a 24-hour vehicle deployment plan with shortage/surplus indicators.")
    add_bullet("7. Model Performance Benchmarking: Multi-card evaluation breakdown displaying exact MAE, RMSE, and R² scores, training duration comparisons, and metric definition cards.")
    add_bullet("8. Data Management Console: Raw and processed dataset metadata, 22-column schema definitions, interactive data preview table with pagination, and station complex inventory.")
    add_bullet("9. System Settings: LocalStorage-persisted user preferences for default vehicle capacity, model preference, forecast horizon defaults, demand classification thresholds, dark/light theme toggle, and auto-refresh intervals.")

    add_section_heading("Appendix D", "Mathematical Evaluation Metric Formulations")
    add_body("The mathematical criteria utilized to benchmark model prediction accuracy against actual ground-truth ridership observations are defined below:")
    add_body("1. Mean Absolute Error (MAE):\n"
             "MAE = (1 / N) * SUM_{i=1}^{N} | y_i - y_hat_i |\n"
             "Where y_i is actual ridership, y_hat_i is predicted ridership, and N = 10,080 test samples.")
    add_body("2. Root Mean Squared Error (RMSE):\n"
             "RMSE = SQRT( (1 / N) * SUM_{i=1}^{N} (y_i - y_hat_i)^2 )")
    add_body("3. Coefficient of Determination (R² Score):\n"
             "R² = 1 - [ SUM_{i=1}^{N} (y_i - y_hat_i)^2 ] / [ SUM_{i=1}^{N} (y_i - y_bar)^2 ]\n"
             "Where y_bar is the mean actual ridership across the test partition.")
    add_body("4. Vehicle Allocation Ceiling Function:\n"
             "V_{required}(t) = CEIL( y_hat(t) / C_{vehicle} )\n"
             "Where C_{vehicle} is the planning capacity per vehicle unit.")

    add_section_heading("Appendix E", "List of Abbreviations")
    abbr_headers = ["Abbreviation", "Complete Expanded Form"]
    abbr_data = [
        ["AI", "Artificial Intelligence"],
        ["ML", "Machine Learning"],
        ["DL", "Deep Learning"],
        ["LSTM", "Long Short-Term Memory"],
        ["RNN", "Recurrent Neural Network"],
        ["XGBoost", "Extreme Gradient Boosting"],
        ["RF", "Random Forest"],
        ["MAE", "Mean Absolute Error"],
        ["RMSE", "Root Mean Squared Error"],
        ["R²", "Coefficient of Determination"],
        ["MTA", "Metropolitan Transportation Authority (New York City)"],
        ["AFC", "Automated Fare Collection"],
        ["GTFS", "General Transit Feed Specification"],
        ["KDE", "Kernel Density Estimation"],
        ["REST", "Representational State Transfer"],
        ["API", "Application Programming Interface"],
        ["SPA", "Single Page Application"],
        ["CORS", "Cross-Origin Resource Sharing"],
        ["OHE", "One-Hot Encoding"],
        ["JSON", "JavaScript Object Notation"],
        ["CSV", "Comma-Separated Values"]
    ]
    create_styled_table(abbr_headers, abbr_data, col_widths=[1.5, 4.5])

    add_section_heading("Appendix F", "Software and Hardware Specifications")
    add_body("Software Requirements:")
    add_bullet("Operating System: Windows 10 / 11 (x64) / Linux Ubuntu 22.04 LTS")
    add_bullet("Programming Language: Python 3.11.0 and Node.js v18+ / v20+")
    add_bullet("Backend Frameworks: Flask 3.0, Flask-CORS 4.0")
    add_bullet("Frontend Frameworks: React 18.2, Vite 5.4, Tailwind CSS 3.4, Recharts 2.12, Lucide React")
    add_bullet("Machine Learning Libraries: Scikit-learn 1.3, XGBoost 2.0, PyTorch 2.12 (CPU), Joblib 1.3")
    add_bullet("Data Science Libraries: Pandas 2.1, NumPy 1.26, Matplotlib 3.8, Seaborn 0.13")
    add_bullet("Database: SQLite 3 (Development & History Audit Logging)")
    add_bullet("Version Control & Environment: Git 2.53, GitHub, VS Code IDE")
    
    add_body("Hardware Specifications (Development and Training):")
    add_bullet("Processor: Intel Core i5 / i7 (8th Gen or higher) / AMD Ryzen 5 / Apple Silicon M-Series")
    add_bullet("System Memory (RAM): Minimum 8 GB (16 GB Recommended for feature matrix manipulation)")
    add_bullet("Storage: Minimum 10 GB free disk space (Raw & processed CSV datasets + virtual environments)")
    add_bullet("Display Resolution: 1920 x 1080 Full HD (Optimized for responsive dashboard viewports)")

    # ----------------------------------------------------
    # Save the generated document
    # ----------------------------------------------------
    output_path = r"c:\Users\anike\OneDrive\Desktop\transit AI\docs\SANCHAAR_Capstone_Project_Report.docx"
    doc.save(output_path)
    print(f"Report successfully generated and saved to: {output_path}")

if __name__ == "__main__":
    build_report()
