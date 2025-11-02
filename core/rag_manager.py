# -*- coding: utf-8 -*-
"""
RAG (Retrieval-Augmented Generation) Manager

Pinecone을 사용한 벡터 검색 및 대화 메모리 관리
OpenAI Embeddings를 사용하여 대화 내용을 임베딩
"""

import json
import logging
import os
from typing import List, Dict, Any, Optional
from django.conf import settings
from django.core.cache import cache

try:
    from pinecone import Pinecone, ServerlessSpec
    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False
    logging.warning("Pinecone이 설치되지 않았습니다. 'pip install pinecone-client'를 실행하세요.")

from openai import OpenAI

from .models import ConversationMemory, Conversation, Message, CustomUser

logger = logging.getLogger(__name__)


class RAGManager:
    """
    RAG Manager 클래스
    
    사용자의 대화 기록을 임베딩하고 Pinecone을 사용하여
    유사도 기반 검색을 수행합니다.
    """
    
    EMBEDDING_MODEL = "text-embedding-3-small"
    EMBEDDING_DIM = 1536  # text-embedding-3-small의 차원
    TOP_K = 5  # 검색할 유사 대화 수
    
    def __init__(self, user: Optional[CustomUser] = None):
        """
        RAG Manager 초기화
        
        Args:
            user: 사용자 객체 (유저별 네임스페이스 관리)
        """
        self.user = user
        self.client = None
        self.pinecone = None
        self.index = None
        
        # OpenAI API 키 확인
        api_key = getattr(settings, 'OPENAI_API_KEY', '')
        if api_key:
            self.client = OpenAI(api_key=api_key)
        else:
            logger.warning("OpenAI API 키가 설정되지 않았습니다. RAG 기능이 제한됩니다.")
        
        # Pinecone 초기화
        if PINECONE_AVAILABLE:
            pinecone_api_key = os.getenv('PINECONE_API_KEY') or getattr(settings, 'PINECONE_API_KEY', '')
            if pinecone_api_key:
                try:
                    self.pinecone = Pinecone(api_key=pinecone_api_key)
                    self._initialize_index()
                    logger.info("Pinecone 초기화 완료")
                except Exception as e:
                    logger.error(f"Pinecone 초기화 실패: {e}")
                    self.pinecone = None
            else:
                logger.warning("Pinecone API 키가 설정되지 않았습니다. RAG 기능이 제한됩니다.")
        else:
            logger.warning("Pinecone 라이브러리가 설치되지 않았습니다.")
    
    def _get_index_name(self) -> str:
        """Pinecone 인덱스 이름"""
        return os.getenv('PINECONE_INDEX_NAME', 'prompt-mate-memories')
    
    def _get_namespace(self) -> str:
        """사용자별 네임스페이스"""
        if self.user:
            return f"user_{self.user.id}"
        else:
            return "global"
    
    def _initialize_index(self):
        """Pinecone 인덱스 초기화"""
        if not self.pinecone:
            return
        
        index_name = self._get_index_name()
        
        try:
            # 인덱스 목록 확인
            existing_indexes = [index.name for index in self.pinecone.list_indexes()]
            
            if index_name not in existing_indexes:
                # 인덱스 생성 (서버리스)
                logger.info(f"Pinecone 인덱스 생성: {index_name}")
                self.pinecone.create_index(
                    name=index_name,
                    dimension=self.EMBEDDING_DIM,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region="us-east-1"
                    )
                )
                logger.info(f"인덱스 {index_name} 생성 완료")
            
            # 인덱스 연결
            self.index = self.pinecone.Index(index_name)
            logger.info(f"Pinecone 인덱스 연결: {index_name}")
            
        except Exception as e:
            logger.error(f"Pinecone 인덱스 초기화 실패: {e}")
            self.index = None
    
    def create_embedding(self, text: str) -> Optional[List[float]]:
        """
        텍스트를 임베딩 벡터로 변환
        
        Args:
            text: 임베딩할 텍스트
        
        Returns:
            임베딩 벡터 (리스트) 또는 None
        """
        if not self.client:
            logger.error("OpenAI 클라이언트가 초기화되지 않았습니다.")
            return None
        
        try:
            # 캐시 키
            cache_key = f"embedding_{hash(text)}"
            cached = cache.get(cache_key)
            if cached is not None:
                return cached
            
            # OpenAI API 호출
            response = self.client.embeddings.create(
                model=self.EMBEDDING_MODEL,
                input=text
            )
            
            embedding = response.data[0].embedding
            
            # 캐시 저장 (1시간)
            cache.set(cache_key, embedding, 3600)
            
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
            # 임베딩을 바이트로 변환 (DB 저장용)
            embedding_bytes = json.dumps(embedding).encode('utf-8')
            
            memory = ConversationMemory.objects.create(
                user=self.user,
                conversation=conversation,
                message=message,
                content=content,
                embedding_vector=embedding_bytes,
                metadata={
                    'model': self.EMBEDDING_MODEL,
                    'dimension': self.EMBEDDING_DIM,
                    'content_length': len(content)
                }
            )
            
            # Pinecone에 벡터 추가
            if self.index is not None:
                try:
                    namespace = self._get_namespace()
                    vector_id = str(memory.id)
                    
                    # 메타데이터 준비
                    metadata = {
                        'conversation_id': str(conversation.id),
                        'conversation_title': conversation.title[:100] if conversation.title else '',
                        'content': content[:500],  # Pinecone 메타데이터는 제한적
                        'created_at': memory.created_at.isoformat(),
                    }
                    
                    if message:
                        metadata['message_id'] = str(message.id)
                    
                    self.index.upsert(
                        vectors=[(vector_id, embedding, metadata)],
                        namespace=namespace
                    )
                    
                    logger.info(f"Pinecone에 벡터 추가: {vector_id}, 네임스페이스: {namespace}")
                except Exception as e:
                    logger.error(f"Pinecone 벡터 추가 실패: {e}")
            
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
        if not self.index:
            logger.info("Pinecone 인덱스가 초기화되지 않았습니다.")
            return []
        
        top_k = top_k or self.TOP_K
        
        # 쿼리 임베딩
        query_embedding = self.create_embedding(query)
        if query_embedding is None:
            return []
        
        try:
            namespace = self._get_namespace()
            
            # Pinecone 검색
            search_results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                namespace=namespace,
                include_metadata=True
            )
            
            results = []
            if search_results.matches:
                for match in search_results.matches:
                    try:
                        memory_id = match.id
                        memory = ConversationMemory.objects.get(id=memory_id)
                        
                        # 유사도 점수 (Pinecone은 cosine similarity를 0-1로 반환)
                        similarity = float(match.score) if match.score else 0.0
                        
                        results.append({
                            'memory_id': str(memory.id),
                            'conversation_id': match.metadata.get('conversation_id', '') if match.metadata else str(memory.conversation.id),
                            'conversation_title': match.metadata.get('conversation_title', '') if match.metadata else memory.conversation.title,
                            'content': match.metadata.get('content', '') if match.metadata else memory.content,
                            'similarity': similarity,
                            'created_at': match.metadata.get('created_at', '') if match.metadata else memory.created_at.isoformat(),
                        })
                    except ConversationMemory.DoesNotExist:
                        logger.warning(f"메모리 {match.id}를 찾을 수 없습니다.")
                        continue
                    except Exception as e:
                        logger.error(f"검색 결과 처리 실패: {e}")
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
        데이터베이스에서 Pinecone 인덱스 재구성
        
        기존 ConversationMemory 레코드를 사용하여 Pinecone 인덱스를 재생성
        """
        if not self.index or not self.user:
            logger.error("Pinecone 인덱스 또는 사용자가 없습니다.")
            return
        
        logger.info(f"사용자 {self.user.username}의 Pinecone 인덱스 재구성 시작...")
        
        namespace = self._get_namespace()
        
        # 네임스페이스 삭제 (선택적 - 주의 필요)
        # self.index.delete(delete_all=True, namespace=namespace)
        
        # 모든 메모리 로드
        memories = ConversationMemory.objects.filter(user=self.user).order_by('created_at')
        
        vectors_to_upsert = []
        batch_size = 100
        
        for memory in memories:
            try:
                # 임베딩 벡터 재생성 또는 로드
                embedding = self.create_embedding(memory.content)
                if embedding is None:
                    continue
                
                metadata = {
                    'conversation_id': str(memory.conversation.id),
                    'conversation_title': memory.conversation.title[:100] if memory.conversation.title else '',
                    'content': memory.content[:500],
                    'created_at': memory.created_at.isoformat(),
                }
                
                if memory.message:
                    metadata['message_id'] = str(memory.message.id)
                
                vectors_to_upsert.append((str(memory.id), embedding, metadata))
                
                # 배치 업로드
                if len(vectors_to_upsert) >= batch_size:
                    self.index.upsert(
                        vectors=vectors_to_upsert,
                        namespace=namespace
                    )
                    logger.info(f"배치 업로드: {len(vectors_to_upsert)}개 벡터")
                    vectors_to_upsert = []
                    
            except Exception as e:
                logger.error(f"메모리 {memory.id} 처리 실패: {e}")
        
        # 남은 벡터 업로드
        if vectors_to_upsert:
            self.index.upsert(
                vectors=vectors_to_upsert,
                namespace=namespace
            )
            logger.info(f"최종 배치 업로드: {len(vectors_to_upsert)}개 벡터")
        
        logger.info(f"Pinecone 인덱스 재구성 완료: {memories.count()}개 메모리")


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
