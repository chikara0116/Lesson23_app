"""
このファイルは、最初の画面読み込み時にのみ実行される初期化処理が記述されたファイルです。
"""

############################################################
# ライブラリの読み込み
############################################################
import os
import logging
from logging.handlers import TimedRotatingFileHandler
from uuid import uuid4
import sys
import unicodedata
from dotenv import load_dotenv
import streamlit as st
from docx import Document
from langchain_community.document_loaders import WebBaseLoader
# ▼▼▼【修正箇所】CharacterTextSplitter ではなく RecursiveCharacterTextSplitter を推奨します ▼▼▼
# 多くのドキュメントタイプでより安定して動作するためです。もしCharacterTextSplitterを使い続ける場合はそのままでOKです。
from langchain.text_splitter import RecursiveCharacterTextSplitter
# ▲▲▲【修正箇所】ここまで ▲▲▲
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
import constants as ct


############################################################
# 設定関連
############################################################
# 「.env」ファイルで定義した環境変数の読み込み
load_dotenv()


############################################################
# 関数定義
############################################################

def initialize():
    """
    画面読み込み時に実行する初期化処理
    """
    # 初期化データの用意
    initialize_session_state()
    # ログ出力用にセッションIDを生成
    initialize_session_id()
    # ログ出力の設定
    initialize_logger()
    # RAGのRetrieverを作成
    initialize_retriever()


def initialize_logger():
    # (この関数は変更なし)
    os.makedirs(ct.LOG_DIR_PATH, exist_ok=True)
    logger = logging.getLogger(ct.LOGGER_NAME)
    if logger.hasHandlers():
        return
    log_handler = TimedRotatingFileHandler(
        os.path.join(ct.LOG_DIR_PATH, ct.LOG_FILE),
        when="D",
        encoding="utf8"
    )
    formatter = logging.Formatter(
        f"[%(levelname)s] %(asctime)s line %(lineno)s, in %(funcName)s, session_id={st.session_state.session_id}: %(message)s"
    )
    log_handler.setFormatter(formatter)
    logger.setLevel(logging.INFO)
    logger.addHandler(log_handler)


def initialize_session_id():
    # (この関数は変更なし)
    if "session_id" not in st.session_state:
        st.session_state.session_id = uuid4().hex


def initialize_retriever():
    """
    画面読み込み時にRAGのRetriever（ベクターストアから検索するオブジェクト）を作成
    """
    logger = logging.getLogger(ct.LOGGER_NAME)

    if "retriever" in st.session_state:
        return
    
    docs_all = load_data_sources()

    for doc in docs_all:
        doc.page_content = adjust_string(doc.page_content)
        for key in doc.metadata:
            doc.metadata[key] = adjust_string(doc.metadata[key])
    
    embeddings = OpenAIEmbeddings()
    
    # ▼▼▼【修正箇所 1/2】チャンク分割のパラメータを定数に置き換え ▼▼▼
    # チャンク分割用のオブジェクトを作成
    text_splitter = RecursiveCharacterTextSplitter( # 推奨のSplitterに変更
        chunk_size=ct.CHUNK_SIZE,
        chunk_overlap=ct.CHUNK_OVERLAP,
    )
    # ▲▲▲【修正箇所】ここまで ▲▲▲

    splitted_docs = text_splitter.split_documents(docs_all)

    db = Chroma.from_documents(splitted_docs, embedding=embeddings)

    # ▼▼▼【修正箇所 2/2】Retrieverの検索パラメータを定数に置き換え ▼▼▼
    # ベクターストアを検索するRetrieverの作成
    st.session_state.retriever = db.as_retriever(search_kwargs={"k": ct.TOP_K_DOCUMENTS})
    # ▲▲▲【修正箇所】ここまで ▲▲▲


def initialize_session_state():
    # (この関数は変更なし)
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.chat_history = []


def load_data_sources():
    # (この関数は変更なし)
    docs_all = []
    recursive_file_check(ct.RAG_TOP_FOLDER_PATH, docs_all)
    web_docs_all = []
    for web_url in ct.WEB_URL_LOAD_TARGETS:
        loader = WebBaseLoader(web_url)
        web_docs = loader.load()
        web_docs_all.extend(web_docs)
    docs_all.extend(web_docs_all)
    return docs_all


def recursive_file_check(path, docs_all):
    # (この関数は変更なし)
    if os.path.isdir(path):
        files = os.listdir(path)
        for file in files:
            full_path = os.path.join(path, file)
            recursive_file_check(full_path, docs_all)
    else:
        file_load(path, docs_all)


def file_load(path, docs_all):
    # (この関数は変更なし)
    file_extension = os.path.splitext(path)[1]
    file_name = os.path.basename(path)
    if file_extension in ct.SUPPORTED_EXTENSIONS:
        loader = ct.SUPPORTED_EXTENSIONS[file_extension](path)
        docs = loader.load()
        docs_all.extend(docs)


def adjust_string(s):
    # (この関数は変更なし)
    if type(s) is not str:
        return s
    if sys.platform.startswith("win"):
        s = unicodedata.normalize('NFC', s)
        s = s.encode("cp932", "ignore").decode("cp932")
        return s
    return s