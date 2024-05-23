# Importing the necassary packages
import pandas as pd
import numpy as np
import scipy
import matplotlib.pyplot as plt
import io
import tempfile
from PIL import Image
from matplotlib.backends.backend_agg import FigureCanvas
from datetime import datetime
from scipy.signal import find_peaks, peak_prominences, peak_widths
from scipy.signal import savgol_filter
from fpdf import FPDF
from scipy.integrate import simps
from sklearn.linear_model import LinearRegression
pd.set_option('mode.chained_assignment', None)


class PyMicro:
    def __init__(self):
        self.HRM_data = pd.DataFrame()
        self.melt_converted_data = pd.DataFrame()
        self.threshold_data = pd.read_excel("Threshold_data.xlsx")
        self.features = pd.DataFrame()
        self.xaxis = []
        self.take_off_points = []
        self.pathogens = []
        self.status = []
        self.y_coordinates = []
        self.xaxis_ct = []
        self.ct_result = pd.DataFrame()
        self.ct = pd.DataFrame()
        self.start_value = None
        self.end_value = None
        self.space = None
        self.melt_result = None

    def data_read(self, dataframe):
        data = dataframe
        pathogens = [pathogen.split(" ")[-1]
                     for pathogen in data.iloc[:, 0::3].iloc[0].to_list()]
        for column, pathogen in zip(data.iloc[:, 2::3].columns, pathogens):
            data.rename(columns={column: pathogen}, inplace=True)
        data.drop(columns=data.iloc[:, 0::3].columns.append(
            data.iloc[:, 4::3].columns), inplace=True)
        x_column_name = data.columns[0]
        data.rename(columns={x_column_name: "X"}, inplace=True)
        self.HRM_data = data

        for column in self.HRM_data.columns[1:]:
            raw_data = self.HRM_data[column].values
            smoothed_data = savgol_filter(
                raw_data, window_length=13, polyorder=3, mode='nearest')
            self.HRM_data[column] = smoothed_data

        return self.HRM_data

    def ct_read(self, dataframe):
        data = dataframe
        pathogens = [pathogen.split(" ")[-1]
                     for pathogen in data.iloc[:, 0::3].iloc[0].to_list()]
        for column, pathogen in zip(data.iloc[:, 2::3].columns, pathogens):
            data.rename(columns={column: pathogen}, inplace=True)
        data.drop(columns=data.iloc[:, 0::3].columns.append(
            data.iloc[:, 4::3].columns), inplace=True)
        x_column_name = data.columns[0]
        data.rename(columns={x_column_name: "X"}, inplace=True)
        self.ct = data

        def moving_average(data):
            moving_avg = np.zeros(len(data))
            moving_avg[0] = (data[0] + data[1]) / 2
            for i in range(1, len(data) - 1):
                moving_avg[i] = (data[i-1] + data[i] + data[i+1]) / 3
            moving_avg[-1] = (data[-2] + data[-1]) / 2
            return moving_avg

        for column in self.ct.columns[1:]:
            data = moving_average(self.ct[column].values)
            self.ct[column] = (data/data[0:15].mean() - 1)/10

        for column in self.ct.columns[1:]:
            raw_data = self.ct[column].values
            smoothed_data = savgol_filter(
                raw_data, window_length=13, polyorder=3, mode='nearest')
            self.ct[column] = smoothed_data

        return self.ct

    def convert_to_melt(self):
        HRM_data = self.HRM_data.copy()

        for i, column in enumerate(HRM_data.columns[1:]):
            diff = np.gradient(HRM_data.iloc[:, i+1], HRM_data.iloc[:, 0])
            HRM_data[column] = -diff/10

        difference = HRM_data.iloc[1, 0] - HRM_data.iloc[0, 0]
        self.start_value = HRM_data.iloc[0, 0] + round(difference, 2)/2
        self.end_value = HRM_data.iloc[-1, 0] - round(difference, 2)/2
        self.space = round(difference, 2)/3

        while self.start_value <= self.end_value:
            self.xaxis.append(self.start_value)
            self.start_value += self.space

        melt_dataframe = pd.DataFrame(columns=HRM_data.columns)
        melt_dataframe.iloc[:, 0] = self.xaxis

        for i, column in enumerate(HRM_data.columns[1:]):
            interpolating = scipy.interpolate.splrep(
                HRM_data.iloc[:, 0], HRM_data.iloc[:, i+1], s=0.031)
            melt_dataframe[melt_dataframe.columns[i+1]
                           ] = scipy.interpolate.splev(self.xaxis, interpolating)
        self.melt_converted_data = melt_dataframe

        return self.melt_converted_data

    def extraction(self):
        feature_data = pd.DataFrame(columns=["Target", "Temperature1", "Width1", "Prominance1", "Take_of_Point1", "Take_down_Point1", "AUC1",
                                    "Temperature2", "Width2", "Prominance2", "Take_of_Point2", "Take_down_Point2", "AUC2"])

        for i, column in enumerate(self.melt_converted_data.columns[1:]):
            peaks, _ = find_peaks(self.melt_converted_data.iloc[:, i+1])
            prominences = peak_prominences(
                self.melt_converted_data.iloc[:, i+1], peaks)[0]
            d_prominences = np.argsort(prominences)[::-1][:2]
            peaks = [peaks[i] for i in d_prominences]
            prominance_value = [
                self.melt_converted_data.iloc[:, i+1][prom] for prom in peaks]
            peak_temp = [self.melt_converted_data.iloc[:, 0][j] for j in peaks]
            width_data = np.array(peak_widths(
                self.melt_converted_data.iloc[:, i+1], peaks, rel_height=0.75)).T

            if len(width_data) == 2:
                peak1, peak2 = width_data
                auc1 = simps(self.melt_converted_data.iloc[int(peak1[2]):int(peak1[3]), i+1].to_numpy(),
                             self.melt_converted_data.iloc[int(peak1[2]):int(peak1[3]), 0].to_numpy())

                auc2 = simps(self.melt_converted_data.iloc[int(peak2[2]):int(peak2[3]), i+1].to_numpy(),
                             self.melt_converted_data.iloc[int(peak2[2]):int(peak2[3]), 0].to_numpy())

                peak1[2:4] = [self.melt_converted_data.iloc[:, 0]
                              [int(index)] for index in peak1[2:4]]
                peak2[2:4] = [self.melt_converted_data.iloc[:, 0]
                              [int(index)] for index in peak2[2:4]]
                if np.min(prominance_value) >= (np.max(prominance_value) * 0.2):
                    prominance_value[1] = prominance_value[1]
                else:
                    peak_temp[1], peak2[0], prominance_value[1], peak2[2], peak2[3], auc2 = 0, 0, 0, 0, 0, 0

                feature_data.loc[i, :] = [column, peak_temp[0], peak1[0], prominance_value[0], peak1[2],
                                          peak1[3], auc1, peak_temp[1], peak2[0], prominance_value[1], peak2[2], peak2[3], auc2]

            elif len(width_data) == 1:
                peak1 = width_data[0]
                auc1 = simps(self.melt_converted_data.iloc[int(peak1[2]):int(peak1[3]), i+1].to_numpy(),
                             self.melt_converted_data.iloc[int(peak1[2]):int(peak1[3]), 0].to_numpy())

                peak1[2:4] = [self.melt_converted_data.iloc[:, 0]
                              [int(index)] for index in peak1[2:4]]
                feature_data.loc[i, :] = [column, peak_temp[0], peak1[0],
                                          prominance_value[0], peak1[2], peak1[3], auc1, 0, 0, 0, 0, 0, 0]

            else:
                feature_data.loc[i, :] = [column, 0,
                                          0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

        self.features = feature_data

        return self.features

    def take_off(self):
        ct_data = self.ct
        for column in ct_data.columns[1:]:
            X = ct_data.iloc[:, 0].values.reshape(-1, 1)
            y = ct_data[column].values
            model = LinearRegression()
            model.fit(X, y)
            pred_y = model.predict(X)
            difference = pred_y - y
            take_off_index = np.argmax(pred_y - y)
            positive_values = np.where(difference > 0)[0]
            if y[take_off_index] >= 0:
                self.pathogens.append(column)
                self.take_off_points.append(int(X[take_off_index]))
                self.y_coordinates.append(float(y[take_off_index]))
                if y[-1] < 0.043:
                    self.status.append("Noise")
                else:
                    self.status.append("Normal")

            elif y[take_off_index] < 0:
                for idx in range(take_off_index, positive_values[-1]):
                    if y[idx] > 0:
                        self.pathogens.append(column)
                        self.take_off_points.append(int(X[idx]))
                        self.y_coordinates.append(float(y[idx]))
                        if y[-1] < 0.043:
                            self.status.append(f"Noise")
                        else:
                            self.status.append("Normal")
                        break

            df = pd.DataFrame()
            df['Pathogen'] = self.pathogens
            df['Take of Point'] = self.take_off_points
            df['Y- Coordiante'] = self.y_coordinates
            df['Status'] = self.status
            self.ct_result = df

        return self.ct_result

    def logical_result(self):
        self.result = {}
        for Tm1, Tm2, column in zip(self.features.iloc[:, 1], self.features.iloc[:, 7], self.features.iloc[:, 0]):
            for min_threshold, max_threshold, short_name in zip(self.threshold_data.iloc[:, 2].values, self.threshold_data.iloc[:, 3].values, self.threshold_data.iloc[:, 1].values):
                if column == short_name:
                    if short_name == "HSV":
                        if (82 <= Tm1 <= 84) or (82 <= Tm2 <= 84):
                            self.result[column] = "Detected"
                        elif (85 <= Tm1 <= 87) or (85 <= Tm2 <= 87):
                            self.result[column] = "Detected"
                        elif (81 <= Tm1 <= 81.99) or (81 <= Tm2 <= 81.99):
                            self.result[column] = "Need Manual Interpretation (Check Tm Value)"
                        elif (84 < Tm1 <= 84.99) or (84 < Tm2 <= 84.99):
                            self.result[column] = "Need Manual Interpretation (Check Tm Value)"
                        elif (87 < Tm1 <= 87.99) or (87 < Tm2 <= 87.99):
                            self.result[column] = "Need Manual Interpretation (Check Tm Value)"
                        else:
                            self.result[column] = "Not Detected"
                    if short_name == "NM":
                        if (78 <= Tm1 <= 82) or (78 <= Tm2 <= 82):
                            self.result[column] = "Detected"
                        elif (77 <= Tm1 <= 77.99) or (77 <= Tm2 <= 77.99):
                            self.result[column] = "Need Manual Interpretation (Check Tm Value)"
                        elif (82 < Tm1 <= 82.99) or (82 < Tm2 <= 82.99):
                            self.result[column] = "Need Manual Interpretation (Check Tm Value)"
                        else:
                            self.result[column] = "Not Detected"
                    else:
                        if (min_threshold <= Tm1 <= max_threshold) or (min_threshold <= Tm2 <= max_threshold):
                            self.result[column] = "Detected"
                        elif (min_threshold-1 <= Tm1 < min_threshold) or (min_threshold-1 <= Tm2 < min_threshold):
                            self.result[column] = "Need Manual Interpretation (Check Tm Value)"
                        elif (max_threshold < Tm1 < max_threshold+1) or (max_threshold < Tm2 < max_threshold+1):
                            self.result[column] = "Need Manual Interpretation (Check Tm Value)"
                        else:
                            self.result[column] = "Not Detected"
                else:
                    continue

        self.melt_result = pd.DataFrame(
            {"Pathogens": self.result.keys(), "Result": self.result.values()})
        return self.melt_result

    def model_result(self):
        model_result = []
        original_variable = {}
        result_dataframe = pd.DataFrame(columns=['Pathogens', "Result"])
        model = pd.read_pickle("random_forest_model_ct.pkl")
        dummy_variable = {"EV": 0, "HI": 1, "HSV": 2,
                          "CMV": 3, "NM": 4, "VZV": 5, "SP": 6}
        feature_data = self.features.copy()
        ct_result = self.ct_result.copy()
        melt_result = self.melt_result.copy()
        feature_data['Ct'] = [i for i in range(0, len(feature_data['Target']))]
        feature_data['CT threshold'] = [
            i for i in range(0, len(feature_data['Target']))]
        for i, (target, pathogen) in enumerate(zip(feature_data["Target"], ct_result["Pathogen"])):
            if target == pathogen:
                feature_data['Ct'][i] = ct_result['Take of Point'][i]
                feature_data['CT threshold'][i] = ct_result["Y- Coordiante"][i]
            else:
                feature_data['CT threshold'][i] = 0
                feature_data["Ct"][i] = 40

        feature_data = feature_data[feature_data["Target"] != "IC"]
        feature_data_ = feature_data.copy()
        feature_data['Target'] = feature_data['Target'].map(dummy_variable)

        for index, row in feature_data.iterrows():
            result = model.predict(
                [[row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[13]]])[0]
            model_result.append(result)

        for key, value in dummy_variable.items():
            original_variable[value] = key

        result_dataframe["Pathogens"] = feature_data["Target"].map(
            original_variable)
        result_dataframe['Result'] = ["Detected" if result_ ==
                                      "P" else "Not Detected" for result_ in model_result]
        for i, (logical_result, model_result, feature_ct) in enumerate(zip(melt_result["Result"], result_dataframe['Result'], feature_data["Ct"])):
            if logical_result == "Need Manual Interpretation (Check Tm Value)":
                result_dataframe['Result'][i] = "Need Manual Interpretation (Check Tm Value)"
            elif (logical_result == "Detected") and (30 <= feature_ct <= 35):
                result_dataframe["Result"][i] = "Need Verfication (Check Ct value)"
            elif (logical_result == "Not Detected"):
                result_dataframe["Result"][i] = "Not Detected"

        feature_data_['Result'] = result_dataframe['Result']
        return result_dataframe, feature_data_

    def report(self):
        melt_converted_data = self.melt_converted_data.copy()
        ct_data = self.ct.copy()

        main_image_figure, ax = plt.subplots(figsize=(10, 5))
        for column in melt_converted_data.columns[1:]:
            ax.plot(
                melt_converted_data.iloc[:, 0], melt_converted_data[column])
        plt.xlabel("Temperature °C")
        plt.ylabel("dF/dT")
        plt.legend(
            labels=melt_converted_data.columns[1:], loc="center left", bbox_to_anchor=(1, 0.5))
        canvas_main_image = FigureCanvas(main_image_figure)
        png_main_image = io.BytesIO()
        canvas_main_image.print_png(png_main_image)
        png_main_image.seek(0)
        PIL_main_image = Image.open(png_main_image)
        with tempfile.NamedTemporaryFile(delete=False) as f:
            PIL_main_image.save(f.name, format="PNG")
            temp_main_image = f.name
        plt.close()
        plt.clf()

        ct_image_figure, ax = plt.subplots(figsize=(10, 5))
        for column in ct_data.columns[1:]:
            ax.plot(ct_data.iloc[:, 0], ct_data[column])
        plt.xlabel("Cycle Time")
        plt.ylabel("Normalized Fluroscence")
        plt.legend(labels=ct_data.columns[1:],
                   loc="center left", bbox_to_anchor=(1, 0.5))
        canvas_ct_image = FigureCanvas(ct_image_figure)
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
        pdf = FPDF(format="A4")
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "Microbiological Laboratory Report", ln=True)
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 7, f"Date: {datetime.now().date()}", ln=True)
        pdf.cell(
            0, 7, f"Time: {datetime.now().strftime('%I:%M:%S %p')}", ln=True)
        pdf.set_font("Arial", "", 12)
        pdf.ln(2)
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 10, "Melt Curve")
        pdf.ln(8)
        pdf.image(temp_main_image, x=1, y=None, w=200, h=100, type='PNG')
        pdf.ln(h=6)
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 10, "Features", ln=True)
        table = self.features.copy()
        table.rename(columns={"Temperature1": "Tm1", "Prominance1": "Prom1", "Take_of_Point1": "Top1", "Take_down_Point1": "Tdp1", "AUC1": "auc1",
                              "Temperature2": "Tm2", "Prominance2": "Prom2", "Take_of_Point2": "Top2", "Take_down_Point2": "Tdp2", "AUC2": "auc2"}, inplace=True)
        pdf.ln(5)
        total_table_width = 14 * len(table.columns)
        x_center = (pdf.w - total_table_width) / 2
        pdf.set_x(x_center)
        for column in table.columns:
            pdf.set_font("Arial", "B", 9)
            pdf.cell(14, 10, column, 1, align="C")
        pdf.ln(1.8)
        for index, row in table.iterrows():
            pdf.ln(8)
            if row["Tm1"] == 0.0:
                pdf.set_text_color(r=255, g=0, b=0)
            else:
                pdf.set_text_color(r=0, g=0, b=0)
            pdf.set_x(x_center)
            pdf.cell(14, 8, str(row["Target"]), 1)
            pdf.cell(14, 8, str(round(row["Tm1"], 2)), 1)
            pdf.cell(14, 8, str(round(row['Width1'], 2)), 1)
            pdf.cell(14, 8, str(round(row['Prom1'], 2)), 1)
            pdf.cell(14, 8, str(round(row['Top1'], 2)), 1)
            pdf.cell(14, 8, str(round(row['Tdp1'], 2)), 1)
            pdf.cell(14, 8, str(round(row['auc1'], 2)), 1)
            pdf.cell(14, 8, str(round(row["Tm2"], 2)), 1)
            pdf.cell(14, 8, str(round(row['Width2'], 2)), 1)
            pdf.cell(14, 8, str(round(row['Prom2'], 2)), 1)
            pdf.cell(14, 8, str(round(row['Top2'], 2)), 1)
            pdf.cell(14, 8, str(round(row['Tdp2'], 2)), 1)
            pdf.cell(14, 8, str(round(row['auc2'], 2)), 1)
        pdf.add_page()
        pdf.set_font("Arial", "", 12)
        pdf.set_text_color(r=0, g=0, b=0)
        pdf.cell(0, 10, "Amplification Curve", ln=True)
        pdf.ln(4)
        pdf.image(temp_ct_image, x=1, y=None, w=200, h=100, type='PNG')
        pdf.ln(h=6)
        pdf.cell(0, 10, "Features", ln=True)
        total_table_width = 26 * len(self.ct_result.columns)
        x_center = (pdf.w - total_table_width) / 2
        pdf.set_x(x_center)
        for column in self.ct_result.columns:
            pdf.set_font("Arial", "B", 9)
            pdf.cell(26, 8, column, 1, align="C")

        for index, row in self.ct_result.iterrows():
            pdf.ln(8)
            if row["Status"] == "Noise":
                pdf.set_text_color(r=255, g=0, b=0)
            else:
                pdf.set_text_color(r=0, g=0, b=0)
            pdf.set_x(x_center)
            pdf.cell(26, 8, str(row["Pathogen"]), 1)
            pdf.cell(26, 8, str(row["Take of Point"]), 1)
            pdf.cell(26, 8, str(round(row["Y- Coordiante"], 7)), 1)
            pdf.cell(26, 8, str(row["Status"]), 1)

        pdf_bytes = pdf.output(dest='S').encode('latin-1')

        return pdf_bytes
