import base64

import pandas as pd
import numpy as np
import sqlite3
from sqlite3 import Connection
import streamlit as st
from datetime import date, datetime
import os.path
import copy as cp
import re
import plotly.graph_objects as go
import time


def welcome():
    t = st.empty()
    text = "WELCOME TO MY FIRST APPLICATION"
    for i in range(len(text) + 1):
        t.markdown("# %s" % text[0:i])
        time.sleep(0.01)


class main:
    def __init__(self):
        self.menu = ['Trang Chủ', 'Hỏi Đáp', 'Biểu Đồ', 'Trợ Giúp']
        self.pos = ["Thủ Môn", "Hậu Vệ", 'Tiền Vệ', 'Tiền Đạo']
        self.club = ['Việt Nam', 'Nhật Bản', 'Saudi Arabia', 'Trung Quốc', 'Úc', 'Oman']
        self.removeOpt = ('Xóa tất cả', 'Xóa từng dòng')
        self.qaOpt = ('Tìm tên cầu thủ', 'Lọc độ tuổi cầu thủ', 'Vị trí và Câu lạc bộ')
        self.saveOpt = ('Lưu Biểu Đồ', 'Lưu Dữ Liệu')

        self.df = None
        if 'flagOpenFile' not in st.session_state:
            st.session_state.flagOpenFile = False
        if 'flag' not in st.session_state:
            st.session_state.flag = False
        if 'welcome' not in st.session_state:
            st.session_state.flag = True
        self.home()

    def home(self):

        # Menu choice
        with st.form(key='Form1'):
            choice = st.sidebar.selectbox("Menu", self.menu)

        # Select menu
        if choice == self.menu[0]:  # Trang chủ
            welcome()
            st.title('Trang chủ')
            st.image("football-manager-champion.jpg")
            buttonOpenFile = st.file_uploader("Tải file dữ liệu lên", type=["db", "csv", "xlsx"])
            print(buttonOpenFile)
            with st.expander("Bật tắt hiển thị dữ liệu"):
                if buttonOpenFile is not None:
                    st.info('Dữ liệu được thêm hoàn tất')
                    _, fileExtension = os.path.splitext(str(buttonOpenFile.name))
                    if fileExtension in ['.xlsx', '.xls']:
                        self.df = pd.read_excel(str(buttonOpenFile.name), engine='openpyxl')
                        st.session_state.flagOpenFile = False
                        st.session_state.flag = True
                    elif fileExtension in ['.csv']:
                        self.df = pd.read_csv(str(buttonOpenFile.name), encoding='utf-8')
                        st.session_state.flagOpenFile = False
                        st.session_state.flag = True
                    else:  # for *.db file
                        conn = self.get_connection(str(buttonOpenFile.name))
                        self.init_db(conn)
                        split_db_name = str(buttonOpenFile.name).split('.')
                        db_name = split_db_name[0]
                        self.df = pd.DataFrame(self.get_data(conn, db_name))
                        st.session_state.flagOpenFile = True
                        st.session_state.flag = True
                    st.info("Please click x to work around the cache")
                    if st.session_state.flag:
                        st.session_state.ssDf = self.df
                else:
                    st.warning('File dữ liệu chưa được thêm mới')

            # Input Data
            with st.expander('Hiển thị nhập dữ liệu'):
                nameValue, yearValue, numValue, clubValue, posValue = self.nhapDuLieu()

                if nameValue != '' or len(nameValue) != 0:
                    if st.button('Thêm'):
                        newYearValue = datetime.strptime(str(yearValue), '%Y-%m-%d').strftime('%d/%m/%Y')
                        if st.session_state.flagOpenFile:
                            lst = np.array([nameValue, newYearValue, posValue, clubValue, numValue])
                        else:
                            lst = [nameValue, newYearValue, posValue, clubValue, numValue]
                        self.importTable(lst)
                        st.success("Thêm dữ liệu cầu thủ <<< {} >>> hoàn tất".format(nameValue))
                else:
                    st.warning('Người dùng cần nhập đầy đủ thông tin')

            # Delete data
            col = st.columns(2)
            boxRemove = col[0].selectbox('Lựa Chọn', options=self.removeOpt)
            buttonRemove = col[0].button('Xóa')
            with st.expander('Hiển thị chỉnh sửa dữ liệu'):
                nameValue, yearValue, numValue, clubValue, posValue = self.nhapDuLieuEdit()
                lineNumEdit = st.number_input("Nhập số dòng", min_value=1, format='%d', help='Nhập số dòng cần chỉnh sửa')
                newYearVal = datetime.strptime(str(yearValue), '%Y-%m-%d').strftime('%d/%m/%Y')
                if st.button('Sửa'):
                    if st.session_state.flagOpenFile:
                        lst = np.array([nameValue, newYearVal, posValue, clubValue, numValue])
                    else:
                        lst = [nameValue, newYearVal, posValue, clubValue, numValue]
                    st.session_state.ssDf.iloc[lineNumEdit] = lst

            if boxRemove == 'Xóa từng dòng':
                id_row_rmv = col[1].text_input('Nhập số dòng cần xóa')
                id_row_rmv = self.randNumInput(id_row_rmv)

                if buttonRemove and id_row_rmv is not None:
                    st.write(st.session_state.ssDf['Họ và Tên'][id_row_rmv])
                    st.info('Độ dài dữ liệu trước khi xóa: ' + str(len(st.session_state.ssDf)))
                    st.session_state.ssDf = st.session_state.ssDf.drop(id_row_rmv)
                    st.session_state.ssDf = st.session_state.ssDf.reset_index(drop=True)
                    st.info('Độ dài dữ liệu sau khi xóa: ' + str(len(st.session_state.ssDf)))
            else:
                if buttonRemove:
                    st.session_state.ssDf = st.session_state.ssDf.drop(index=list(range(len(st.session_state.ssDf))))

            if self.df is not None:
                st.dataframe(st.session_state.ssDf)

            buttonSave = st.button('Lưu Dữ Liệu')
            if buttonSave:
                st.markdown(self.download_link(st.session_state.ssDf), unsafe_allow_html=True)
        elif choice == self.menu[1]:  # Hỏi đáp
            try:
                _newDf = None
                _copy_Df = None
                split_space_word = []
                st.title('Hỏi Đáp')
                self.check_database_exist()
                boxQa = st.selectbox('Lựa Chọn Câu Hỏi', options=self.qaOpt)
                st.markdown('*Lựa chọn cột hiển thị*')
                col = st.columns(5)
                filter_col1 = col[0].checkbox('Họ và Tên', True)
                filter_col2 = col[1].checkbox('Ngày Sinh', True)
                filter_col3 = col[2].checkbox('Vị Trí', True)
                filter_col4 = col[3].checkbox('Câu Lạc Bộ', True)
                filter_col5 = col[4].checkbox('Số Áo', True)
                col_filter_list = [filter_col1, filter_col2, filter_col3, filter_col4, filter_col5]
                if boxQa == self.qaOpt[0]:
                    names = st.text_input('Tìm cầu thủ')  # Người dùng nhập 1 hoặc nhiều tên
                    # và cách nhau bằng dấu phẩy
                    optionSearch = st.radio('Cách tìm kiếm', ('Chính Xác', 'Tương Đối'), index=0)
                    if st.session_state.ssDf is not None and len(names) > 0:
                        split_comma = names.split(',')
                        for word in split_comma:
                            word_list = re.findall(r"[\w']+", word)
                            split_space_word.extend(word_list)
                        _newDf = self.search_string(split_space_word, optionSearch)
                elif boxQa == self.qaOpt[1]:
                    old_lst = st.slider('Nhập Tuổi', min_value=18, max_value=50, value=[18, 20], step=1)  # Nhập số tuổi
                    # của cầu thủ
                    if st.session_state.ssDf is not None and len(old_lst) > 0:
                        _newDf = self.search_number(old_lst)
                elif boxQa == self.qaOpt[2]:
                    col1 = st.sidebar.selectbox("Vị Trí", self.pos)
                    col2 = st.sidebar.selectbox("Câu Lạc Bộ", self.club)
                    col_lst = [col1, col2]
                    if st.session_state.ssDf is not None:
                        _newDf = self.search_col(col_lst)
                buttonQa = st.button('Trả Lời')
                if buttonQa:
                    if _newDf is not None:
                        _newDf = self.filter_col(_newDf, col_filter_list)
                        import time
                        latest_iteration = st.empty()
                        bar = st.progress(0)
                        num = 10
                        for i in range(0, num + 1, 1):
                            latest_iteration.text(f'{num - i} seconds left')
                            bar.progress((100 // num) * i)
                            time.sleep(0.1)
                        st.dataframe(_newDf)
                    else:
                        st.error('Không có dữ liệu để trả lời câu hỏi. Vui lòng kiểm tra lại thông tin nhập')
            except:
                st.error('Chưa có dữ liệu')
        elif choice == self.menu[2]:  # Biểu đồ
            st.title('Biểu Đồ')
            try:
                cp_df = cp.deepcopy(st.session_state.ssDf)
                self.check_database_exist()
                if cp_df is None:
                    return
                fig = None
                num_club_dict = self.cal_string_club(cp_df['Câu Lạc Bộ'])
                num_pos_dict = self.cal_string_pos(cp_df['Câu Lạc Bộ'], num_club_dict, cp_df['Vị Trí'])
                chart_visual = st.sidebar.selectbox('Lựa chọn biểu đồ',
                                                    ('Bar Chart', 'Pie Chart'))
                opt_club = self.club[:]
                opt_club.insert(0, 'Tất Cả')
                list_club_keys = list(num_club_dict.keys())
                list_club_val = list(num_club_dict.values())
                list_pos_of_club_keys = list(num_pos_dict.keys())
                list_pos_of_club_val = list(num_pos_dict.values())
                list_pos_of_club_in_keys = list(list_pos_of_club_val[0].keys())
                if chart_visual == 'Bar Chart':
                    detail = st.sidebar.checkbox('Chi Tiết',
                                                 help='Thể hiện chi tiết số lượng từng vị trí trong đội bóng')
                    # create list to append into go.Bar
                    graph_bar = []
                    for i in range(len(list_club_keys)):
                        graph_bar.append(go.Bar(name=list_club_keys[i],
                                                x=[list_club_keys[i]],
                                                y=[list_club_val[i]]))
                    fig = go.Figure(data=graph_bar)
                    # Change the bar mode
                    fig.update_layout(title='Số Lượng Cầu Thủ Của Từng Đội Bóng World Cup 2021',
                                      barmode='group',
                                      xaxis_title="Các Quốc Gia Tham Gia World Cup 2022 Bảng A",
                                      yaxis_title="Số Lượng Cầu Thủ",
                                      font=dict(
                                          family="Courier New, monospace",
                                          size=15))
                    if detail:
                        x_axis_i = []
                        y_axis_0 = []  # position Thu Mon
                        y_axis_1 = []  # position Hau Ve
                        y_axis_2 = []  # position Tien Ve
                        y_axis_3 = []  # position Tien Dao

                        for y in range(len(list_club_keys)):
                            x_axis_i.append(list_pos_of_club_keys[y])

                        x_axis_0 = x_axis_i

                        for i in range(len(list_pos_of_club_in_keys)):
                            for y in range(len(list(list_pos_of_club_val))):
                                if i == 0:
                                    y_axis_0.append(list(list_pos_of_club_val[y].values())[i])
                                if i == 1:
                                    y_axis_1.append(list(list_pos_of_club_val[y].values())[i])
                                if i == 2:
                                    y_axis_2.append(list(list_pos_of_club_val[y].values())[i])
                                if i == 3:
                                    y_axis_3.append(list(list_pos_of_club_val[y].values())[i])

                        y_axis_0 = y_axis_0
                        y_axis_1 = y_axis_1
                        y_axis_2 = y_axis_2
                        y_axis_3 = y_axis_3
                        fig = go.Figure(data=[
                            go.Bar(name=list_pos_of_club_in_keys[0],
                                   x=x_axis_0,
                                   y=y_axis_0),
                            go.Bar(name=list_pos_of_club_in_keys[1],
                                   x=x_axis_0,
                                   y=y_axis_1),
                            go.Bar(name=list_pos_of_club_in_keys[2],
                                   x=x_axis_0,
                                   y=y_axis_2),
                            go.Bar(name=list_pos_of_club_in_keys[3],
                                   x=x_axis_0,
                                   y=y_axis_3)])
                        #  Change the bar mode
                        fig.update_layout(title='Số Lượng Vị Trí Cầu Thủ Đội Bóng World Cup 2021',
                                          barmode='group',
                                          xaxis_title="Các Quốc Gia Tham Gia World Cup 2022 Bảng A",
                                          yaxis_title="Số Lượng Cầu Thủ",
                                          font=dict(
                                              family="Courier New, monospace",
                                              size=15)
                                          )
                elif chart_visual == 'Pie Chart':
                    fig = go.Figure(data=[go.Pie(labels=list_club_keys,
                                                 values=list_club_val,
                                                 hovertemplate="%{label} "
                                                               "<br>Số lượng cầu thủ: %{value} </br> "
                                                               "Tỉ lệ phần trăm: %{percent}")])
                st.write(fig)

            except:
                st.error('Chưa có dữ liệu')
        elif choice == self.menu[3]:  # Liên hệ
            st.title('Liên Hệ')
            self.info()

    def nhapDuLieu(self):
        nameValue = st.text_input("Tên Đầy Đủ", help='Nhập họ và tên cầu thủ')
        col1, col2 = st.columns(2)
        yearValue = col1.date_input('Ngày Sinh', help='Nhập ngày tháng năm sinh cầu thủ',
                                    min_value=datetime(1950, 1, 1), max_value=datetime.now())
        numValue = col2.number_input("Số Áo", min_value=1, format='%d', help='Nhập số áo cầu thủ')
        clubValue = col1.selectbox("Câu Lạc Bộ", tuple(self.club), help='Chọn câu lạc bộ cầu thủ đang tham gia')
        posValue = col2.selectbox("Vị Trí", tuple(self.pos), help='Chọn vị trí của cầu thủ')

        return nameValue, yearValue, numValue, clubValue, posValue

    def nhapDuLieuEdit(self):
        nameValue = st.text_input("Tên Đầy Đủ", help='Nhập họ và tên cầu thủ', key='name')
        col1, col2 = st.columns(2)
        yearValue = col1.date_input('Ngày Sinh', help='Nhập ngày tháng năm sinh cầu thủ',
                                    min_value=datetime(1950, 1, 1), max_value=datetime.now(), key='date')
        numValue = col2.number_input("Số Áo", min_value=1, format='%d', help='Nhập số áo cầu thủ', key='number')
        clubValue = col1.selectbox("Câu Lạc Bộ", tuple(self.club), help='Chọn câu lạc bộ cầu thủ tham gia', key='club')
        posValue = col2.selectbox("Vị Trí", tuple(self.pos), help='Chọn vị trí của cầu thủ', key='pos')

        return nameValue, yearValue, numValue, clubValue, posValue

    @staticmethod
    def getList(inputDict):
        return list(inputDict.keys())

    def cal_string_pos(self, clubDf, clubdict, posLstDf):
        out_pos_dict = {}
        out_dict = {}
        clubdict_keylst = list(clubdict.keys())
        clubdict_vallst = list(clubdict.values())
        for i in range(len(posLstDf)):
            for j in range(len(posLstDf)):
                if posLstDf[i] == posLstDf[j]:
                    out_pos_dict[posLstDf[i]] = 0
                else:
                    pass
        pos_dict = self.getList(out_pos_dict)
        for i in range(len(clubDf)):
            for j in range(len(clubdict_keylst)):
                if clubDf[i] == clubdict_keylst[j]:
                    for k in range(len(pos_dict)):
                        if pos_dict[k] == posLstDf[i]:
                            out_pos_dict[pos_dict[k]] = out_pos_dict.get(pos_dict[k]) + 1
                    out_dict[clubdict_keylst[j]] = out_pos_dict
                    if sum(out_pos_dict.values()) == clubdict_vallst[j]:
                        out_pos_dict = out_pos_dict.fromkeys(out_pos_dict, 0)
        return out_dict

    def cal_string_club(self, inputClubLstDf):
        out_club_dict = {}
        for i in range(len(inputClubLstDf)):
            for j in range(len(inputClubLstDf)):
                if inputClubLstDf[i] == inputClubLstDf[j]:
                    out_club_dict[inputClubLstDf[i]] = 0
                else:
                    pass
        pos_dict = self.getList(out_club_dict)
        for i in range(len(inputClubLstDf)):
            for j in range(len(pos_dict)):
                if pos_dict[j] == inputClubLstDf[i]:
                    out_club_dict[pos_dict[j]] = out_club_dict.get(pos_dict[j]) + 1
        return out_club_dict

    @staticmethod
    def check_database_exist():
        if st.session_state.ssDf is not None:
            _copy_Df = cp.deepcopy(st.session_state.ssDf)
            st.dataframe(_copy_Df)
            col1, col2 = st.columns([4, 1])
            clearDB = col2.button('Clear dữ liệu')
            if clearDB:
                _copy_Df = _copy_Df[0:0]
                col1.warning('Dữ liệu chưa được nhập')
            else:
                col1.info('Dữ liệu đã được nhập')

    @staticmethod
    def search_col(col_list=None):
        obj = None
        cp_df = cp.deepcopy(st.session_state.ssDf)
        if col_list is not None:
            obj = cp_df[cp_df['Vị Trí'] == col_list[0]]
            obj = obj[obj['Câu Lạc Bộ'] == col_list[1]]
        return obj

    @staticmethod
    def filter_col(df, col_filter_list=None):
        show_names_lst = []
        if col_filter_list is not None:
            for i in range(len(col_filter_list)):
                if col_filter_list[i]:
                    show_names_lst.append(df.columns[i])
        obj = df[show_names_lst]
        return obj

    @staticmethod
    def session_state_df(dataframe):
        if dataframe is not None:
            st.session_state.ssDf = dataframe
        return st.dataframe(st.session_state.ssDf)

    @staticmethod
    def search_number(oldList):
        result = []
        today = date.today()
        currentYear = today.strftime('%Y')
        cp_df = cp.deepcopy(st.session_state.ssDf)
        for dateIdx in cp_df['Ngày Sinh']:
            date_transfer_df = datetime.strptime(dateIdx, '%d/%m/%Y')
            year_player = date_transfer_df.strftime('%Y')
            old_player = int(currentYear) - int(year_player)
            if oldList[0] <= int(old_player) <= oldList[1]:
                result.append(True)
            else:
                result.append(False)
        cp_df['result'] = result
        tuoiDf = cp_df[cp_df['result'] == True]
        obj = tuoiDf.drop(columns='result')
        return obj

    @staticmethod
    def search_string(word_list_name, option=0):
        cp_df = cp.deepcopy(st.session_state.ssDf)
        if option == 'Chính Xác':
            obj = cp_df[np.logical_and.reduce([cp_df['Họ và Tên'].str.contains(word) for word in word_list_name])]
        else:
            obj = cp_df[cp_df['Họ và Tên'].str.contains('|'.join(word_list_name))]
        return obj

    @staticmethod
    def rmvDuplicateValInLst(list_value):
        new_list = list(dict.fromkeys(list_value))
        return new_list

    def graph(self):
        pass

    @staticmethod
    def init_db(conn: Connection):
        conn.commit()

    @staticmethod
    def get_data(conn: Connection, db_name):
        db_select = "SELECT * FROM " + db_name
        df = pd.read_sql(db_select, con=conn)
        return df

    @staticmethod
    def get_connection(path: str):
        return sqlite3.connect(path, check_same_thread=False)

    def download_link(self, df):
        from io import BytesIO
        time_file = self.date_time()
        db_name = 'database' + time_file
        output = BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        df.to_excel(writer, sheet_name='Sheet1', index=False)
        writer.save()
        val = output.getvalue()
        b64 = base64.b64encode(val)  # val looks like b'...'

        obj_1 = f'<a href="data:application/octet-stream;base64,{b64.decode()}"'
        obj_2 = ' download=' + db_name + '.xlsx' + '>'
        obj_3 = '<input type="button" value="Download File"></a>'
        obj_download = obj_1 + obj_2 + obj_3
        return obj_download

    @staticmethod
    def info():
        st.subheader('FOOTBALL MANAGER\n')
        st.code("The Application is in demo phase\n"
                "---------------------------------------------"
                "\nPlease contact me through out these infomation below"
                "\nMember of Football Manager:"
                "\n      Name  : Nguyễn Lê Minh Hòa"
                "\n      Mobile: 0944 886 896")

    @staticmethod
    def importTable(lst):
        # Thêm vào database table
        if len(st.session_state.ssDf) > 0:
            st.session_state.ssDf.loc[-1] = lst
            st.session_state.ssDf.index += 1
        else:
            st.session_state.ssDf.loc[0] = lst
        st.session_state.ssDf.sort_index(inplace=True)

    @staticmethod
    def randNumInput(numStr):
        if len(numStr) == 0:
            return

        numStrLst = numStr.split(',')
        array = []
        for i in range(len(list(numStrLst))):
            if len(numStrLst[i]) > 1:
                d = numStrLst[i].split('-')
                for y in range(int(d[0]), int(d[1]) + 1):
                    array.append(y)
            else:
                array.append(int(numStrLst[i]))

        return array

    @staticmethod
    def getDifferentVal(lst):
        res = []
        for i in lst:
            if i not in res:
                res.append(i)
        res = sorted(res)

        return res

    @staticmethod
    def date_time():
        time_zone = datetime.now()
        current_time = (time_zone.strftime("%X")).replace(":", ".")
        time_file = time_zone.strftime("_%d-" + "%m-" + "%y_" + current_time)

        return time_file


if __name__ == '__main__':
    main()
