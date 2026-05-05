#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MinIO对象存储服务
统一封装文件上传、下载、管理
支持对话记录、PDF导出、媒体文件存储
"""

import json
import io
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from loguru import logger
from minio import Minio
from minio.error import S3Error

from Agent.config.settings import Config


class MinIOStorageService:
    """
    MinIO对象存储服务
    管理对话记录、PDF导出、媒体文件等
    """
    
    def __init__(self):
        """初始化MinIO客户端"""
        self.client: Optional[Minio] = None
        self.bucket_name = Config.MINIO_BUCKET_NAME
        self._connect()
    
    def _connect(self):
        """连接到MinIO服务器"""
        try:
            self.client = Minio(
                Config.MINIO_ENDPOINT,
                access_key=Config.MINIO_ACCESS_KEY,
                secret_key=Config.MINIO_SECRET_KEY,
                secure=Config.MINIO_SECURE,
                region=Config.MINIO_REGION
            )
            self._ensure_bucket_exists()
            logger.info(f"MinIO连接成功: {Config.MINIO_ENDPOINT}")
        except Exception as e:
            logger.error(f"MinIO连接失败: {str(e)}")
            raise RuntimeError(f"无法连接到MinIO: {str(e)}")
    
    def _ensure_bucket_exists(self):
        """确保存储桶存在"""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"创建存储桶: {self.bucket_name}")
            else:
                logger.info(f"存储桶已存在: {self.bucket_name}")
        except S3Error as e:
            logger.error(f"检查/创建存储桶失败: {str(e)}")
            raise
    
    def _generate_object_path(self, 
                             category: str, 
                             username: str, 
                             filename: str,
                             date_folder: bool = True) -> str:
        """
        生成对象存储路径
        
        Args:
            category: 类别 (conversations, exports/pdf, media/images等)
            username: 用户名
            filename: 文件名
            date_folder: 是否按日期分文件夹
        
        Returns:
            str: 完整对象路径
        """
        if date_folder:
            date_str = datetime.now().strftime("%Y-%m-%d")
            return f"{category}/{username}/{date_str}/{filename}"
        else:
            return f"{category}/{username}/{filename}"
    
    def upload_conversation(self, 
                           username: str,
                           session_id: str,
                           conversation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        上传对话记录到MinIO
        
        Args:
            username: 用户名
            session_id: 会话ID
            conversation_data: 对话记录数据
        
        Returns:
            Dict: 上传结果，包含object_path
        """
        try:
            timestamp = datetime.now().strftime("%H%M%S")
            filename = f"{session_id}_{timestamp}.json"
            object_path = self._generate_object_path(
                "conversations", username, filename
            )
            
            json_data = json.dumps(conversation_data, ensure_ascii=False, indent=2)
            data_bytes = json_data.encode('utf-8')
            data_stream = io.BytesIO(data_bytes)
            
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_path,
                data=data_stream,
                length=len(data_bytes),
                content_type="application/json",
                metadata={
                    "username": username,
                    "session_id": session_id,
                    "upload_time": datetime.now().isoformat(),
                    "message_count": str(len(conversation_data.get("messages", [])))
                }
            )
            
            logger.info(f"对话记录已上传: {object_path}")
            return {
                "success": True,
                "object_path": object_path,
                "size": len(data_bytes),
                "url": self.generate_presigned_url(object_path, expiry=3600*24)
            }
            
        except Exception as e:
            logger.error(f"上传对话记录失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def upload_pdf(self, 
                  username: str,
                  pdf_bytes: bytes,
                  metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        上传PDF文件到MinIO
        
        Args:
            username: 用户名
            pdf_bytes: PDF文件字节
            metadata: 元数据信息
        
        Returns:
            Dict: 上传结果
        """
        try:
            destination = metadata.get("destination", "unknown")
            timestamp = datetime.now().strftime("%H%M%S")
            safe_dest = destination.encode('ascii', 'ignore').decode('ascii').strip('_').strip()
            if not safe_dest:
                try:
                    from urllib.parse import quote
                    safe_dest = quote(destination, safe='')
                except Exception:
                    safe_dest = "plan"
            filename = f"travel_plan_{safe_dest}_{timestamp}.pdf"
            
            object_path = self._generate_object_path(
                "exports/pdf", username, filename
            )
            
            data_stream = io.BytesIO(pdf_bytes)
            
            safe_metadata = {
                "username": username,
                "destination": destination.encode('ascii', 'ignore').decode('ascii') if destination else "unknown",
                "upload_time": datetime.now().isoformat(),
            }
            for k, v in metadata.items():
                if k != "destination":
                    safe_value = str(v).encode('ascii', 'ignore').decode('ascii')
                    safe_metadata[k] = safe_value
            
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_path,
                data=data_stream,
                length=len(pdf_bytes),
                content_type="application/pdf",
                metadata=safe_metadata
            )
            
            logger.info(f"PDF已上传: {object_path}")
            return {
                "success": True,
                "object_path": object_path,
                "size": len(pdf_bytes),
                "url": self.generate_presigned_url(object_path, expiry=3600*24*7)
            }
            
        except Exception as e:
            logger.error(f"上传PDF失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def generate_presigned_url(self, 
                              object_path: str, 
                              expiry: int = 3600,
                              method: str = "GET") -> Optional[str]:
        """
        生成预签名URL
        
        Args:
            object_path: 对象路径
            expiry: 过期时间（秒）
            method: HTTP方法
        
        Returns:
            Optional[str]: 预签名URL
        """
        try:
            url = self.client.presigned_get_object(
                self.bucket_name,
                object_path,
                expires=timedelta(seconds=expiry)
            )
            return url
        except Exception as e:
            logger.error(f"生成预签名URL失败: {str(e)}")
            return None
    
    def health_check(self) -> Dict[str, Any]:
        """
        健康检查
        
        Returns:
            Dict: 健康状态
        """
        try:
            buckets = list(self.client.list_buckets())
            return {
                "status": "healthy",
                "endpoint": Config.MINIO_ENDPOINT,
                "total_buckets": len(buckets),
                "connection": "ok"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "endpoint": Config.MINIO_ENDPOINT,
                "error": str(e)
            }


_minio_service_instance = None


def get_minio_service() -> MinIOStorageService:
    """获取全局MinIO服务实例"""
    global _minio_service_instance
    if _minio_service_instance is None:
        _minio_service_instance = MinIOStorageService()
    return _minio_service_instance


def reset_minio_service():
    """重置MinIO服务实例（用于测试）"""
    global _minio_service_instance
    _minio_service_instance = None
