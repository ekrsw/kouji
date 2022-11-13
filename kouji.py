import datetime as dt
import pandas as pd


def wareki_to_seireki(kansei):
    '''和暦(R03/04/01)→西暦(2021/04/01)→date型へ変換する関数

    Parameters:
    --------
    kansei:str
        和暦の日付(R03/04/01)

    Returns:
    --------
    date
        date型の年月日
    '''
    if kansei != 0:
        tmp = kansei.split('/')
        # 昭和
        if tmp[0][0] == 'S':
            tmp[0] = str(int(tmp[0][1:]) + 1925)

        # 平成
        elif tmp[0][0] == 'H':
            tmp[0] = str(int(tmp[0][1:]) + 1988)

        # 令和
        elif tmp[0][0] == 'R':
            tmp[0] = str(int(tmp[0][1:]) + 2018)
        tmp = dt.datetime.strptime('/'.join(tmp), '%Y/%m/%d')
        kansei = dt.date(tmp.year, tmp.month, tmp.day)
    else:
        kansei = False
    return kansei


def read_csv_pro_ce(PATH):
    '''工事管理表(簡易)CSVから辞書｛工事コード：[工事名, 実績, 累計, 期首, 完成年月日]｝
       を作成して返す。

    Parameters:
    --------
    PATH: str
        NX-Pro/NX-CEで出力した工事管理表(簡易)のCSVファイルのPATH。
        カレントディレクトリにあるならファイル名。

    Returns:
    --------
    dict
        dictionary型。｛工事コード：[工事名, 実績, 累計, 期首, 完成年月日]｝
    '''
    df = pd.read_csv(PATH, header = 0, encoding="ANSI", \
                     dtype = {'コード':'str', '完成年月日':'str'})
    df = df.fillna(0)
    d = {}
    for i in range(0, len(df)-5, 3):
        code = df.iat[i, 0]
        name = df.iat[i, 1]
        jisseki = int(df.iat[i, 3])
        ruikei = int(df.iat[i+1, 3])
        kisyu = int(ruikei - jisseki)
        kansei = wareki_to_seireki(df.iat[i, 5])
        val = [name, jisseki, ruikei, kisyu, kansei]
        d[code] = val

    return d

def mk_set(dic, kisyunen):
    '''集合作成関数
    Parameters:
    --------
    dic: dict
        ｛工事コード：[工事名, 実績, 累計, 期首, 完成年月日]｝
    kisyunen: date
         当期データの期首の年月日
    
    Returns:
    --------
         al: set
         mi: set
         fu: set
         kan: set
         集合作成。al: すべて, mi: 未成, fu: 当期首以降の完成日, kan: 過年度の完成日
    '''
    # すべて
    al = set(dic.keys())
    # 未成
    mi = {i for i in dic if dic[i][4] == False}
    # 当期首以降の完成日
    fu = {i for i in dic if dic[i][4] != False and dic[i][4] >= kisyunen}
    # 過年度の完成日
    kan = {i for i in dic if dic[i][4] != False and dic[i][4] < kisyunen}

    return al, mi, fu, kan

# 出力の様式
def print_ans(i, dif, name):
    print(i.ljust(12), ':', '{:,}'.format(dif).rjust(15), ':', name, sep='')
# 出力の項目名。上部に表示。
def print_title():
    print('<Code>'.ljust(12), ':', '<Amount>'.ljust(15), ':', '<Name>', sep='')

# メインの処理関数
def main(zenki, touki, pre_all, pre_mi, pre_fu, pre_kan, cur_all, cur_mi, cur_fu, cur_kan):
    ans_mi_non = pre_mi - cur_all    
    ans_fu_non = pre_fu - cur_all
    tmp = (cur_mi | cur_fu) - pre_all
    ans_non_zan = {i for i in tmp if touki[i][3] != 0}
    ans_kan_mi = pre_kan & cur_mi
    ans_mi_kan = pre_mi & cur_kan
    ans_fu_kan = pre_fu & cur_kan
    ans_kan_fu = pre_kan & cur_fu
    tmp = (pre_all & cur_all) - (pre_kan & cur_kan)
    ans_zan_zan = {i for i in tmp if zenki[i][2] != touki[i][3]}

    ans_key = ans_mi_non | ans_fu_non | ans_non_zan | ans_kan_mi | ans_mi_kan | ans_fu_kan | ans_kan_fu | ans_zan_zan

    if ans_key:
        print('\n','※※※※※※※《未成工事の差額となる不整合》※※※※※※※', '\n', sep='')
        
        # 前期未成だった工事が無くなっている。
        if ans_mi_non:
            ans_mi_non = list(ans_mi_non)
            ans_mi_non.sort()
            print( '【前期未成だった工事が無くなっている】', sep='')
            print_title()
            for i in ans_mi_non:
                name = zenki[i][0]
                dif = -zenki[i][2]
                print_ans(i, dif, name)
            print('')
        
        # 前期に当期以降の完成日が入っていた工事が無くなっている。
        if ans_fu_non:
            ans_fu_non = list(ans_fu_non)
            ans_fu_non.sort()
            print('【前期に当期以降の完成日が入っていた工事が無くなっている】', sep='')
            print_title()
            for i in ans_fu_non:
                name = zenki[i][0]
                dif = -zenki[i][2]
                print_ans(i, dif, name)
            print('')

        # 前期に無かった工事が当期首残を持っている。
        if ans_non_zan:
            ans_non_zan = list(ans_non_zan)
            ans_non_zan.sort()
            print('【前期に無かった工事が当期首残を持っている】', sep='')
            print_title()
            for i in ans_non_zan:
                name = touki[i][0]
                dif = touki[i][3]
                print_ans(i, dif, name)
            print('')

        # 過年度に完成していた工事が当期に未成となっている。
        if ans_kan_mi:
            ans_kan_mi = list(ans_kan_mi)
            ans_kan_mi.sort()
            print('【過年度に完成していた工事が当期に未成となっている】', sep='')
            print_title()
            for i in ans_kan_mi:
                name = touki[i][0]
                dif = touki[i][2]
                print_ans(i, dif, name)
            print('')

        # 前期末に未成だった工事が当期に過年度完成となっている。
        if ans_mi_kan:
            ans_mi_kan = list(ans_mi_kan)
            ans_mi_kan.sort()
            print('【前期末に未成だった工事が当期に過年度完成となっている】', sep='')
            print_title()
            for i in ans_mi_kan:
                name = zenki[i][0]
                dif = -zenki[i][2]
                print_ans(i, dif, name)
            print('')

        # 前期に当期以降の完成日が入っていた工事が当期に過年度完成になっている。
        if ans_fu_kan:
            ans_fu_kan = list(ans_fu_kan)
            ans_fu_kan.sort()
            print('【前期に当期以降の完成日が入っていた工事が当期に過年度完成になっている】', sep='')
            print_title()
            for i in ans_fu_kan:
                name = touki[i][0]
                dif = -zenki[i][2]
                print_ans(i, dif, name)
            print('')

        # 過年度に完成していた工事に当期以降の完成日が入っている。
        if ans_kan_fu:
            ans_kan_fu = list(ans_kan_fu)
            ans_kan_fu.sort()
            print('【過年度に完成していた工事に当期以降の完成日が入っている】', sep='')
            print_title()
            for i in ans_kan_fu:
                name = touki[i][0]
                dif = touki[i][2]
                print_ans(i, dif, name)
            print('')

        # 当期首残高と前期末残高が異なる。
        if ans_zan_zan:
            ans_zan_zan = list(ans_zan_zan)
            ans_zan_zan.sort()
            print('【当期首残高と前期末残高が異なる】', sep='')
            print_title()
            for i in ans_zan_zan:
                name = zenki[i][0]
                dif = touki[i][3]-zenki[i][2]
                print_ans(i, dif, name)
            print('')

    # 未成工事の差額にはならない不整合。要確認。
    # 前期に無かった工事が当期に過年度完成になっている
    ans_non_kan = cur_kan - pre_all

    # 前期に完成している工事で当期首残高と前期末残高が異なる
    tmp = pre_kan & cur_kan
    ans_kan_kan = {i for i in tmp if zenki[i][2] != touki[i][3]}

    # 差額にならない不整合がある時だけ実行。
    else_ans = ans_non_kan | ans_kan_kan

    if else_ans:
        print('※※※※※※《未成工事の差額とはならない不整合》※※※※※※', '\n', sep='')
        if ans_non_kan:
            print('【前期に無かった工事が当期に過年度完成になっている】', sep='')
            print_title()
            ans_non_kan = list(ans_non_kan)
            ans_non_kan.sort()
            for i in ans_non_kan:
                name = touki[i][0]
                dif = touki[i][2]
                print_ans(i, dif, name)
            print('')

        if ans_kan_kan:
            print('【前期に完成している工事で当期首残高と前期末残高が異なる】', sep='')
            print_title()
            ans_kan_kan = list(ans_kan_kan)
            ans_kan_kan.sort()
            for i in ans_kan_kan:
                name = zenki[i][0]
                dif = touki[i][3]-zenki[i][2]
                print_ans(i, dif, name)
            print('')

if __name__ == '__main__':
    input_data = input('期首年月日[例：2021年4月1日→20210401]>>')
    tmp = [input_data[0:4], input_data[4:6], input_data[6:]]
    tmp = '/'.join(tmp)

    tmp = dt.datetime.strptime(tmp, '%Y/%m/%d')
    kisyunen = dt.date(tmp.year, tmp.month, tmp.day)

    zenki = read_csv_pro_ce('zenki.csv')
    touki = read_csv_pro_ce('touki.csv')

    pre_all, pre_mi, pre_fu, pre_kan = mk_set(zenki, kisyunen)
    cur_all, cur_mi, cur_fu, cur_kan = mk_set(touki, kisyunen)
    main(zenki, touki, pre_all, pre_mi, pre_fu, pre_kan, cur_all, cur_mi, cur_fu, cur_kan)

    input('Press "Enter" key')
