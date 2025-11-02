# -*- coding: utf-8 -*-
"""
RAG (Retrieval-Augmented Generation) Manager

FAISS를 사용한 벡터 검색 및 대화 메모리 관리
OpenAI Embeddings를 사용하여 대화 내용을 임베딩
"""

import logging
import os
import pickle
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from django.conf import settings
from django.core.cache import cache

try:
    import faiss
except ImportError:
    faiss = None
    logging.warning("FAISS가 설치되지 않았습니다. 'pip install faiss-cpu'를 실행하세요.")

from openai import OpenAI

from .models import ConversationMemory, Conversation, Message, CustomUser

logger = logging.getLogger(__name__)


class RAGManager:
    """
    RAG Manager 클래스
    
    사용자의 대화 기록을 임베딩하고 FAISS를 사용하여
    유사도 기반 검색을 수행합니다.
    """
    
    EMBEDDING_MODEL = "text-embedding-3-small"
    EMBEDDING_DIM = 1536  # text-embedding-3-small의 차원
    # Railway 영구 볼륨 경로 사용 (없으면 기본 경로)
    INDEX_DIR = os.getenv('RAILWAY_VOLUME_MOUNT_PATH', os.path.join(settings.BASE_DIR, 'faiss_indexes'))
    TOP_K = 5  # 검색할 유사 대화 수
    
    def __init__(self, user: Optional[CustomUser] = None):
        """
        RAG Manager 초기화
        
        Args:
            user: 사용자 객체 (유저별 인덱스 관리)
        """
        self.user = user
        self.client = None
        
        # OpenAI API 키 확인
        api_key = settings.OPENAI_API_KEY
        if api_key:
            self.client = OpenAI(api_key=api_key)
        else:
            logger.warning("OpenAI API 키가 설정되지 않았습니다. RAG 기능이 제한됩니다.")
        
        # FAISS 인덱스 초기화
        self.index = None
        self.index_to_memory_id = []  # 인덱스 ID -> ConversationMemory ID 매핑
        
        if faiss and user:
            self._load_or_create_index()
    
    def _get_index_path(self) -> str:
        """사용자별 FAISS 인덱스 파일 경로"""
        # INDEX_DIR은 이미 설정되어 있음 (Railway 볼륨 경로 또는 기본 경로)
        index_dir = self.INDEX_DIR if isinstance(self.INDEX_DIR, str) else str(self.INDEX_DIR)
        if not os.path.exists(index_dir):
            os.makedirs(index_dir, exist_ok=True)
        
        if self.user:
            return os.path.join(index_dir, f"user_{self.user.id}.index")
        else:
            return os.path.join(index_dir, "global.index")
    
    def _get_mapping_path(self) -> str:
        """인덱스 매핑 파일 경로"""
        index_dir = self.INDEX_DIR if isinstance(self.INDEX_DIR, str) else str(self.INDEX_DIR)
        if self.user:
            return os.path.join(index_dir, f"user_{self.user.id}_mapping.pkl")
        else:
            return os.path.join(index_dir, "global_mapping.pkl")
    
    def _load_or_create_index(self):
        """FAISS 인덱스 로드 또는 생성"""
        if not faiss:
            logger.error("FAISS가 설치되지 않았습니다.")
            return
        
        index_path = self._get_index_path()
        mapping_path = self._get_mapping_path()
        
        if os.path.exists(index_path) and os.path.exists(mapping_path):
            try:
                # 기존 인덱스 로드
                self.index = faiss.read_index(index_path)
                with open(mapping_path, 'rb') as f:
                    self.index_to_memory_id = pickle.load(f)
                logger.info(f"FAISS 인덱스 로드: {index_path}, 벡터 수: {self.index.ntotal}")
            except Exception as e:
                logger.error(f"인덱스 로드 실패: {e}")
                self._create_new_index()
        else:
            self._create_new_index()
    
    def _create_new_index(self):
        """새 FAISS 인덱스 생성"""
        if not faiss:
            return
        
        # L2 거리 기반 인덱스 생성
        self.index = faiss.IndexFlatL2(self.EMBEDDING_DIM)
        self.index_to_memory_id = []
        logger.info(f"새 FAISS 인덱스 생성: 차원={self.EMBEDDING_DIM}")
    
    def _save_index(self):
        """FAISS 인덱스 저장"""
        if not faiss or not self.index:
            return
        
        try:
            index_path = self._get_index_path()
            mapping_path = self._get_mapping_path()
            
            faiss.write_index(self.index, index_path)
            with open(mapping_path, 'wb') as f:
                pickle.dump(self.index_to_memory_id, f)
            
            logger.info(f"FAISS 인덱스 저장: {index_path}")
        except Exception as e:
            logger.error(f"인덱스 저장 실패: {e}")
    
    def create_embedding(self, text: str) -> Optional[np.ndarray]:
        """
        텍스트를 임베딩 벡터로 변환
        
        Args:
            text: 임베딩할 텍스트
        
        Returns:
            임베딩 벡터 (numpy array) 또는 None
        """
        if not self.client:
            logger.error("OpenAI 클라이언트가 초기화되지 않았습니다.")
            return None
        
        try:
            # 캐시 키
            cache_key = f"embedding_{hash(text)}"
            cached = cache.get(cache_key)
            if cached is not None:
                return np.frombuffer(cached, dtype=np.float32)
            
            # OpenAI API 호출
            response = self.client.embeddings.create(
                model=self.EMBEDDING_MODEL,
                input=text
            )
            
            embedding = np.array(response.data[0].embedding, dtype=np.float32)
            
            # 캐시 저장 (1시간)
            cache.set(cache_key, embedding.tobytes(), 3600)
            
            return embedding
        
        except Exception as e:
            logger.error(f"임베딩 생성 실패: {e}")
            return None
    
    def add_conversation_to_memory(
        self,
        conversation: Conversation,
        message: Optional[Message] = None
    ) -> Optional[ConversationMemory]:
        """
        대화를 메모리에 추가
        
        Args:
            conversation: 대화 객체
            message: 특정 메시지 (선택적)
        
        Returns:
            ConversationMemory 객체 또는 None
        """
        if not self.user:
            logger.error("사용자가 지정되지 않았습니다.")
            return None
        
        # 임베딩할 내용 구성
        if message:
            content = f"{message.role}: {message.content}"
        else:
            # 대화 전체 요약
            messages = conversation.messages.all()[:10]  # 최근 10개 메시지
            content = "\n".join([f"{m.role}: {m.content[:200]}" for m in messages])
        
        if not content.strip():
            return None
        
        # 임베딩 생성
        embedding = self.create_embedding(content)
        if embedding is None:
            return None
        
        # DB에 저장
        try:
            memory = ConversationMemory.objects.create(
                user=self.user,
                conversation=conversation,
                message=message,
                content=content,
                embedding_vector=embedding.tobytes(),
                metadata={
                    'model': self.EMBEDDING_MODEL,
                    'dimension': self.EMBEDDING_DIM,
                    'content_length': len(content)
                }
            )
            
            # FAISS 인덱스에 추가
            if faiss and self.index is not None:
                self.index.add(embedding.reshape(1, -1))
                self.index_to_memory_id.append(str(memory.id))
                self._save_index()
            
            logger.info(f"메모리 추가: {memory.id}, 인덱스 크기: {self.index.ntotal if self.index else 0}")
            
            return memory
        
        except Exception as e:
            logger.error(f"메모리 저장 실패: {e}")
            return None
    
    def search_similar_conversations(
        self,
        query: str,
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        유사한 대화 검색
        
        Args:
            query: 검색 쿼리
            top_k: 반환할 결과 수
        
        Returns:
            유사 대화 목록 (메타데이터 포함)
        """
        if not self.index or self.index.ntotal == 0:
            logger.info("인덱스가 비어있습니다.")
            return []
        
        if not faiss:
            logger.error("FAISS가 설치되지 않았습니다.")
            return []
        
        top_k = top_k or self.TOP_K
        
        # 쿼리 임베딩
        query_embedding = self.create_embedding(query)
        if query_embedding is None:
            return []
        
        try:
            # FAISS 검색
            query_embedding = query_embedding.reshape(1, -1)
            distances, indices = self.index.search(query_embedding, top_k)
            
            results = []
            for dist, idx in zip(distances[0], indices[0]):
                if idx == -1:  # FAISS가 충분한 결과를 찾지 못한 경우
                    continue
                
                memory_id = self.index_to_memory_id[idx]
                
                try:
                    memory = ConversationMemory.objects.get(id=memory_id)
                    results.append({
                        'memory_id': str(memory.id),
                        'conversation_id': str(memory.conversation.id),
                        'conversation_title': memory.conversation.title,
                        'content': memory.content,
                        'distance': float(dist),
                        'similarity': 1.0 / (1.0 + float(dist)),  # 유사도 점수
                        'created_at': memory.created_at.isoformat(),
                    })
                except ConversationMemory.DoesNotExist:
                    logger.warning(f"메모리 {memory_id}를 찾을 수 없습니다.")
                    continue
            
            logger.info(f"유사 대화 검색: 쿼리='{query[:50]}...', 결과={len(results)}개")
            
            return results
        
        except Exception as e:
            logger.error(f"검색 실패: {e}")
            return []
    
    def get_relevant_context(
        self,
        query: str,
        top_k: int = 3,
        min_similarity: float = 0.7
    ) -> str:
        """
        쿼리와 관련된 컨텍스트 생성
        
        Args:
            query: 검색 쿼리
            top_k: 검색할 결과 수
            min_similarity: 최소 유사도
        
        Returns:
            컨텍스트 문자열
        """
        results = self.search_similar_conversations(query, top_k=top_k)
        
        # 유사도 필터링
        relevant_results = [
            r for r in results
            if r['similarity'] >= min_similarity
        ]
        
        if not relevant_results:
            return ""
        
        # 컨텍스트 구성
        context_parts = ["[관련 대화 기록]"]
        for i, result in enumerate(relevant_results, 1):
            context_parts.append(
                f"\n--- 대화 {i} (유사도: {result['similarity']:.2f}) ---\n"
                f"{result['content'][:500]}\n"
            )
        
        context = "\n".join(context_parts)
        
        logger.info(f"컨텍스트 생성: {len(relevant_results)}개 대화, {len(context)} 문자")
        
        return context
    
    def rebuild_index_from_database(self):
        """
        데이터베이스에서 인덱스 재구성
        
        기존 ConversationMemory 레코드를 사용하여 FAISS 인덱스를 재생성
        """
        if not faiss or not self.user:
            return
        
        logger.info(f"사용자 {self.user.username}의 인덱스 재구성 시작...")
        
        # 새 인덱스 생성
        self._create_new_index()
        
        # 모든 메모리 로드
        memories = ConversationMemory.objects.filter(user=self.user).order_by('created_at')
        
        vectors = []
        ids = []
        
        for memory in memories:
            try:
                vector = np.frombuffer(memory.embedding_vector, dtype=np.float32)
                vectors.append(vector)
                ids.append(str(memory.id))
            except Exception as e:
                logger.error(f"메모리 {memory.id} 로드 실패: {e}")
        
        if vectors:
            # 인덱스에 추가
            vectors_array = np.array(vectors, dtype=np.float32)
            self.index.add(vectors_array)
            self.index_to_memory_id = ids
            self._save_index()
            
            logger.info(f"인덱스 재구성 완료: {len(vectors)}개 벡터")
        else:
            logger.warning("재구성할 메모리가 없습니다.")


# 전역 RAG Manager 인스턴스 생성 함수
def get_rag_manager(user: Optional[CustomUser] = None) -> RAGManager:
    """
    RAG Manager 인스턴스 가져오기
    
    Args:
        user: 사용자 객체
    
    Returns:
        RAGManager 인스턴스
    """
    return RAGManager(user=user)

