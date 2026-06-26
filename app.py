import streamlit as st
import google.generativeai as genai
import os
import time

# --- 初期設定 ---
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# 事前に読み込ませるPDFのファイル名をリスト（配列）で指定します
PRE_INPUT_PDFS = ["wasedasaiall.pdf", "wasedasaiinsyoku.pdf"]

st.title("📚 早稲田祭資料対応アシスタント")
st.write(f"計 {len(PRE_INPUT_PDFS)} 件の資料に基づいて回答します。")

# --- 1. アプリ起動時に複数のPDFをGeminiにアップロード ---
if "gemini_files" not in st.session_state:
    st.session_state.gemini_files = [] # 複数のファイルオブジェクトを保存する空リスト
    
    with st.spinner("資料（PDF）を読み込み中... 少しお待ちください"):
        try:
            for pdf_path in PRE_INPUT_PDFS:
                if os.path.exists(pdf_path):
                    # ファイルをアップロード
                    gemini_file = genai.upload_file(path=pdf_path)
                    
                    # 処理完了を待機
                    while gemini_file.state.name == "PROCESSING":
                        time.sleep(2)
                        gemini_file = genai.get_file(gemini_file.name)
                    
                    # 成功したファイルをリストに追加
                    st.session_state.gemini_files.append(gemini_file)
                else:
                    st.warning(f"スキップしました: 『{pdf_path}』が見つかりません。")
            
            if st.session_state.gemini_files:
                st.success("すべての資料の読み込みが完了しました！いつでも質問をどうぞ。")
            else:
                st.error("読み込めるファイルが1つもありませんでした。")
                
        except Exception as e:
            st.error(f"資料のアップロード中にエラーが発生しました: {e}")

# --- 2. チャット履歴の初期化 ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# --- 3. ユーザーからの質問入力 ---
user_question = st.chat_input("知りたいことを入力してください")

if user_question and "gemini_files" in st.session_state and len(st.session_state.gemini_files) > 0:
    st.chat_message("user").write(user_question)
    st.session_state.messages.append({"role": "user", "content": user_question})

    with st.spinner("回答を探しています..."):
        try:
            model = genai.GenerativeModel("gemini-3.5-flash") # 動作したモデル名
            
            # 【ポイント】複数のファイルリストとユーザーの質問を結合して渡す
            contents = st.session_state.gemini_files + [user_question]
            
            response = model.generate_content(contents)
            
            st.chat_message("assistant").write(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")
