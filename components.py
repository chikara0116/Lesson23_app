"""
このファイルは、画面表示に特化した関数定義のファイルです。
"""

############################################################
# ライブラリの読み込み
############################################################
import streamlit as st
import utils
import constants as ct


############################################################
# 関数定義
############################################################

def display_app_title():
    """
    タイトル表示
    """
    st.title(ct.APP_NAME)


def display_sidebar():
    """
    サイドバーのコンテンツを表示
    """
    st.sidebar.header(ct.SIDEBAR_TITLE)
    
    st.session_state.mode = st.sidebar.radio(
        "モード選択",
        [ct.ANSWER_MODE_1, ct.ANSWER_MODE_2],
        label_visibility="hidden"
    )
    
    st.sidebar.markdown("---")

    st.sidebar.markdown(ct.SIDEBAR_SEARCH_INFO_HEADER)
    st.sidebar.info(ct.SIDEBAR_SEARCH_INFO_BODY)
    st.sidebar.markdown(ct.SIDEBAR_SEARCH_EXAMPLE)
    
    st.sidebar.markdown(ct.SIDEBAR_INQUIRY_INFO_HEADER)
    st.sidebar.info(ct.SIDEBAR_INQUIRY_INFO_BODY)
    st.sidebar.markdown(ct.SIDEBAR_INQUIRY_EXAMPLE)


def display_initial_ai_message():
    """
    AIメッセージの初期表示
    """
    with st.chat_message("assistant"):
        st.info(ct.INITIAL_AI_MESSAGE)
        st.warning(ct.INPUT_PROMPT_WARNING, icon=ct.WARNING_ICON)


# ▼▼▼【修正箇所】ページ番号表示ロジックを追加 ▼▼▼
def display_conversation_log():
    """
    会話ログの一覧表示
    """
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "user":
                st.markdown(message["content"])
            else:
                if message["content"]["mode"] == ct.ANSWER_MODE_1:
                    if not "no_file_path_flg" in message["content"]:
                        st.markdown(message["content"]["main_message"])
                        
                        # メインドキュメントの表示
                        main_path = message['content']['main_file_path']
                        main_display_text = main_path
                        if main_path.lower().endswith(".pdf") and "main_page_number" in message["content"]:
                            main_display_text += f" {ct.PAGE_NUMBER_TEMPLATE.format(page_number=message['content']['main_page_number'])}"
                        
                        icon = utils.get_source_icon(main_path)
                        st.success(main_display_text, icon=icon)
                        
                        # サブドキュメントの表示
                        if "sub_message" in message["content"]:
                            st.markdown(message["content"]["sub_message"])
                            for sub_choice in message["content"]["sub_choices"]:
                                sub_path = sub_choice['source']
                                sub_display_text = sub_path
                                if sub_path.lower().endswith(".pdf") and "page_number" in sub_choice:
                                    sub_display_text += f" {ct.PAGE_NUMBER_TEMPLATE.format(page_number=sub_choice['page_number'])}"

                                icon = utils.get_source_icon(sub_path)
                                st.info(sub_display_text, icon=icon)
                    else:
                        st.markdown(message["content"]["answer"])
                else:
                    st.markdown(message["content"]["answer"])
                    if "file_info_list" in message["content"]:
                        st.divider()
                        st.markdown(f"##### {message['content']['message']}")
                        for file_info in message["content"]["file_info_list"]:
                            # file_infoには既にページ番号が含まれているのでそのまま表示
                            icon = utils.get_source_icon(file_info)
                            st.info(file_info, icon=icon)

# ▼▼▼【修正箇所】ページ番号表示ロジックを追加 ▼▼▼
def display_search_llm_response(llm_response):
    """
    「社内文書検索」モードにおけるLLMレスポンスを表示
    """
    if llm_response["context"] and llm_response["answer"] != ct.NO_DOC_MATCH_ANSWER:
        main_message = "入力内容に関する情報は、以下のファイルに含まれている可能性があります。"
        st.markdown(main_message)
        
        # メインドキュメントの表示
        main_context = llm_response["context"][0]
        main_file_path = main_context.metadata["source"]
        main_display_text = main_file_path
        icon = utils.get_source_icon(main_file_path)

        main_page_number = None
        if main_file_path.lower().endswith(".pdf") and "page" in main_context.metadata:
            main_page_number = main_context.metadata["page"] + 1
            main_display_text += f" {ct.PAGE_NUMBER_TEMPLATE.format(page_number=main_page_number)}"
        
        st.success(main_display_text, icon=icon)

        # サブドキュメントの表示
        sub_choices = []
        duplicate_check_list = []
        for document in llm_response["context"][1:]:
            sub_file_path = document.metadata["source"]
            if sub_file_path == main_file_path or sub_file_path in duplicate_check_list:
                continue
            duplicate_check_list.append(sub_file_path)
            
            sub_choice = {"source": sub_file_path}
            if sub_file_path.lower().endswith(".pdf") and "page" in document.metadata:
                sub_choice["page_number"] = document.metadata["page"] + 1
            sub_choices.append(sub_choice)
        
        if sub_choices:
            sub_message = "その他、ファイルありかの候補を提示します。"
            st.markdown(sub_message)
            for sub_choice in sub_choices:
                sub_display_text = sub_choice['source']
                icon = utils.get_source_icon(sub_choice['source'])
                if "page_number" in sub_choice:
                    sub_display_text += f" {ct.PAGE_NUMBER_TEMPLATE.format(page_number=sub_choice['page_number'])}"
                st.info(sub_display_text, icon=icon)

        # ログ用のcontent作成
        content = {
            "mode": ct.ANSWER_MODE_1,
            "main_message": main_message,
            "main_file_path": main_file_path,
        }
        if main_page_number:
            content["main_page_number"] = main_page_number
        if sub_choices:
            content["sub_message"] = sub_message
            content["sub_choices"] = sub_choices
    else:
        st.markdown(ct.NO_DOC_MATCH_MESSAGE)
        content = {
            "mode": ct.ANSWER_MODE_1,
            "answer": ct.NO_DOC_MATCH_MESSAGE,
            "no_file_path_flg": True
        }
    return content

# ▼▼▼【修正箇所】ページ番号表示ロジックを追加 ▼▼▼
def display_contact_llm_response(llm_response):
    """
    「社内問い合わせ」モードにおけるLLMレスポンスを表示
    """
    st.markdown(llm_response["answer"])

    file_info_list = []
    if llm_response["answer"] != ct.INQUIRY_NO_MATCH_ANSWER:
        st.divider()
        message = "情報源"
        st.markdown(f"##### {message}")

        file_path_list = []
        for document in llm_response["context"]:
            file_path = document.metadata["source"]
            if file_path in file_path_list:
                continue
            
            file_path_list.append(file_path)
            
            display_text = file_path
            if file_path.lower().endswith(".pdf") and "page" in document.metadata:
                page_number = document.metadata["page"] + 1
                display_text += f" {ct.PAGE_NUMBER_TEMPLATE.format(page_number=page_number)}"

            icon = utils.get_source_icon(file_path)
            st.info(display_text, icon=icon)
            file_info_list.append(display_text) # ログには表示用テキストをそのまま保存

    # ログ用のcontent作成
    content = {
        "mode": ct.ANSWER_MODE_2,
        "answer": llm_response["answer"]
    }
    if file_info_list:
        content["message"] = message
        content["file_info_list"] = file_info_list

    return content