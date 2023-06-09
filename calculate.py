import pandas as pd
from pythainlp.tokenize import word_tokenize
import openpyxl
import pandas as pd
import requests
from io import BytesIO
from pythainlp.util import text_to_arabic_digit

class NurseCalculator:

    def __init__(self,spreadsheetId):
        self.spreadsheetid = spreadsheetId
        self.text_list=[]
        self.cls_response_ask=[]
        self.df = None
        self.df_dp = None
        self.df_id = None
        self.dict_dp = None
        self.predict = None 
        self.check_status = None
        self.response_ask = None
        self.pred = None
        self.total_spend = None
        self.response = None


    def read_google_spreadsheet(self):
        url = "https://docs.google.com/spreadsheets/export?exportFormat=xlsx&id=" + self.spreadsheetid
        res = requests.get(url)
        data = BytesIO(res.content)
        xlsx = openpyxl.load_workbook(filename=data)
        self.df =  pd.read_excel(data, sheet_name="database")
        self.df_dp = pd.read_excel(data, sheet_name="dp_dict")
        self.df_id = pd.read_excel(data, sheet_name="identification")
        # load price data
        df_price_id = pd.read_excel(data, sheet_name="price_id")
        df_price_rm = pd.read_excel(data, sheet_name="price_rm")
        df_price_dis = pd.read_excel(data, sheet_name="price_dis")
        self.dict_dp=self.df_dp.to_dict()
        return df_price_id,df_price_rm,df_price_dis
              
  
    def predict_info(self,text):
        self.text_list.append(text)

        text_concat=''
        for text in range(len(self.text_list)):
            text_concat = self.text_list[text]+text_concat
        self.predict = ["-"] * len(self.df.columns)# initialize prediction list with placeholders
        # Find the department in the dictionary
        for key, sub_dict in self.dict_dp.items():
            for sub_key, sub_value in sub_dict.items():
                if isinstance(sub_value, str) and sub_value in text_concat:
                    self.predict[0] = key
                    break
          

        # Find the values in the dataframe
        for i, column in enumerate(self.df.columns[1:]):
            for v in self.df[column]:
                if isinstance(v, str) and v in text_concat:
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
        conditions_id = (len(self.df_id[self.df_id['ชื่อจริง'] == name])==1) | (len(self.df_id[self.df_id['ชื่อเล่น'] == nickname])==1) | (len(self.df_id[(self.df_id['ชื่อจริง'] == name)&(self.df_id['ชื่อเล่น'] == nickname)])==1)| (len(self.df_id[(self.df_id['แผนก'] == department)&(self.df_id['ชื่อเล่น'] == nickname)])==1)| (len(self.df_id[(self.df_id['แผนก'] == department)&(self.df_id['ชื่อจริง'] == name)])==1)
        conditions_dp = (department != "-")
        conditions_rm = ((roomtype != "-") and (number != "-")) or ((roomtype != "-") and (number != "-") and (duration != "-"))
        conditions_dis = (disease != "-")
       
        
        if conditions_id:
            if name != '-' and nickname != '-':
                conditions_frist_nickname = (self.df_id[(self.df_id['ชื่อจริง'] == name) & (self.df_id['ชื่อเล่น'] == nickname)].shape[0] == 1)
            else:
                conditions_frist_nickname = True
        else:
            conditions_frist_nickname = "Can't check"

        if conditions_dp and conditions_id and (name != '-' or nickname != '-'):
            conditions_name_department = (self.df_id[(self.df_id['ชื่อจริง'] == name) & (self.df_id['แผนก'] == department)].shape[0] == 1) | (self.df_id[(self.df_id['ชื่อเล่น'] == nickname) & (self.df_id['แผนก'] == department)].shape[0] == 1)
        else:
            conditions_name_department = "Can't check"
        
        print(conditions_frist_nickname)
        

        return conditions_id,conditions_dp,conditions_rm,conditions_dis,conditions_frist_nickname,conditions_name_department
    #request more information
    def request_info(self,conditions_id,conditions_dp,conditions_rm,conditions_dis):
        info = self.df.columns.tolist()
        self.pred=[]
        self.response_ask = []

        if not conditions_dp:
            self.response_ask.append((info[0], 0,"แผนกที่เข้ารับการรักษา"))

        if not conditions_id:
            for i in range(1, 3):
                if self.predict[i] == "-":
                    if i == 1:
                        self.response_ask.append((info[i], i,"ชื่อเล่นคุณหมอ"))
                    if i == 2:
                        self.response_ask.append((info[i], i,"ชื่อจริงคุณหมอ"))

        if not conditions_rm:
            for z in range(5, 7):
                if self.predict[z] == "-":
                    if z == 5:
                        self.response_ask.append((info[z], z,"ประเภทของห้องพักฟื้น"))
                    if z == 6:
                        self.response_ask.append((info[z], z,"จำนวนระยะเวลาที่เข้าพัก"))

        if not conditions_dis:
            self.response_ask.append((info[4], 4,"โรคที่เข้ารับการรักษา"))
        self.pred.append((self.predict,self.response_ask))
        self.cls_response_ask.append(self.response_ask)
        print(self.pred)
        return(self.pred)
        

    
    def calculate_total_spend(self,df_price_id,df_price_rm,df_price_dis,conditions_frist_nickname,conditions_name_department):
        # extract relevant information from prediction
        name = self.predict[2]
        nickname = self.predict[1]
        department = self.predict[0]
        disease = self.predict[4]
        roomtype = self.predict[5]
        number = self.predict[6]
        duration = self.predict[7] 
        
        if self.response_ask == [] and conditions_frist_nickname == True and conditions_name_department == True:
            # get price of id
            if name != '-' and nickname != '-':
                p_id = df_price_id.loc[(df_price_id['แผนก'] == department) & (df_price_id['ชื่อจริง'] == name) & (df_price_id['ชื่อเล่น'] == nickname), df_price_id.columns[-1]]
            elif name != '-':
                p_id = df_price_id.loc[(df_price_id['แผนก'] == department) & (df_price_id['ชื่อจริง'] == name), df_price_id.columns[-1]]
            elif nickname != '-':
                p_id = df_price_id.loc[(df_price_id['แผนก'] == department) & (df_price_id['ชื่อเล่น'] == nickname), df_price_id.columns[-1]]
            
            # get price of room
            p_rm = df_price_rm.loc[df_price_rm['ห้องพัก'] == roomtype, df_price_rm.columns[-2]]
            condition = {
                1: duration in ["คืน", "วัน","-"],
                7: duration == "สัปดาห์",
                30: duration == "เดือน",
                356: duration == "ปี",   
            }
            day = next(key for key, value in condition.items() if value)
            p_rm *= int(text_to_arabic_digit(number)) * day
            
            # get price of disease
            p_dis = df_price_dis[df_price_dis[disease]==1]['ราคา'].sum()
            
            # calculate total spend
            self.total_spend = int(p_id) + int(p_rm) + int(p_dis)
            
            return self.total_spend 


    def response_back(self,conditions_frist_nickname,conditions_name_department):
        self.response = ''
        if not conditions_frist_nickname:
            self.response = "ไม่พบรายชื่อในฐานข้อมูล กรุณาระบุอีกครั้งนะคะ"
        elif not conditions_name_department:
            self.response = "ข้อมูลที่ระบุไม่ตรงกับฐานข้อมูล กรุณาระบุใหม่นะคะ"
        elif self.response_ask != [] and conditions_name_department is not False and conditions_frist_nickname is not False:
            for ask in range(len(self.response_ask)):
                if ask == 0:
                    self.response = "กรุณาระบุ" + self.response_ask[ask][2]
                else:
                   self.response += " " + self.response_ask[ask][2]
            self.response = self.response + "ค่ะ"
        elif self.response_ask == [] and conditions_name_department is True and conditions_frist_nickname is True:
            self.response = "ค่าใช้จ่ายเบื้องต้นอยู่ที่" + str(self.total_spend) + "ค่ะ"
        return self.response

    def reset(self):
        list_res_reset=['ไม่พบรายชื่อในฐานข้อมูล','ข้อมูลที่ระบุไม่ตรงกับฐานข้อมูล','ค่าใช้จ่าย']
        if any(reset in self.response for reset in list_res_reset):
            self.cls_response_ask = []
            self.text_list = []
            self.df = None
            self.df_dp = None
            self.df_id = None
            self.dict_dp = None
            self.predict = None 
            self.check_status = None
            self.response_ask = None
            self.pred = None
            self.total_spend = None
            self.response = None

    def func_all(self,text):
        df_price_id,df_price_rm,df_price_dis = self.read_google_spreadsheet()
        self.predict_info(text)
        conditions_id,conditions_dp,conditions_rm,conditions_dis,conditions_frist_nickname,conditions_name_department = self.check_valid_prediction()
        self.request_info(conditions_id,conditions_dp,conditions_rm,conditions_dis)
        self.calculate_total_spend(df_price_id, df_price_rm, df_price_dis,conditions_frist_nickname,conditions_name_department)
        response = self.response_back(conditions_frist_nickname,conditions_name_department)
        self.reset()
        return response

    
   
spreadsheetId = "11Q8gRfwRHBkyIk6lAHKKTj7LySsOS2aU" # Please set your Spreadsheet ID.
text= "คนไข้ ท้องเสียรุนแรง รักษา กับ อาจารย์ ให้ น้ำเกลือ พัก ห้อง ธรรมดา หนึ่ง คืน"
information = NurseCalculator(spreadsheetId)
res = information.func_all(text)
print(res)
text_2="อาจารย์ นลินญา แผนก เวชศาสตร์ ฉุกเฉิน"
res = information.func_all(text_2)
print(res)
text_3="อาจารย์หมอออมกชพรรณแผนกออร์โธผ่าตัดเข่าคนไข้ข้อเข่าเสื่อม นอนห้องธรรมดาสองคืน"
res = information.func_all(text_3)
print(res)
text_4="อาจารย์ หมอ กชพรรณ แผนก ออร์โธ ผ่าตัด เข่า คนไข้ ข้อเข่าเสื่อม พักฟื้น ห้อง ธรรมดา หนึ่ง "
res = information.func_all(text_4)
print(res)






