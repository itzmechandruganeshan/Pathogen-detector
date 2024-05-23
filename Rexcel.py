import pandas as pd
import xml.etree.ElementTree as ET


class Rextractor:
    def __init__(self, file):
        self.amplification_data = []
        self.HRM_data = []
        self.count_ct = []
        self.temp_value = []
        self.minxpoint = None
        self.startx = None
        self.stepx = None
        self.master_ct = []
        self.master_hrm = []
        if file is not None:
            self.data = file.read()

        # Parse the XML content
        self.Element = ET.fromstring(self.data)

    def Amplification(self):
        if self.Element[19].tag == "RawChannels":
            for i, Raw_channel in enumerate(self.Element[19]):
                if i == 0:
                    if Raw_channel.find("Name").text == "Cycling A.Green":
                        self.count_ct = [i for i in range(int(Raw_channel.find(
                            "StartX").text), int(Raw_channel.find("MinXPoints").text)+1)]
                        readings = Raw_channel.findall("Reading")
                        for i, reading in enumerate(readings):
                            reading_data = reading.text
                            reading_data = reading_data.split(" ")
                            reading_data = [float(value)
                                            for value in reading_data]
                            self.amplification_data.append(reading_data)

                        for count in range(len(self.amplification_data)):
                            self.master_ct.append(self.count_ct)

        elif self.Element[18].tag == "RawChannels":
            for i, Raw_channel in enumerate(self.Element[18]):
                if i == 0:
                    if Raw_channel.find("Name").text == "Cycling A.Green":
                        self.count_ct = [i for i in range(int(Raw_channel.find(
                            "StartX").text), int(Raw_channel.find("MinXPoints").text)+1)]
                        readings = Raw_channel.findall("Reading")
                        for i, reading in enumerate(readings):
                            reading_data = reading.text
                            reading_data = reading_data.split(" ")
                            reading_data = [float(value)
                                            for value in reading_data]
                            self.amplification_data.append(reading_data)

                        for count in range(len(self.amplification_data)):
                            self.master_ct.append(self.count_ct)

        return self.master_ct, self.amplification_data

    def HRM(self):
        if self.Element[19].tag == "RawChannels":
            for i, Raw_channel in enumerate(self.Element[19]):
                if i == 1:
                    if Raw_channel.find("Name").text == "HRM A.HRM":
                        self.minxpoint = Raw_channel.find("MinXPoints").text
                        self.startx = Raw_channel.find("StartX").text
                        self.stepx = Raw_channel.find("StepX").text
                        self.temp_value = [
                            int(self.startx) + i * float(self.stepx) for i in range(int(self.minxpoint)-1)]
                        readings = Raw_channel.findall("Reading")
                        for j, reading in enumerate(readings):
                            reading_data = reading.text
                            reading_data = reading_data.split(" ")
                            reading_data = [float(value)
                                            for value in reading_data]
                            self.HRM_data.append(reading_data)
                        for count in range(len(self.HRM_data)):
                            self.master_hrm.append(self.temp_value)

        elif self.Element[18].tag == "RawChannels":
            for i, Raw_channel in enumerate(self.Element[18]):
                if i == 1:
                    if Raw_channel.find("Name").text == "HRM A.HRM":
                        self.minxpoint = Raw_channel.find("MinXPoints").text
                        self.startx = Raw_channel.find("StartX").text
                        self.stepx = Raw_channel.find("StepX").text
                        self.temp_value = [
                            int(self.startx) + i * float(self.stepx) for i in range(int(self.minxpoint)-1)]
                        readings = Raw_channel.findall("Reading")
                        for j, reading in enumerate(readings):
                            reading_data = reading.text
                            reading_data = reading_data.split(" ")
                            reading_data = [float(value)
                                            for value in reading_data]
                            self.HRM_data.append(reading_data)
                        for count in range(len(self.HRM_data)):
                            self.master_hrm.append(self.temp_value)
        return self.master_hrm, self.HRM_data

    def Sample_details(self):
        if self.Element[16].tag == "Samples":
            Ct = []
            HRM = []
            Page = self.Element[16].find("Page")
            sample_id = Page.findall("Sample")

            for i, Raw_channel in enumerate(self.Element[19]):
                if Raw_channel.find("Name").text == "Cycling A.Green":
                    self.StartX = int(Raw_channel.find("StartX").text)
                    self.MinXPoints = int(Raw_channel.find("MinXPoints").text)
                    self.stepx = float(Raw_channel.find("StepX").text)

                elif Raw_channel.find("Name").text == "HRM A.HRM":
                    self.StartX = int(Raw_channel.find("StartX").text)
                    self.MinXPoints = int(Raw_channel.find("MinXPoints").text)
                    self.stepx = float(Raw_channel.find("StepX").text)
                    for sample in sample_id:
                        id = sample.find("ID").text
                        Name = sample.find("Name").text
                        Text1 = []
                        Text2 = []
                        for count in range(int(self.Element[19].find("RawChannel").find("MinXPoints").text)):
                            Text1.append(f"{id}: {Name}")

                        for count in range(len([int(self.StartX) + i * float(self.stepx) for i in range(int(self.MinXPoints)-1)])):
                            Text2.append(f"{id}: {Name}")

                        Ct.append(Text1)
                        HRM.append(Text2)

                        del Text1
                        del Text2

        elif self.Element[15].tag == "Samples":
            Ct = []
            HRM = []
            Page = self.Element[15].find("Page")
            sample_id = Page.findall("Sample")

            for i, Raw_channel in enumerate(self.Element[18]):
                if Raw_channel.find("Name").text == "Cycling A.Green":
                    self.StartX = int(Raw_channel.find("StartX").text)
                    self.MinXPoints = int(Raw_channel.find("MinXPoints").text)
                    self.stepx = float(Raw_channel.find("StepX").text)

                elif Raw_channel.find("Name").text == "HRM A.HRM":
                    self.StartX = int(Raw_channel.find("StartX").text)
                    self.MinXPoints = int(Raw_channel.find("MinXPoints").text)
                    self.stepx = float(Raw_channel.find("StepX").text)
                    for sample in sample_id:
                        id = sample.find("ID").text
                        Name = sample.find("Name").text
                        Text1 = []
                        Text2 = []
                        for count in range(int(self.Element[18].find("RawChannel").find("MinXPoints").text)):
                            Text1.append(f"{id}: {Name}")

                        for count in range(len([int(self.StartX) + i * float(self.stepx) for i in range(int(self.MinXPoints)-1)])):
                            Text2.append(f"{id}: {Name}")

                        Ct.append(Text1)
                        HRM.append(Text2)

                        del Text1
                        del Text2
        return Ct, HRM


def HRM_data(file):
    try:
        obj = Rextractor(file)
        x_hrm, y_hrm = obj.HRM()
        _, sample_data_hrm = obj.Sample_details()
        dataframes = []
        for i, (Text, x, y) in enumerate(zip(sample_data_hrm, x_hrm, y_hrm)):
            df = pd.DataFrame({
                f"Text{i}": Text,
                f"X{i}": x,
                f"Y{i}": y
            })
            if Text[0].split(" ")[1] != "None":
                dataframes.append(df)

        concatenated_df = pd.concat(dataframes, axis=1)
        pathogens = ["HSV", "EV", "CMV", "VZV", "HI", "NM", "SP", "IC"]
        transformed_data = []
        targets = concatenated_df.iloc[0, :][0::3]
        targets = [target.split(" ")[-1] for target in targets]
        for i, target in enumerate(targets):
            for j, pathogen in enumerate(pathogens):
                if pathogen == target:
                    df = concatenated_df.iloc[:, [(3*i), (3*i)+1, (3*i)+2]]
                    transformed_data.append(df)

        mep_df = pd.concat(transformed_data, axis=1)
        seperate_dataframes = {}
        text_columns = mep_df.iloc[0, :][0::3]
        text_columns = [column.split(" ")[1] for column in text_columns]
        unique_barcode = list(set(text_columns))
        data_frames = []
        for i, barcode in enumerate(unique_barcode):
            for j, column in enumerate(text_columns):
                if barcode == column:
                    df = mep_df.iloc[:, [(3*j), (3*j)+1, (3*j)+2]]
                    data_frames.append(df)
            barcode_df = pd.concat(data_frames, axis=1)
            data_frames.clear()
            seperate_dataframes[barcode] = barcode_df

        return seperate_dataframes
    except:
        return None


def CT_Cycle(file):
    try:
        obj = Rextractor(file)
        x_ct, y_ct = obj.Amplification()
        sample_data_ct, _ = obj.Sample_details()
        dataframes = []
        for i, (Text, x, y) in enumerate(zip(sample_data_ct, x_ct, y_ct)):
            df = pd.DataFrame({
                f"Text{i}": Text,
                f"X{i}": x,
                f"Y{i}": y
            })
            if Text[0].split(" ")[1] != "None":
                dataframes.append(df)

        concatenated_df = pd.concat(dataframes, axis=1)
        pathogens = ["HSV", "EV", "CMV", "VZV", "HI", "NM", "SP", "IC"]
        transformed_data = []
        targets = concatenated_df.iloc[0, :][0::3]
        targets = [target.split(" ")[-1] for target in targets]
        for i, target in enumerate(targets):
            for j, pathogen in enumerate(pathogens):
                if pathogen == target:
                    df = concatenated_df.iloc[:, [(3*i), (3*i)+1, (3*i)+2]]
                    transformed_data.append(df)

        mep_df = pd.concat(transformed_data, axis=1)
        seperate_dataframes = {}
        text_columns = mep_df.iloc[0, :][0::3]
        text_columns = [column.split(" ")[1] for column in text_columns]
        unique_barcode = list(set(text_columns))
        data_frames = []
        for i, barcode in enumerate(unique_barcode):
            for j, column in enumerate(text_columns):
                if barcode == column:
                    df = mep_df.iloc[:, [(3*j), (3*j)+1, (3*j)+2]]
                    data_frames.append(df)
            barcode_df = pd.concat(data_frames, axis=1)
            data_frames.clear()
            seperate_dataframes[barcode] = barcode_df

        return seperate_dataframes
    except:
        return None
