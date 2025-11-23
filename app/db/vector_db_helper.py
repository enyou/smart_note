#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件名: vector_db_helper.py
功能: 向量数据的使用的helper
作者: Yang
创建日期: 2025-09-15
版本号: 1.0
变更说明: 无
"""
from functools import lru_cache
from langchain.schema import Document
from typing import List, Dict, Any
from langchain_community.vectorstores import Chroma
from chromadb import Client
from langchain_huggingface.embeddings import HuggingFaceEmbeddings


class ChromaLangChainManager:
    def __init__(self, persist_directory: str = "./data/smart_note_vector_db"):
        """
        初始化ChromaDB管理器（使用LangChain）

        Args:
            persist_directory: 数据持久化目录
        """
        self.persist_directory = persist_directory
        self.embedding_function = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )
        self.vectorstore = None
        self.collection_name = "smart_note"

    def create_collection(self, documents: List[Document]):
        """
        创建向量数据库集合

        Args:
            documents: Document对象列表
            collection_name: 集合名称

        Returns:
            Chroma向量存储对象
        """
        self.vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=self.embedding_function,
            persist_directory=self.persist_directory,
            collection_name=self.collection_name
        )
        print(f"集合 '{self.collection_name}' 创建成功，包含 {len(documents)} 个文档")
        return self.vectorstore

    def load_existing_collection(self):
        """
        加载已存在的集合

        Args:
            collection_name: 集合名称

        Returns:
            Chroma向量存储对象
        """
        self.vectorstore = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embedding_function,
            collection_name=self.collection_name
        )
        print(f"集合 '{self.collection_name}' 加载成功")
        return self.vectorstore

    def add_documents(self, documents: List[Document]):
        """
        向现有集合添加文档

        Args:
            documents: Document对象列表
            collection_name: 集合名称
        """
        if self.vectorstore is None:
            self.load_existing_collection(self.collection_name)

        # 获取当前集合的文档数量
        current_count = self.vectorstore._collection.count()

        # 添加新文档
        self.vectorstore.add_documents(documents)

        new_count = self.vectorstore._collection.count()
        print(f"添加了 {new_count - current_count} 个新文档，现在共有 {new_count} 个文档")

    def similarity_search(self, query: str, k: int = 3, filter_dict: Dict[str, Any] = None):
        """
        相似性搜索

        Args:
            query: 查询文本
            k: 返回结果数量
            filter_dict: 过滤条件

        Returns:
            搜索结果列表
        """
        if self.vectorstore is None:
            raise ValueError("请先创建或加载集合")

        results = self.vectorstore.similarity_search(
            query=query,
            k=k,
            filter=filter_dict
        )
        return results

    def similarity_search_with_score(self, query: str, k: int = 3, filter_dict: Dict[str, Any] = None):
        """
        带相似度分数的搜索

        Args:
            query: 查询文本
            k: 返回结果数量
            filter_dict: 过滤条件

        Returns:
            带分数的搜索结果
        """
        if self.vectorstore is None:
            raise ValueError("请先创建或加载集合")

        results = self.vectorstore.similarity_search_with_score(
            query=query,
            k=k,
            filter=filter_dict
        )
        return results

    def get_collection_info(self):
        """
        获取集合信息
        """
        if self.vectorstore is None:
            raise ValueError("请先创建或加载集合")

        count = self.vectorstore._collection.count()
        print(f"集合中共有 {count} 个文档")
        return count

    def persist(self):
        """
        持久化数据到磁盘
        """
        if self.vectorstore is None:
            raise ValueError("请先创建或加载集合")

        self.vectorstore.persist()
        print(f"数据已保存到 {self.persist_directory}")

# @lru_cache
# def load_vector_db():
#     chroma = ChromaLangChainManager()
#     vetcor = chroma.load_existing_collection()
#     return vetcor
