"""
このファイルは、画面表示以外の様々な関数が定義されたファイルです。
"""

############################################################
# 1. ライブラリの読み込み
############################################################
import os
import streamlit as st
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain.retrievers.multi_query import MultiQueryRetriever
import constants as ct

############################################################
# 2. 関数定義
############################################################

def get_llm_response(chat_message: str):
    """
    LLMから回答を取得します。
    """
    # ------------------------------------------
    # 1. Retrieverの準備
    # ------------------------------------------
    # session_stateからRetrieverを取得
    # initialize.pyでst.session_state.retrieverに格納されている想定
    base_retriever = st.session_state.retriever

    # ユーザーの多様な質問に対応できるよう、MultiQueryRetrieverを使用
    llm = ChatOpenAI(temperature=0)
    retriever = MultiQueryRetriever.from_llm(
        retriever=base_retriever, llm=llm
    )

    # ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼
    # 【デバッグコード】
    # Retrieverがどんなドキュメントを返しているかターミナルで確認します。
    # -------------------------------------------------------------
    print(f"--- ユーザーの質問: {chat_message} ---")
    retrieved_docs = retriever.invoke(chat_message)
    print("----- 検索されたドキュメント -----")
    if not retrieved_docs:
        print("ドキュメントが見つかりませんでした。")
    else:
        for i, doc in enumerate(retrieved_docs):
            print(f"【ドキュメント {i+1}】")
            print(f"  Source: {doc.metadata.get('source', 'N/A')}")
            print(f"  Page: {doc.metadata.get('page', 'N/A')}")
            # コンテンツの先頭150文字を表示
            content_preview = doc.page_content[:150].replace('\n', ' ')
            print(f"  Content: {content_preview}...")
    print("----------------------------\n")
    # ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲


    # ------------------------------------------
    # 2. プロンプトとChainの準備
    # ------------------------------------------
    # モードに応じてプロンプトを切り替え
    if st.session_state.mode == ct.ANSWER_MODE_1:
        # 社内文書検索モード
        prompt = ChatPromptTemplate.from_template(ct.SYSTEM_PROMPT_DOC_SEARCH)
    else:
        # 社内問い合わせモード
        prompt = ChatPromptTemplate.from_template(ct.SYSTEM_PROMPT_INQUIRY)

    # ------------------------------------------
    # 3. Chainの実行
    # ------------------------------------------
    # Chainを構築
    # retrieved_docsを直接contextとして渡すように変更
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    # Chainを実行して回答を取得
    answer = rag_chain.invoke(chat_message)

    # ------------------------------------------
    # 4. 返却値の整形
    # ------------------------------------------
    # components.pyで使いやすいように、回答とコンテキストを辞書にまとめる
    llm_response = {
        "answer": answer,
        "context": retrieved_docs
    }
    
    return llm_response


def get_source_icon(file_path: str) -> str:
    """
    ファイルパスに応じて適切なアイコンを返します。
    """
    if "http" in file_path:
        return ct.LINK_SOURCE_ICON
    else:
        return ct.DOC_SOURCE_ICON


def build_error_message(message: str) -> str:
    """
    エラーメッセージを整形します。
    """
    return f"{message}\n{ct.COMMON_ERROR_MESSAGE}"

# 注: initialize.pyで`utils.load_documents()`を呼び出している場合、
# その関数もこのファイルに必要です。もしそのような関数があれば、
# このコードに追記してください。
#
# def load_documents():
#     ...
#     return docs