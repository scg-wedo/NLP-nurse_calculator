import pandas as pd
from pythainlp.tokenize import word_tokenize
import openpyxl
import pandas as pd
import requests
from io import BytesIO
from pythainlp.util import text_to_arabic_digit

class extract:
    def __init__(self,spreadsheetId):
        self.spreadsheetid = spreadsheetId
        self.df = None
        self.df_dp = None
        self.df_id = None
        self.dict_dp = None
        self.df_price_id = None
        self.df_price_rm = None
        self.df_price_dis = None
        self.predict = None 
        self.conditions_id = None
        self.conditions_dp = None
        self.conditions_rm = None
        self.conditions_dis = None
        self.check_status = None
        self.conditions_frist_nickname = None
        self.conditions_name_department = None
        self.read_google_spreadsheet()
        self.predict_info(text)
        self.check_valid_prediction()
        self.request_info()


    def read_google_spreadsheet(self):
        url = "https://docs.google.com/spreadsheets/export?exportFormat=xlsx&id=" + self.spreadsheetid
        res = requests.get(url)
        data = BytesIO(res.content)
        xlsx = openpyxl.load_workbook(filename=data)
        self.df =  pd.read_excel(data, sheet_name="database")
        self.df_dp = pd.read_excel(data, sheet_name="dp_dict")
        self.df_id = pd.read_excel(data, sheet_name="identification")
        # load price data
        self.df_price_id = pd.read_excel(data, sheet_name="price_id")
        self.df_price_rm = pd.read_excel(data, sheet_name="price_rm")
        self.df_price_dis = pd.read_excel(data, sheet_name="price_dis")
        self.dict_dp=self.df_dp.to_dict()

    def predict_info(self,text):
        self.predict = ["-"] * len(self.df.columns)  # initialize prediction list with placeholders

        # Find the department in the dictionary
        for key, sub_dict in self.dict_dp.items():
            for sub_key, sub_value in sub_dict.items():
                if isinstance(sub_value, str) and sub_value in text:
                    self.predict[0] = key
                    break
            if self.predict[0] != "-":
                break

        # Find the values in the dataframe
        for i, column in enumerate(self.df.columns[1:]):
            for v in self.df[column]:
                if isinstance(v, str) and v in text:
                    self.predict[i+1] = v
                    break
        
    

    #condition
    #identify doctor/department/desease
    def check_valid_prediction(self):
        name = self.predict[2]
        nickname = self.predict[1]
        department = self.predict[0]
        disease = self.predict[4]
        roomtype = self.predict[5]
        number = self.predict[6]
        duration = self.predict[7] 
        self.conditions_id = (len(self.df_id[self.df_id['ชื่อจริง'] == name])==1) | (len(self.df_id[self.df_id['ชื่อเล่น'] == nickname])==1) | (len(self.df_id[(self.df_id['ชื่อจริง'] == name)&(self.df_id['ชื่อเล่น'] == nickname)])==1)| (len(self.df_id[(self.df_id['แผนก'] == department)&(self.df_id['ชื่อเล่น'] == nickname)])==1)| (len(self.df_id[(self.df_id['แผนก'] == department)&(self.df_id['ชื่อจริง'] == name)])==1)
        self.conditions_dp = (department != "-")
        self.conditions_rm = ((roomtype != "-") and (number != "-")) or ((roomtype == "-") and (number == "-") and (duration == "-"))
        self.conditions_dis = (disease != "-")
       
        if self.conditions_dp == True & self.conditions_id == True:
            if name  != '-'   &  nickname  != '-' :
                    self.conditions_frist_nickname = (self.df_id[(self.df_id['ชื่อจริง'] == name) & (self.df_id['ชื่อเล่น'] == nickname)].shape[0] == 1)
            self.conditions_name_department = (self.df_id[(self.df_id['ชื่อจริง'] == name) & (self.df_id['แผนก'] == department)].shape[0] == 1) | (self.df_id[(self.df_id['ชื่อเล่น'] == nickname) & (self.df_id['แผนก'] == department)].shape[0] == 1)
        else:
                self.conditions_frist_nickname = "can't check"
                self.conditions_name_department = "can't check"

        return(self.conditions_frist_nickname ,self.conditions_name_department)

    #request more information
    def request_info(self):
        info = self.df.columns.tolist()
        pred=[]
        response_ask = []

        if not self.conditions_dp:
            response_ask.append((info[0], 0))

        if not self.conditions_id:
            for i in range(1, 3):
                if self.predict[i] == "-":
                    response_ask.append((info[i], i))

        if not self.conditions_rm:
            for z in range(5, 8):
                if self.predict[z] == "-":
                    response_ask.append((info[z], z))

        if not self.conditions_dis:
            response_ask.append((info[4], 4))
        pred.append((self.predict,response_ask))
        return(pred)
        
spreadsheetId = "11Q8gRfwRHBkyIk6lAHKKTj7LySsOS2aU" # Please set your Spreadsheet ID.
text="คนไข้ท้องเสียรุนแรงรักษากับอาจารย์ทรงภูมิแผนกศัลยกรรม ให้น้ำเกลือพักห้องธรรมดาคืน"
information = extract(spreadsheetId)
information.predict_info(text)
pred = information.request_info()
error1,error2 = information.check_valid_prediction()
print(pred)
print(error1,error2)




# def update_predict(predict, response_ask, predict_2):
#     for i in range(len(response_ask)):
#         predict[response_ask[i][1]] = predict_2[response_ask[i][1]]
#     return predict
# predict = update_predict(predict, response_ask, predict_2)
# print(predict)

# class calculate(predict):
#     #calculator
#     def calculate_total_spend(predict):
        
#         # extract relevant information from prediction
#         name = predict[2]
#         nickname = predict[1]
#         disease = predict[4]
#         roomtype = predict[5]
#         number = predict[6]
#         duration = predict[7] 
        
#         # get price of id
#         p_id = df_price_id.loc[(df_price_id['ชื่อจริง'] == name) & (df_price_id['ชื่อเล่น'] == nickname), df_price_id.columns[-1]]

#         # get price of room
#         p_rm = df_price_rm.loc[df_price_rm['ห้องพัก'] == roomtype, df_price_rm.columns[-2]]
#         condition = {
#             1: duration in ["คืน", "วัน"],
#             7: duration == "สัปดาห์",
#             30: duration == "เดือน",
#             356: duration == "ปี",   
#         }
#         day = next(key for key, value in condition.items() if value)
#         p_rm *= int(text_to_arabic_digit(number)) * day

#         # get price of disease
#         p_dis = df_price_dis[df_price_dis[disease]==1]['ราคา'].sum()

#         # calculate total spend
#         total_spend = int(p_id) + int(p_rm) + int(p_dis)
        
#         return total_spend
