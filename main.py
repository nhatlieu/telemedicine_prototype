from flask import Flask, request, jsonify, render_template, redirect, url_for
import pandas as pd

app = Flask(__name__)



# ここに既存のPythonコードを統合
# データの読み込み
dia_3_df = pd.read_csv('./dia_3.csv')
dia_t_df = pd.read_csv('./dia_t.csv')
diagn_title_df = pd.read_csv('./diagn_title.csv')
diffsydiw_df = pd.read_csv('./diffsydiw.csv')
sym_3_df = pd.read_csv('./sym_3.csv')
dia_dis_matrix_df = pd.read_csv('./sym_dis_matrix.csv')
sym_t_df = pd.read_csv('./sym_t.csv')
symtoms2_df = pd.read_csv('./symptoms2.csv')

# 症状データの統合
symptoms_df = pd.merge(sym_3_df, sym_t_df, left_on='_id', right_on='syd', how='inner')

# dia_3.csv の '_id' 列を整数型に変換
dia_3_df['_id'] = pd.to_numeric(dia_3_df['_id'], errors='coerce')
dia_t_df['did'] = pd.to_numeric(dia_t_df['did'], errors='coerce')

# 変換できなかった行を削除
dia_3_df.dropna(subset=['_id'], inplace=True)
dia_t_df.dropna(subset=['did'], inplace=True)

# 診断データの統合
diagnosis_df = pd.merge(dia_3_df, dia_t_df, left_on='_id', right_on='did', how='inner')
diagnosis_df = pd.merge(diagnosis_df, diagn_title_df, left_on='_id', right_on='id', how='inner')

# 症状と診断の関連データの統合
symptom_diagnosis_relation = pd.merge(diffsydiw_df, symptoms_df, left_on='syd', right_on='syd', how='inner')
symptom_diagnosis_relation = pd.merge(symptom_diagnosis_relation, diagnosis_df, left_on='did', right_on='did', how='inner')

# 初期診断の提案を行う関数
def initial_diagnosis_suggestion(symptom, data, top_n=5):
    """初期診断を提案する関数"""
    filtered_data = data[data['symptom_x'] == symptom]
    diagnoses = filtered_data.groupby('diagnose_x')['wei'].sum().reset_index()
    top_diagnoses = diagnoses.sort_values(by='wei', ascending=False).head(top_n)
    return top_diagnoses['diagnose_x'].tolist()

# 診断の絞り込みを行う関数
def refine_diagnosis(initial_diagnoses, additional_symptom, data, top_n=1):
    # 追加の症状に基づいてフィルタリング
    filtered_data = data[data['symptom_x'] == additional_symptom]
    print("Filtered Data on Additional Symptom:", filtered_data)

    # 初期診断結果に含まれる診断でフィルタリング
    filtered_data = filtered_data[filtered_data['diagnose_x'].isin(initial_diagnoses)]
    print("Filtered Data on Initial Diagnoses:", filtered_data)

    # 絞り込まれた診断の計算
    refined_diagnoses = filtered_data.groupby('diagnose_x')['wei'].sum().reset_index()
    top_refined_diagnoses = refined_diagnoses.sort_values(by='wei', ascending=False).head(top_n)
    print("Refined Diagnoses:", top_refined_diagnoses)

    return top_refined_diagnoses['diagnose_x'].tolist()

# 例：初期症状として「Back ache or pain」が選択され、追加症状として「Fever」が提供された場合の処理

# selected_symptom = "Back ache or pain"
# additional_symptom = "Fever"

# initial_suggestions = initial_diagnosis_suggestion(selected_symptom, symptom_diagnosis_relation)
# print("Initial Diagnosis Suggestions:", initial_suggestions)

# refined_suggestions = refine_diagnosis(initial_suggestions, additional_symptom, symptom_diagnosis_relation)
# print("Refined Diagnosis Suggestions:", refined_suggestions)

# print(symptoms_df.columns)
# print(symptoms_df.head())
# print(symptom_diagnosis_relation)



@app.route('/', methods=['GET', 'POST'])
def index():
    symptoms_list = symptoms_df['symptom_x'].tolist()  # 症状のリストを作成
    return render_template('index.html', symptoms_list=symptoms_list)

@app.route('/initial_diagnosis', methods=['GET', 'POST'])
def initial_diagnosis():
    selected_symptom = request.form.get('symptom')
    initial_suggestions = initial_diagnosis_suggestion(selected_symptom, symptom_diagnosis_relation)
    return render_template('initial_diagnosis.html', initial_suggestions=initial_suggestions, symptom=selected_symptom)

@app.route('/additional_symptom', methods=['GET', 'POST'])
def additional_symptom():
    symptoms_list = symptoms_df['symptom_x'].tolist()
    if request.method == 'POST':
        selected_symptom = request.form.get('symptom')
        return render_template('additional_symptom.html', symptoms_list=symptoms_list, selected_symptom=selected_symptom)
    return render_template('additional_symptom.html', symptoms_list=symptoms_list)

@app.route('/final_diagnosis', methods=['GET', 'POST'])
def final_diagnosis():
    selected_symptom = request.form.get('symptom')
    additional_symptom = request.form.get('additional_symptom')
    initial_suggestions = initial_diagnosis_suggestion(selected_symptom, symptom_diagnosis_relation)
    refined_suggestions = refine_diagnosis(initial_suggestions, additional_symptom, symptom_diagnosis_relation)
    return render_template('final_diagnosis.html', refined_suggestions=refined_suggestions)

if __name__ == '__main__':
    app.run(debug=True)