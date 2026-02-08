#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MinIO对象存储服务
统一封装文件上传、下载、管理
支持对话记录、PDF导出、媒体文件存储
"""

import json
import io
from typing import Dict, Any, List, Optional, BinaryIO
from datetime import datetime, timedelta
from pathlib import Path
from loguru import logger

from Agent.config.settings import Config

# 尝试导入minio
try:
    from minio import Minio
    from minio.error import S3Error
    MINIO_AVAILABLE = True
except ImportError:
    MINIO_AVAILABLE = False
    logger.warning("minio库未安装，MinIO功能不可用。请运行: pip install minio")


class MinIOStorageService:
    """
    MinIO对象存储服务
    管理对话记录、PDF导出、媒体文件等
    """
    
    def __init__(self):
        """初始化MinIO客户端"""
        if not MINIO_AVAILABLE:
            raise RuntimeError("minio库未安装，无法使用MinIO存储服务")
        
        self.client: Optional[Minio] = None
        self.bucket_name = Config.MINIO_BUCKET_NAME
        self._init_client()
        self._ensure_bucket_exists()
    
    def _init_client(self):
        """初始化MinIO客户端连接"""
        try:
            self.client = Minio(
                Config.MINIO_ENDPOINT,
                access_key=Config.MINIO_ACCESS_KEY,
                secret_key=Config.MINIO_SECRET_KEY,
                secure=Config.MINIO_SECURE,
                region=Config.MINIO_REGION
            )
            # 测试连接
            self.client.list_buckets()
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
                
                # 设置桶策略（可选：允许公共读取）
                # self._set_bucket_policy()
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
            
            # 序列化JSON数据
            json_data = json.dumps(conversation_data, ensure_ascii=False, indent=2)
            data_bytes = json_data.encode('utf-8')
            data_stream = io.BytesIO(data_bytes)
            
            # 上传对象
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
    
    def download_conversation(self, object_path: str) -> Optional[Dict[str, Any]]:
        """
        从MinIO下载对话记录
        
        Args:
            object_path: 对象路径
        
        Returns:
            Optional[Dict]: 对话记录数据
        """
        try:
            response = self.client.get_object(self.bucket_name, object_path)
            data = json.loads(response.read().decode('utf-8'))
            response.close()
            response.release_conn()
            return data
        except S3Error as e:
            logger.error(f"下载对话记录失败: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"解析对话记录失败: {str(e)}")
            return None
    
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
            filename = f"travel_plan_{destination}_{timestamp}.pdf"
            
            object_path = self._generate_object_path(
                "exports/pdf", username, filename
            )
            
            data_stream = io.BytesIO(pdf_bytes)
            
            # 处理metadata，确保只包含ASCII字符（MinIO限制）
            safe_metadata = {
                "username": username,
                "destination": destination.encode('ascii', 'ignore').decode('ascii') if destination else "unknown",
                "upload_time": datetime.now().isoformat(),
            }
            # 添加其他metadata，过滤掉非ASCII字符
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
    
    def upload_json_export(self,
                          username: str,
                          json_data: Dict[str, Any],
                          plan_id: str) -> Dict[str, Any]:
        """
        上传JSON导出文件
        
        Args:
            username: 用户名
            json_data: JSON数据
            plan_id: 规划ID
        
        Returns:
            Dict: 上传结果
        """
        try:
            timestamp = datetime.now().strftime("%H%M%S")
            filename = f"plan_export_{plan_id}_{timestamp}.json"
            
            object_path = self._generate_object_path(
                "exports/json", username, filename
            )
            
            json_bytes = json.dumps(json_data, ensure_ascii=False, indent=2).encode('utf-8')
            data_stream = io.BytesIO(json_bytes)
            
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_path,
                data=data_stream,
                length=len(json_bytes),
                content_type="application/json",
                metadata={
                    "username": username,
                    "plan_id": plan_id,
                    "upload_time": datetime.now().isoformat()
                }
            )
            
            logger.info(f"JSON导出已上传: {object_path}")
            return {
                "success": True,
                "object_path": object_path,
                "size": len(json_bytes)
            }
            
        except Exception as e:
            logger.error(f"上传JSON导出失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def upload_media(self,
                    username: str,
                    file_bytes: bytes,
                    filename: str,
                    media_type: str = "images") -> Dict[str, Any]:
        """
        上传媒体文件
        
        Args:
            username: 用户名
            file_bytes: 文件字节
            filename: 文件名
            media_type: 媒体类型 (images, audio, documents)
        
        Returns:
            Dict: 上传结果
        """
        try:
            content_type_map = {
                "images": "image/jpeg",
                "audio": "audio/mpeg",
                "documents": "application/octet-stream"
            }
            
            object_path = self._generate_object_path(
                f"media/{media_type}", username, filename, date_folder=True
            )
            
            data_stream = io.BytesIO(file_bytes)
            
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_path,
                data=data_stream,
                length=len(file_bytes),
                content_type=content_type_map.get(media_type, "application/octet-stream"),
                metadata={
                    "username": username,
                    "upload_time": datetime.now().isoformat(),
                    "original_filename": filename
                }
            )
            
            logger.info(f"媒体文件已上传: {object_path}")
            return {
                "success": True,
                "object_path": object_path,
                "size": len(file_bytes),
                "url": self.generate_presigned_url(object_path)
            }
            
        except Exception as e:
            logger.error(f"上传媒体文件失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_user_objects(self, 
                        username: str, 
                        prefix: str = "",
                        recursive: bool = True) -> List[Dict[str, Any]]:
        """
        获取用户的所有对象列表
        
        Args:
            username: 用户名
            prefix: 路径前缀筛选
            recursive: 是否递归
        
        Returns:
            List[Dict]: 对象列表
        """
        try:
            user_prefix = f"{prefix}/{username}/" if prefix else f"conversations/{username}/"
            
            objects = []
            for obj in self.client.list_objects(
                self.bucket_name, 
                prefix=user_prefix,
                recursive=recursive
            ):
                objects.append({
                    "object_name": obj.object_name,
                    "size": obj.size,
                    "last_modified": obj.last_modified.isoformat() if obj.last_modified else None,
                    "etag": obj.etag,
                    "content_type": obj.content_type
                })
            
            return objects
            
        except Exception as e:
            logger.error(f"获取用户对象列表失败: {str(e)}")
            return []
    
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
            from datetime import timedelta
            
            url = self.client.presigned_get_object(
                self.bucket_name,
                object_path,
                expires=timedelta(seconds=expiry)
            )
            return url
        except Exception as e:
            logger.error(f"生成预签名URL失败: {str(e)}")
            return None
    
    def delete_object(self, object_path: str) -> bool:
        """
        删除对象
        
        Args:
            object_path: 对象路径
        
        Returns:
            bool: 是否成功
        """
        try:
            self.client.remove_object(self.bucket_name, object_path)
            logger.info(f"对象已删除: {object_path}")
            return True
        except Exception as e:
            logger.error(f"删除对象失败: {str(e)}")
            return False
    
    def get_object_metadata(self, object_path: str) -> Optional[Dict[str, Any]]:
        """
        获取对象元数据
        
        Args:
            object_path: 对象路径
        
        Returns:
            Optional[Dict]: 元数据
        """
        try:
            stat = self.client.stat_object(self.bucket_name, object_path)
            return {
                "size": stat.size,
                "last_modified": stat.last_modified.isoformat() if stat.last_modified else None,
                "etag": stat.etag,
                "content_type": stat.content_type,
                "metadata": stat.metadata
            }
        except Exception as e:
            logger.error(f"获取对象元数据失败: {str(e)}")
            return None
    
    def health_check(self) -> Dict[str, Any]:
        """
        MinIO健康检查
        
        Returns:
            Dict: 健康状态
        """
        try:
            # 测试连接
            buckets = self.client.list_buckets()
            bucket_exists = self.client.bucket_exists(self.bucket_name)
            
            # 获取存储桶统计
            objects = list(self.client.list_objects(self.bucket_name, limit=1))
            
            return {
                "status": "healthy",
                "endpoint": Config.MINIO_ENDPOINT,
                "bucket": self.bucket_name,
                "bucket_exists": bucket_exists,
                "total_buckets": len(buckets),
                "connection": "ok"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "endpoint": Config.MINIO_ENDPOINT,
                "error": str(e)
            }


# 全局MinIO服务实例
_minio_service_instance = None

def get_minio_service() -> MinIOStorageService:
    """
    获取全局MinIO服务实例
    
    Returns:
        MinIOStorageService: MinIO服务实例
    """
    global _minio_service_instance
    if _minio_service_instance is None:
        _minio_service_instance = MinIOStorageService()
    return _minio_service_instance


def reset_minio_service():
    """重置MinIO服务实例（用于测试）"""
    global _minio_service_instance
    _minio_service_instance = None
