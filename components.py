"""
このファイルは、画面表示に特化した関数定義のファイルです。
"""

############################################################
# ライブラリの読み込み
############################################################
import os
import streamlit as st
import utils
import constants as ct

############################################################
# 関数定義
############################################################

# --- ヘルパー関数 ---
def create_download_button(file_path, page_number=None, key_prefix="", use_success=False):
    """ダウンロードボタンを生成するヘルパー関数"""
    try:
        # ファイルをバイナリモードで読み込む
        with open(file_path, "rb") as fp:
            file_data = fp.read()
        
        # 表示用のラベルを作成
        display_label = os.path.basename(file_path)
        if file_path.lower().endswith(".pdf") and page_number:
            display_label += f" {ct.PAGE_NUMBER_TEMPLATE.format(page_number=page_number)}"
        
        # ボタンを表示
        st.download_button(
            label=display_label,
            data=file_data,
            file_name=os.path.basename(file_path),
            key=f"{key_prefix}_{file_path}_{page_number}",
            use_container_width=True, # ボタンをコンテナの幅に広げる
        )
    except FileNotFoundError:
        st.error(f"ファイルが見つかりません: {file_path}", icon="⚠️")

# --- 画面表示関数 ---

def display_app_title():
    st.title(ct.APP_NAME)

def display_sidebar():
    st.sidebar.header(ct.SIDEBAR_TITLE)
    st.session_state.mode = st.sidebar.radio(
        "モード選択", [ct.ANSWER_MODE_1, ct.ANSWER_MODE_2], label_visibility="hidden"
    )
    st.sidebar.markdown("---")
    st.sidebar.markdown(ct.SIDEBAR_SEARCH_INFO_HEADER)
    st.sidebar.info(ct.SIDEBAR_SEARCH_INFO_BODY)
    st.sidebar.markdown(ct.SIDEBAR_SEARCH_EXAMPLE)
    st.sidebar.markdown(ct.SIDEBAR_INQUIRY_INFO_HEADER)
    st.sidebar.info(ct.SIDEBAR_INQUIRY_INFO_BODY)
    st.sidebar.markdown(ct.SIDEBAR_INQUIRY_EXAMPLE)

def display_initial_ai_message():
    with st.chat_message("assistant"):
        st.info(ct.INITIAL_AI_MESSAGE)
        st.warning(ct.INPUT_PROMPT_WARNING, icon=ct.WARNING_ICON)

# ▼▼▼【修正箇所】ダウンロードボタンを表示するように変更 ▼▼▼
def display_conversation_log():
    """会話ログの一覧表示"""
    for i, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            if message["role"] == "user":
                st.markdown(message["content"])
            else:
                if message["content"]["mode"] == ct.ANSWER_MODE_1:
                    if "no_file_path_flg" not in message["content"]:
                        st.markdown(message["content"]["main_message"])
                        create_download_button(
                            message['content']['main_file_path'],
                            message['content'].get('main_page_number'),
                            key_prefix=f"log_main_{i}"
                        )
                        if "sub_message" in message["content"]:
                            st.markdown(message["content"]["sub_message"])
                            for j, sub_choice in enumerate(message["content"]["sub_choices"]):
                                create_download_button(
                                    sub_choice['source'],
                                    sub_choice.get('page_number'),
                                    key_prefix=f"log_sub_{i}_{j}"
                                )
                    else:
                        st.markdown(message["content"]["answer"])
                else: # 社内問い合わせモード
                    st.markdown(message["content"]["answer"])
                    if "file_info_list" in message["content"]:
                        st.divider()
                        st.markdown(f"##### {message['content']['message']}")
                        for k, file_info in enumerate(message["content"]["file_info_list"]):
                            create_download_button(
                                file_info['source'],
                                file_info.get('page_number'),
                                key_prefix=f"log_contact_{i}_{k}"
                            )

# ▼▼▼【修正箇所】ダウンロードボタンを表示するように変更 ▼▼▼
def display_search_llm_response(llm_response):
    """「社内文書検索」モードにおけるLLMレスポンスを表示"""
    if llm_response["context"] and llm_response["answer"] != ct.NO_DOC_MATCH_ANSWER:
        main_message = "入力内容に関する情報は、以下のファイルに含まれている可能性があります。"
        st.markdown(main_message)
        
        main_context = llm_response["context"][0]
        main_file_path = main_context.metadata["source"]
        main_page_number = main_context.metadata.get("page", -1) + 1
        
        create_download_button(main_file_path, main_page_number, "current_main")
        
        sub_choices = []
        duplicate_check_list = []
        if len(llm_response["context"]) > 1:
            sub_message = "その他、ファイルありかの候補を提示します。"
            st.markdown(sub_message)
            for i, document in enumerate(llm_response["context"][1:]):
                sub_file_path = document.metadata["source"]
                if sub_file_path == main_file_path or sub_file_path in duplicate_check_list:
                    continue
                duplicate_check_list.append(sub_file_path)
                
                sub_page_number = document.metadata.get("page", -1) + 1
                create_download_button(sub_file_path, sub_page_number, f"current_sub_{i}")
                
                sub_choices.append({"source": sub_file_path, "page_number": sub_page_number})
        
        content = {"mode": ct.ANSWER_MODE_1, "main_message": main_message, "main_file_path": main_file_path}
        if main_page_number > 0: content["main_page_number"] = main_page_number
        if sub_choices: content.update({"sub_message": sub_message, "sub_choices": sub_choices})
    else:
        st.markdown(ct.NO_DOC_MATCH_MESSAGE)
        content = {"mode": ct.ANSWER_MODE_1, "answer": ct.NO_DOC_MATCH_MESSAGE, "no_file_path_flg": True}
    return content

# ▼▼▼【修正箇所】ダウンロードボタンを表示するように変更 ▼▼▼
def display_contact_llm_response(llm_response):
    """「社内問い合わせ」モードにおけるLLMレスポンスを表示"""
    st.markdown(llm_response["answer"])

    file_info_list_for_log = []
    if llm_response["answer"] != ct.INQUIRY_NO_MATCH_ANSWER and llm_response["context"]:
        st.divider()
        message = "情報源"
        st.markdown(f"##### {message}")
        
        file_path_list = []
        for i, document in enumerate(llm_response["context"]):
            file_path = document.metadata["source"]
            if file_path in file_path_list: continue
            file_path_list.append(file_path)
            
            page_number = document.metadata.get("page", -1) + 1
            create_download_button(file_path, page_number, f"current_contact_{i}")
            
            log_entry = {"source": file_path}
            if page_number > 0: log_entry["page_number"] = page_number
            file_info_list_for_log.append(log_entry)

    content = {"mode": ct.ANSWER_MODE_2, "answer": llm_response["answer"]}
    if file_info_list_for_log:
        content["message"] = message
        content["file_info_list"] = file_info_list_for_log
    return content