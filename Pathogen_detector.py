# Importing necassary packages
import streamlit as st
from streamlit_option_menu import option_menu
from streamlit_gsheets import GSheetsConnection
from rextractor.Rexcel import HRM_data, CT_Cycle
from pymicro.PyMicro import *
import yaml
import io
import time
from PIL import Image
import plotly.express as px
from fpdf import FPDF

icon_path = os.path.join("icons", "Pathogen Detector Icon.ico")
icon_image = Image.open(icon_path)

# Set the page configurationons
st.set_page_config(page_title="Pathogen Detector",
                   initial_sidebar_state="expanded", layout="wide", page_icon=icon_image)

gsheet_url = "https://docs.google.com/spreadsheets/d/1L5hBrjqB_7UWtcURcEHSa_wqmV-ru-9LpHVgIOMxpdY"

# Load the YAML file
credential_path = os.path.join("credentials","credentials.yaml")
with open(credential_path, 'r') as file:
    credentials = yaml.safe_load(file)


# Define page background color
page_bg_color = """
<style>
[data-testid="stAppViewContainer"]{
    background-color: #fffff;
}
[data-testid="stHeader"]{
    background-color: rgba(0,0,0,0)
}
[data-testid="stAppViewBlockContainer"]{
    padding-top: 0rem;
    position: relative;
}
[data-testid="stFileUploaderDropzoneInstructions"]{
    display:none;
}
[data-testid="stFileUploaderDropzone"]{
    background-color:rgba(0,0,0,0);
}
#MainMenu {
    visibility: hidden;
}
footer {
    visibility: hidden;
} 
[data-testid="stDeployButton"]{
    visibility: hidden;
}
[data-testid="stFileDropzoneInstructions"]{
    display: none;
}
.st-emotion-cache-ott0ng {
    padding: 0rem;
}
.st-emotion-cache-fis6aj{
    padding-left: 0rem;
}
[data-testid="stDecoration"]{
    display: none;
}
[data-baseweb="tab-border"]{
    visibility: hidden;
}
[data-testid="stFileUploadDropzone"]{
    background-color: rgba(0,0,0,0);
}
.st-emotion-cache-fqsvsg{
    font-size:0.7rem;
}
.st-emotion-cache-1mpho7o{
    padding-left:0rem;
}
.st-emotion-cache-fis6aj{
    line-height:1.10rem;
}
.st-emotion-cache-1v7f65g .e1b2p2ww15{
    padding-top:0rem;
    padding-botton:0rem;
}
.st-emotion-cache-16txtl3{
    padding: 1.7rem 1.5rem;
}
</style>
"""
st.markdown(page_bg_color, unsafe_allow_html=True)

# Class for Peforming Analysis


class Pathogen_Detector:

    def __init__(self):
        # Define page background color
        self.pymicro = PyMicro()
        self.final_report = None
        self.authenticator = None
        self.uploaded_data = None
        self.updated_result = pd.DataFrame(
            columns=['Pathogens', "Result"])
        self.manual_change = False
        self.ct_data_read = pd.DataFrame()
        self.melt_converted_data = pd.DataFrame()
        self.extracted_features = pd.DataFrame()
        self.take_off = pd.DataFrame()
        self.modfied_result = pd.DataFrame()
        self.option = None
        self.logical_result = None
        self.classified_result = pd.DataFrame()
        self.selected_barcode = None
        self.barcode = None
        self.updated_status = False
        self.Ct_data = None
        self.result = pd.DataFrame()
        self.raw_fluroscence = False
        self.melt_data = False
        self.melt_feature = False
        self.report = False

    def plot(self, data):
        if data.iloc[1, 1] > 2.0:
            title = "<i><b>Raw Fluorescence Curve</b></i>"
            ytitle = "<b>Fluorescence</b>"
            xtitle = '<b>Temperature in Celsius</b>'
        elif data.iloc[0, 0] == 1:
            title = "<i><b>Amplification Curve</b></i>"
            ytitle = "<b>Normalized Fluorescence</b>"
            xtitle = '<b>Cycle Time</b>'
        else:
            title = "<i><b>Melt Curve</b></i>"
            ytitle = '<b>dF/dT</b>'
            xtitle = '<b>Temperature in Celsius</b>'

        fig = px.scatter(width=900, height=430)
        for column in data.columns[1:]:
            fig.add_scatter(
                x=data.iloc[:, 0], y=data[column], name=column)
        fig.update_layout(title={'text': (title),
                                 "xanchor": 'center',
                                 'yanchor': 'top'},
                          title_x=0.5,
                          xaxis_title=xtitle,
                          yaxis_title=ytitle,
                          title_font_size=30,
                          title_font_family='Arial',
                          legend_itemclick="toggleothers",
                          legend_itemdoubleclick="toggleothers",
                          legend_groupclick="togglegroup",
                          legend_title_text='<b>Pathogens<b>',
                          legend_font_size=12,
                          legend_title_font_family='Arial',
                          legend_title_font_size=18,
                          legend_bgcolor="rgba(0,0,0,0)",
                          legend_borderwidth=1,
                          plot_bgcolor='rgba(0,0,0,0)',
                          title_font_color="#417B41",

                          )
        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(showgrid=False)

        st.plotly_chart(fig, use_container_width=True)

    def Interpreter(self):
        self.option = option_menu(
            None, options=["High Resolution Melt", "Amplification", "Result"], orientation='horizontal', icons=['bi bi-activity', 'bi bi-graph-up', 'bi bi-clipboard-check'])
        with st.sidebar:
            self.uploaded_data = st.file_uploader(
                "*Upload your Run Files*", label_visibility='collapsed')
        if self.uploaded_data is not None:
            if self.uploaded_data.name.split(".")[-1] == "rex":
                if self.option == "High Resolution Melt":
                    try:
                        self.dataframe_dict = HRM_data(io.BytesIO(
                            self.uploaded_data.getvalue()))

                        with st.sidebar:
                            self.selected_barcode = st.radio(
                                "*Patient ID*", options=self.dataframe_dict.keys())

                        data_read = self.pymicro.data_read(
                            self.dataframe_dict[self.selected_barcode])
                        melt_converted_data = self.pymicro.convert_to_melt()
                        extracted_features = self.pymicro.extraction()
                        self.logical_result = self.pymicro.logical_result()
                        # result = self.pymicro.model_result()

                        col1, col2, col3 = st.columns(
                            [0.63, 0.63, 0.35], gap='large')

                        with col1:
                            self.raw_fluroscence = st.button("Raw Fluroscence")
                        with col2:
                            self.melt_data = st.button("Melt Curve")
                        with col3:
                            self.melt_feature = st.button("Detected Features")

                        if self.raw_fluroscence:
                            self.plot(data_read)
                        if self.melt_data:
                            self.plot(melt_converted_data)
                        if self.melt_feature:
                            st.dataframe(extracted_features,
                                         use_container_width=True, hide_index=True)
                    except:
                        st.error("The Uploaded file seems to be Incomplete")

                elif self.option == "Amplification":
                    try:
                        self.dataframe_dict = CT_Cycle(
                            io.BytesIO(self.uploaded_data.getvalue()))
                        with st.sidebar:
                            self.barcode = st.radio(
                                "*Patient ID*", options=self.dataframe_dict.keys())
                        self.Ct_data = self.pymicro.ct_read(
                            self.dataframe_dict[self.barcode])
                        take_off = self.pymicro.take_off()
                        col1, col2 = st.columns([0.75, 2])
                        with col1:
                            self.amplification = st.button(
                                "Amplification Curve")
                        with col2:
                            self.take_off_points = st.button("Take Off Points")

                        if self.amplification:
                            self.plot(self.Ct_data)
                        if self.take_off_points:
                            st.dataframe(take_off, hide_index=True,
                                         use_container_width=True)
                    except:
                        st.error("CT Not Found")

                elif self.option == "Result":

                    model_result, update_result, view_ghseet = st.tabs(
                        ['Result', "Manual Interpretation", "Updated Features"])
                    dataframe_dict = HRM_data(io.BytesIO(
                        self.uploaded_data.getvalue()))
                    dataframe_ct = CT_Cycle(
                        io.BytesIO(self.uploaded_data.getvalue()))

                    with st.sidebar:
                        self.selected_barcode = st.radio(
                            "*Patient ID*", options=dataframe_dict.keys())

                    data_read = self.pymicro.data_read(
                        dataframe_dict[self.selected_barcode])
                    self.ct_data_read = self.pymicro.ct_read(
                        dataframe_ct[self.selected_barcode])
                    self.melt_converted_data = self.pymicro.convert_to_melt()
                    self.extracted_features = self.pymicro.extraction()
                    self.take_off = self.pymicro.take_off()
                    self.logical_result = self.pymicro.logical_result()
                    self.result, feature_data = self.pymicro.model_result()
                    original_feature = feature_data.copy()

                    if self.result.empty:
                        st.warning(
                            "MEP Not Found (or) Check Pathogens Naming Conventions")
                    else:
                        with model_result:
                            st.dataframe(self.result, hide_index=True,
                                         use_container_width=True)

                            def report(melt_data, ct_read_data, feature_data, take_off, result):
                                melt_converted_data = melt_data.copy()
                                ct_data = ct_read_data.copy()

                                main_image_figure, ax = plt.subplots(
                                    figsize=(15, 10))
                                for column in melt_converted_data.columns[1:]:
                                    ax.plot(
                                        melt_converted_data.iloc[:, 0], melt_converted_data[column])
                                plt.xlabel("Temperature °C")
                                plt.ylabel("dF/dT")
                                plt.legend(
                                    labels=melt_converted_data.columns[1:], loc="center left", bbox_to_anchor=(1, 0.5))
                                canvas_main_image = FigureCanvas(
                                    main_image_figure)
                                png_main_image = io.BytesIO()
                                canvas_main_image.print_png(png_main_image)
                                png_main_image.seek(0)
                                PIL_main_image = Image.open(png_main_image)
                                with tempfile.NamedTemporaryFile(delete=False) as f:
                                    PIL_main_image.save(
                                        f.name, format="PNG")
                                    temp_main_image = f.name
                                plt.close()
                                plt.clf()

                                ct_image_figure, ax = plt.subplots(
                                    figsize=(15, 10))
                                for column in ct_data.columns[1:]:
                                    ax.plot(
                                        ct_data.iloc[:, 0], ct_data[column])
                                plt.xlabel("Cycle Time")
                                plt.ylabel("Normalized Fluroscence")
                                plt.legend(labels=ct_data.columns[1:],
                                           loc="center left", bbox_to_anchor=(1, 0.5))
                                canvas_ct_image = FigureCanvas(
                                    ct_image_figure)
                                png_ct_image = io.BytesIO()
                                canvas_ct_image.print_png(png_ct_image)
                                png_ct_image.seek(0)
                                PIL_ct_image = Image.open(png_ct_image)
                                with tempfile.NamedTemporaryFile(delete=False) as f:
                                    PIL_ct_image.save(f.name, format="PNG")
                                    temp_ct_image = f.name
                                plt.close()
                                plt.clf()

                                # Create a PDF object
                                pdf = FPDF(
                                    format="A4", orientation="landscape")
                                pdf.add_page()
                                pdf.set_font("Arial", "B", 16)
                                pdf.cell(
                                    0, 10, "Microbiological Laboratory Research and Services", ln=True)
                                pdf.set_font("Arial", "", 10)
                                pdf.cell(
                                    0, 7, f"Patient Id: {self.selected_barcode}          Date: {datetime.now().date()}          Time: {datetime.now().strftime('%I:%M:%S %p')}", ln=True)
                                # pdf.cell(
                                #     0, 7, f"Date: {datetime.now().date()}", ln=True)
                                # pdf.cell(
                                #     0, 7, f"Time: {datetime.now().strftime('%I:%M:%S %p')}", ln=True)
                                pdf.set_font("Arial", "", 12)
                                pdf.ln(2)
                                pdf.set_font("Arial", "", 12)
                                pdf.cell(0, 10, "Melt Curve")
                                pdf.ln(8)
                                pdf.image(temp_main_image, x=1, y=None,
                                          w=280, h=150, type='PNG')
                                # pdf.ln(h=6)
                                pdf.add_page()
                                pdf.set_font("Arial", "", 12)
                                pdf.cell(0, 10, "Features", ln=True)
                                table = feature_data.copy()
                                table.rename(columns={"Temperature1": "Tm1", "Prominance1": "Prom1", "Take_of_Point1": "Top1", "Take_down_Point1": "Tdp1", "AUC1": "auc1",
                                                      "Temperature2": "Tm2", "Prominance2": "Prom2", "Take_of_Point2": "Top2", "Take_down_Point2": "Tdp2", "AUC2": "auc2"}, inplace=True)
                                pdf.ln(5)
                                total_table_width = 17 * len(table.columns)
                                x_center = (pdf.w - total_table_width) / 2
                                pdf.set_x(x_center)
                                for column in table.columns:
                                    pdf.set_font("Arial", "B", 9)
                                    pdf.cell(17, 10, column, 1, align="C")
                                pdf.ln(1.8)
                                for index, row in table.iterrows():
                                    pdf.ln(8)
                                    if row["Tm1"] == 0.0:
                                        pdf.set_text_color(r=255, g=0, b=0)
                                    else:
                                        pdf.set_text_color(r=0, g=0, b=0)
                                    pdf.set_x(x_center)
                                    pdf.cell(17, 8, str(row["Target"]), 1)
                                    pdf.cell(17, 8, str(
                                        round(row["Tm1"], 2)), 1)
                                    pdf.cell(17, 8, str(
                                        round(row['Width1'], 2)), 1)
                                    pdf.cell(17, 8, str(
                                        round(row['Prom1'], 2)), 1)
                                    pdf.cell(17, 8, str(
                                        round(row['Top1'], 2)), 1)
                                    pdf.cell(17, 8, str(
                                        round(row['Tdp1'], 2)), 1)
                                    pdf.cell(17, 8, str(
                                        round(row['auc1'], 2)), 1)
                                    pdf.cell(17, 8, str(
                                        round(row["Tm2"], 2)), 1)
                                    pdf.cell(17, 8, str(
                                        round(row['Width2'], 2)), 1)
                                    pdf.cell(17, 8, str(
                                        round(row['Prom2'], 2)), 1)
                                    pdf.cell(17, 8, str(
                                        round(row['Top2'], 2)), 1)
                                    pdf.cell(17, 8, str(
                                        round(row['Tdp2'], 2)), 1)
                                    pdf.cell(17, 8, str(
                                        round(row['auc2'], 2)), 1)

                                pdf.cell(17,8,"",0,ln=True)    
                                pdf.set_text_color(r=0, g=0, b=0)
                                pdf.ln(5)
                                pdf.set_font("Arial", "", 12)
                                pdf.cell(0, 10, "Tm Threshold", ln=True)
                                tm_data_path = os.path.join("data","Expected_Tm.xlsx")
                                tm_data = pd.read_excel(tm_data_path)

                                total_table_width = 24 * len(tm_data.columns)
                                x_center = (pdf.w - total_table_width) / 2

                                pdf.set_x(x_center)
                                for column in tm_data.columns:
                                    pdf.set_font("Arial", "B", 9)
                                    pdf.cell(24, 10, column, 1, align="C")
                                pdf.ln(1.8)
                                for index, row in tm_data.iterrows():
                                    pdf.ln(8)
                                    pdf.set_x(x_center)
                                    pdf.cell(24, 8, str(
                                        row["Target"]), 1, align="C")
                                    pdf.cell(24, 8, str(
                                        row["SP"]), 1, align="C")
                                    pdf.cell(24, 8, str(
                                        row["HI"]), 1, align="C")
                                    pdf.cell(24, 8, str(
                                        row["NM"]), 1, align="C")
                                    pdf.cell(24, 8, str(
                                        row["EV"]), 1, align="C")
                                    pdf.cell(24, 8, str(
                                        row["HSV 1"]), 1, align="C")
                                    pdf.cell(24, 8, str(
                                        row["HSV 2"]), 1, align="C")
                                    pdf.cell(24, 8, str(
                                        row["VZV"]), 1, align="C")
                                    pdf.cell(24, 8, str(
                                        row["CMV"]), 1, align="C")

                                pdf.add_page()
                                pdf.set_font("Arial", "", 12)
                                pdf.set_text_color(r=0, g=0, b=0)
                                pdf.cell(
                                    0, 10, "Amplification Curve", ln=True)
                                pdf.ln(4)
                                pdf.image(temp_ct_image, x=1, y=None,
                                          w=280, h=150, type='PNG')
                                # pdf.ln(h=6)
                                pdf.add_page()
                                pdf.cell(0, 10, "Features", ln=True)
                                total_table_width = 26 * \
                                    len(take_off.columns)
                                x_center = (pdf.w - total_table_width) / 2
                                pdf.set_x(x_center)
                                for column in take_off.columns:
                                    pdf.set_font("Arial", "B", 9)
                                    pdf.cell(26, 8, column, 1, align="C")

                                for index, row in take_off.iterrows():
                                    pdf.ln(8)
                                    if row["Status"] == "Noise":
                                        pdf.set_text_color(r=255, g=0, b=0)
                                    else:
                                        pdf.set_text_color(r=0, g=0, b=0)
                                    pdf.set_x(x_center)
                                    pdf.cell(26, 8, str(
                                        row["Pathogen"]), 1)
                                    pdf.cell(26, 8, str(
                                        row["Take of Point"]), 1)
                                    pdf.cell(26, 8, str(
                                        round(row["Y- Coordiante"], 7)), 1)
                                    pdf.cell(26, 8, str(row["Status"]), 1)

                                # pdf.ln(h=10)
                                pdf.add_page()
                                pdf.set_text_color(r=0, g=0, b=0)
                                pdf.set_font("Arial", "", 12)
                                pdf.cell(0, 10, "Result", ln=True)
                                total_table_width = 70 * \
                                    len(result.columns)
                                x_center = (pdf.w - total_table_width) / 2
                                pdf.set_x(x_center)

                                for column in result.columns:
                                    pdf.set_font("Arial", "B", 9)
                                    pdf.cell(70, 8, column, 1, align="C")

                                for index, row in result.iterrows():
                                    pdf.ln(8)
                                    if row["Result"] == "Not Detected":
                                        pdf.set_text_color(r=0, g=128, b=0)
                                    else:
                                        pdf.set_text_color(r=255, g=0, b=0)
                                    pdf.set_x(x_center)
                                    pdf.cell(70, 8, str(
                                        row['Pathogens']), 1)
                                    pdf.cell(70, 8, str(row['Result']), 1)

                                pdf_bytes = pdf.output(
                                    dest='S').encode('latin-1')
                                return pdf_bytes

                            if not any(result in self.result['Result'].values for result in ["Need Manual Interpretation (Check Tm Value)", "Need Verfication (Check Ct value)"]):
                                report_generation, software_result = st.columns([
                                    5, 5])

                                st.caption(
                                    "*Note: Update the features to database if Software Interpretation is correct. Otherwise Update the features after Manual Interpretation*")

                                with software_result:
                                    update_result_button = st.empty()

                                    if update_result_button.button("Update Result"):
                                        original_feature_barcode = [
                                            self.selected_barcode for i in range(len(original_feature))]
                                        original_feature.insert(
                                            0, "Barcode", original_feature_barcode)
                                        for column in original_feature.columns:
                                            if column == "Barcode":
                                                original_feature[column] = original_feature[column].astype(
                                                    float)
                                            elif column in original_feature.columns[2:16]:
                                                original_feature[column] = original_feature[column].astype(
                                                    float)
                                            else:
                                                original_feature[column] = original_feature[column].astype(
                                                    object)
                                                continue

                                        conn = st.connection(
                                            "gsheets", type=GSheetsConnection)
                                        existing_data = conn.read(
                                            spreadsheet=gsheet_url, worksheet="Original Features", usecols=list(range(17)), ttl=5)
                                        existing_data = existing_data.dropna(
                                            how="all")
                                        combined_data = pd.concat(
                                            [existing_data, original_feature], ignore_index=True)
                                        combined_data['Barcode'] = combined_data['Barcode'].apply(
                                            lambda x: str(x))

                                        existing_barcode = existing_data[existing_data['Barcode'] == float(
                                            self.selected_barcode)].reset_index(drop=True)
                                        existing_barcode_remaining = existing_data[existing_data['Barcode'] != float(
                                            self.selected_barcode
                                        )]

                                        if existing_barcode.equals(original_feature):
                                            st.warning(
                                                "Already Updated")

                                        elif (existing_barcode.equals(original_feature) == False):
                                            conn.clear(
                                                worksheet="Original Features")
                                            conn.update(
                                                worksheet="Original Features", data=combined_data)
                                            success_slot = st.empty()
                                            success_slot.success(
                                                "Details Updated Successfully")
                                            time.sleep(1)
                                            success_slot.empty()
                                            update_result_button.empty()

                                with report_generation:
                                    if st.button("Generate Report"):
                                        pdf_bytes = report(self.melt_converted_data, self.ct_data_read,
                                                           self.extracted_features, self.take_off, self.result)
                                        st.download_button(
                                            "Download", data=pdf_bytes, file_name=f"{self.selected_barcode}.pdf", mime="application/pdf")

                            if 'IC' in self.extracted_features['Target'].values:
                                ic_row = self.extracted_features[self.extracted_features["Target"] == "IC"]
                                ic_temperature1 = ic_row["Temperature1"].values[0]
                                if 83 < ic_temperature1 < 85:
                                    st.success("IC Passed")
                                else:
                                    st.error("IC Failed")
                            else:
                                st.warning("IC Not Found")

                        with update_result:
                            if self.result.empty:
                                st.warning(
                                    "MEP Not Found (or) Check Pathogens Naming Conventions")
                            else:
                                password = credentials["credentials"]["usernames"]["admin"]["password"]
                                if "permission_granted" not in st.session_state:
                                    st.session_state.permission_granted = False

                                if st.session_state.permission_granted == False:
                                    access_id = st.text_input(
                                        "Access ID to Change results", type="password")
                                    if st.button("Login"):
                                        if access_id is not None:
                                            if access_id == password:
                                                st.session_state.permission_granted = True
                                                st.rerun()

                                        if access_id == "":
                                            st.warning(
                                                "Enter your Access ID")

                                        elif access_id != password:
                                            st.session_state.permission_granted = False
                                            st.error("Incorrect Password")

                                if st.session_state.permission_granted:
                                    updated_result = st.data_editor(
                                        self.result,
                                        use_container_width=True,
                                        column_config={
                                            "Result": st.column_config.SelectboxColumn(
                                                "Manual Result",
                                                help="Result of Pathogen",
                                                options=[
                                                    "Detected",
                                                    "Not Detected",
                                                    "Need Verfication (Check Ct value)",
                                                    "Need Manual Interpretation (Check Tm Value)"
                                                ],
                                                required=True
                                            )
                                        },
                                        hide_index=True
                                    )

                                    if st.button("Update Results"):
                                        feature_data['Result'] = self.result["Result"]
                                        feature_data['Manual Result'] = updated_result["Result"]
                                        self.result['Result'] = updated_result['Result']
                                        barcode_data = [
                                            self.selected_barcode for i in range(0, len(feature_data))]
                                        feature_data.insert(
                                            0, "Barcode", barcode_data)
                                        conn = st.connection(
                                            "gsheets", type=GSheetsConnection)
                                        existing_data = conn.read(
                                            spreadsheet=gsheet_url, worksheet="Mep Features", usecols=list(range(18)), ttl=5)
                                        existing_data = existing_data.dropna(
                                            how="all")

                                        combined_data = pd.concat(
                                            [existing_data, feature_data], ignore_index=True)

                                        existing_data['Barcode'] = existing_data['Barcode'].apply(
                                            lambda x: str(x))

                                        for column in feature_data.columns:
                                            if column in feature_data.columns[2:16]:
                                                feature_data[column] = feature_data[column].astype(
                                                    float)
                                            elif column == "Barcode":
                                                feature_data[column] = feature_data[column].astype(
                                                    float)

                                            elif column in ["Target", "Result", "Manual Result"]:
                                                feature_data[column] = feature_data[column].astype(
                                                    object)

                                        for column in existing_data.columns:
                                            if column == "Barcode":
                                                existing_data[column] = existing_data[column].astype(
                                                    float)
                                            else:
                                                continue
                                        existing_exceptional_feature = existing_data[existing_data['Barcode'] == float(
                                            self.selected_barcode)].reset_index(drop=True)

                                        existing_exceptional_feature_remaining = existing_data[existing_data['Barcode'] != float(
                                            self.selected_barcode)]

                                        if existing_exceptional_feature.iloc[:, 0:].equals(feature_data.iloc[:, 0:]):
                                            st.warning(
                                                f"{self.selected_barcode} Details already Updated")

                                        elif (existing_exceptional_feature.iloc[:, 0:17].equals(feature_data.iloc[:, 0:17])) and (existing_exceptional_feature.iloc[:, 17].equals(feature_data.iloc[:, 17]) == False):
                                            updated_feature_data = pd.concat(
                                                [existing_exceptional_feature_remaining, feature_data])
                                            conn.clear(
                                                worksheet="Mep Features")
                                            conn.update(
                                                worksheet="Mep Features", data=updated_feature_data)
                                            st.success(
                                                f"{self.selected_barcode} Details Modified")
                                        elif (existing_exceptional_feature.iloc[:, 0:17].equals(feature_data.iloc[:, 0:17]) == False) and (existing_exceptional_feature.iloc[:, 17].equals(feature_data.iloc[:, 17]) == False):
                                            conn.clear(
                                                worksheet="Mep Features")
                                            conn.update(
                                                worksheet="Mep Features", data=combined_data)
                                            st.success(
                                                f"{self.selected_barcode} Details successfully added!")

                                        pdf_bytes = report(self.melt_converted_data, self.ct_data_read,
                                                           self.extracted_features, self.take_off, self.result)
                                        st.download_button(
                                            "Download Report", data=pdf_bytes, file_name=f"{self.selected_barcode}.pdf", mime="application/pdf")

                                    if st.button("Logout"):
                                        st.session_state.permission_granted = False
                                        st.rerun()

                        with view_ghseet:
                            if st.session_state.permission_granted:
                                conn = st.connection(
                                    "gsheets", type=GSheetsConnection)
                                existing_data = conn.read(
                                    spreadsheet=gsheet_url, worksheet="Mep Features", usecols=list(range(18)), ttl=5)
                                existing_data = existing_data.dropna(
                                    how="all")
                                existing_data['Barcode'] = existing_data['Barcode'].apply(
                                    lambda x: str(x).split(".")[0])
                                st.dataframe(
                                    existing_data, hide_index=True)
                            else:
                                st.info("Login to see updated features")

            else:
                st.error(
                    "Unsupported file format! Please upload files with the .rex extension only.")


if 'login' not in st.session_state:
    st.session_state.login = False

col1, col2, col3 = st.columns([4, 7, 4])


if not st.session_state.get('login'):
    with col2:
        st.markdown(
            """
            <br><br>
            <div align='center'>
                <h1><span style='color: #00ABE4;'>Login</span></h1>
            </div>
            """, unsafe_allow_html=True)

        st.markdown(
            """
            <style>
                #MainMenu {
                    visibility: visible;
                }
            </style>
            """, unsafe_allow_html=True
        )

        with st.form("Login"):
            username = st.text_input(":blue[Username]")
            password = st.text_input(
                ":blue[Password]", type="password")
            submit = st.form_submit_button(":blue[Submit]")

            if submit:
                if (username == credentials["credentials"]['usernames']['mlrs_user']['name']) and (password == credentials["credentials"]['usernames']['mlrs_user']['password']):
                #if (username in credentials["credentials"]['usernames']) and (password == credentials["credentials"]['usernames'][username]['password']):
                    st.session_state.login = True
                    st.success("Login Sucessfull")
                    st.rerun()

                elif (username == "") or (password == ""):
                    st.error("Username/Password is missing!")

                else:
                    st.error("Incorrect username or password!")

if st.session_state.get('login'):
    with st.sidebar:
        st.markdown("""
                    <html>
                    <head>
                    <style type="text/css">
                        .glow {
                            -webkit-animation-duration: 1s;
                            -webkit-animation-name: glow;
                            -webkit-animation-direction: alternate;
                            -webkit-animation-iteration-count: infinite;
                            animation-duration: 0.5s;
                            animation-name: glow;
                            animation-direction: alternate;
                            animation-iteration-count: infinite;  
                        }
                        @-webkit-keyframes glow {
                            from { text-shadow: 0 0 0px red; }
                            to { text-shadow: 0 0 20px red; }
                        }
                    </style>
                    </head>
                    <body>
                    <h1 class="glow">Pathogen Detector</h1>
                    </body>
                    </html>
                    """, unsafe_allow_html=True)
    #     page_option = option_menu(menu_title=None, options=[
    #                               "Interpreter"], icons=[" "])
    # if page_option == "Interpreter":
    obj = Pathogen_Detector()
    obj.Interpreter()

    with st.sidebar:
        logout = st.button(label="Logout", key="logout_key")
        if logout:
            st.session_state.clear()
            st.rerun()
