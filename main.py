from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import pandas as pd

app = Flask(__name__)
app.secret_key = 'language'


# ここに既存のPythonコードを統合
# データの読み込み
dia_3_df = pd.read_csv('./dia_3.csv', encoding='utf-8')
dia_t_df = pd.read_csv('./dia_t.csv', encoding='utf-8')
diagn_title_df = pd.read_csv('./diagn_title.csv', encoding='utf-8')
diffsydiw_df = pd.read_csv('./diffsydiw.csv', encoding='utf-8')
sym_3_df = pd.read_csv('./sym_3.csv', encoding='utf-8')
dia_dis_matrix_df = pd.read_csv('./sym_dis_matrix.csv', encoding='utf-8')
sym_t_df = pd.read_csv('./sym_t.csv', encoding='utf-8')
symtoms2_df = pd.read_csv('./symptoms2.csv', encoding='utf-8')

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

# 辞書型の作成
languages1 = {
    'en': {
        'title': 'Select Symptoms',
        'symptom': 'Symptom:',
        'next_button': 'Next'
    },
    'ja': {
        'title': '症状を選択',
        'symptom': '症状:',
        'next_button': '次へ'
    }
}

languages2 = {
    'en': {
        'initial_diagnosis_title': 'Initial Diagnosis Result',
        'add_symptom_button': 'Add Symptoms:'
    },
    'ja': {
        'initial_diagnosis_title': '初期診断の結果',
        'add_symptom_button': '症状を追加する:'
    }
}

languages3 = {
    'en': {
        'additional_symptom_title': 'Select Additional Symptom',
        'select_optionymptom_button': 'Symptom:',
        'show_results_button': 'See the result'
    },
    'ja': {
        'additional_symptom_title': '追加の症状を診断する',
        'select_optionymptom_button': '症状:',
        'show_results_button': '診断結果を見る'
    }
}

languages4 = {
    'en': {
        'final_diagnosis_title': 'Diagnosis Result',
        'new_diagnosis_button': 'Try Again'
    },
    'ja': {
        'final_diagnosis_title': '診断の結果',
        'new_diagnosis_button': 'もう一度診断する'
    }
}

# 初期診断の提案を行う関数
def initial_diagnosis_suggestion(symptom, data, top_n=5):
    """初期診断を提案する関数"""
    filtered_data = data[data['symptom_x'] == symptom]
    diagnoses = filtered_data.groupby('diagnose_x')['wei'].sum().reset_index()
    top_diagnoses = diagnoses.sort_values(by='wei', ascending=False).head(top_n)
    return top_diagnoses['diagnose_x'].tolist()

# 診断の絞り込みを行う関数
def refined_diagnosis_with_weights(initial_diagnoses, additional_symptom, data):
    # 初期診断の重み付け
    data['initial_weight'] = data['diagnose_x'].apply(lambda x: 2 if x in initial_diagnoses else 0)

    # 追加症状の重み付け
    data['additional_weight'] = data['symptom_x'].apply(lambda x: 1 if x == additional_symptom else 0)

    # 両方が一致する場合の重み付け
    data['combined_weight'] = data.apply(lambda row: 3 if row['diagnose_x'] in initial_diagnoses and row['symptom_x'] == additional_symptom else 0, axis=1)

    # 総重みの計算
    data['total_weight'] = data['initial_weight'] + data['additional_weight'] + data['combined_weight']

    # 最終的な診断の選択
    refined_diagnoses = data.sort_values(by='total_weight', ascending=False).head(1)
    return refined_diagnoses['diagnose_x'].tolist()

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
    lang = session.get('language', 'en')  # デフォルト言語は英語
    lang_data = languages1[lang]
    
    symptoms_list = symptoms_df['symptom_x'].tolist()
    return render_template('index.html', symptoms_list=symptoms_list, lang_data=lang_data)

@app.route('/initial_diagnosis', methods=['GET', 'POST'])
def initial_diagnosis():
    lang = session.get('language', 'en')  # デフォルト言語は英語
    lang_data = languages2[lang]  # 追加

    selected_symptom = request.form.get('symptom')
    initial_suggestions = initial_diagnosis_suggestion(selected_symptom, symptom_diagnosis_relation)
    return render_template('initial_diagnosis.html', initial_suggestions=initial_suggestions, symptom=selected_symptom, lang_data=lang_data)  # lang_data を渡す

@app.route('/additional_symptom', methods=['GET', 'POST'])
def additional_symptom():
    lang = session.get('language', 'en')  # デフォルト言語は英語
    lang_data = languages3[lang]  # 追加

    symptoms_list = symptoms_df['symptom_x'].tolist()
    if request.method == 'POST':
        selected_symptom = request.form.get('symptom')
        return render_template('additional_symptom.html', symptoms_list=symptoms_list, selected_symptom=selected_symptom, lang_data=lang_data)
    return render_template('additional_symptom.html', symptoms_list=symptoms_list, lang_data=lang_data)

@app.route('/final_diagnosis', methods=['GET', 'POST'])
def final_diagnosis():
    lang = session.get('language', 'en')  # デフォルト言語は英語
    lang_data = languages4[lang]  # 追加

    selected_symptom = request.form.get('symptom')
    additional_symptom = request.form.get('additional_symptom')
    initial_suggestions = initial_diagnosis_suggestion(selected_symptom, symptom_diagnosis_relation)
    refined_suggestions = refined_diagnosis_with_weights(initial_suggestions, additional_symptom, symptom_diagnosis_relation)
    return render_template('final_diagnosis.html', refined_suggestions=refined_suggestions, lang_data=lang_data)

@app.route('/switch_language/<language>')
def switch_language(language):
    session['language'] = language
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
