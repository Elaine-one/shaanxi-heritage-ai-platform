from celery import shared_task
import logging
from django.db import transaction
from .models import News, Policy
from .redis_utils import redis_client

logger = logging.getLogger(__name__)

@shared_task
def sync_view_counts_to_db():
    """同步Redis中的浏览量数据到MySQL数据库
    
    这个任务会定期执行，将Redis中缓存的浏览量数据批量同步到MySQL，
    以减少数据库写入频率，提高性能。
    """
    logger.info("开始同步浏览量数据到数据库")
    
    try:
        # 同步新闻浏览量
        news_counts = redis_client.get_all_view_counts('news')
        news_updated = sync_news_view_counts(news_counts)
        
        # 同步政策浏览量
        policy_counts = redis_client.get_all_view_counts('policy')
        policy_updated = sync_policy_view_counts(policy_counts)
        
        logger.info(f"浏览量同步完成: 新闻 {news_updated} 条, 政策 {policy_updated} 条")
        
        return {
            'status': 'success',
            'news_updated': news_updated,
            'policy_updated': policy_updated
        }
        
    except Exception as e:
        logger.error(f"同步浏览量数据失败: {e}")
        return {
            'status': 'error',
            'message': str(e)
        }

def sync_news_view_counts(redis_counts: dict) -> int:
    """同步新闻浏览量
    
    Args:
        redis_counts: Redis中的浏览量数据 {news_id: view_count}
        
    Returns:
        更新的记录数
    """
    if not redis_counts:
        return 0
    
    updated_count = 0
    
    try:
        with transaction.atomic():
            for news_id, redis_view_count in redis_counts.items():
                try:
                    news = News.objects.get(id=news_id, is_active=True)
                    
                    # 只有当Redis中的浏览量大于数据库中的浏览量时才更新
                    if redis_view_count > news.view_count:
                        # 计算增量
                        increment = redis_view_count - news.view_count
                        
                        # 更新数据库
                        News.objects.filter(id=news_id).update(
                            view_count=redis_view_count
                        )
                        
                        updated_count += 1
                        logger.debug(f"新闻 {news_id} 浏览量更新: {news.view_count} -> {redis_view_count} (+{increment})")
                        
                        # 清除Redis缓存（可选，也可以保留一段时间）
                        # redis_client.delete_view_count('news', news_id)
                        
                except News.DoesNotExist:
                    logger.warning(f"新闻 {news_id} 不存在，跳过同步")
                    # 清除无效的Redis缓存
                    redis_client.delete_view_count('news', news_id)
                    
                except Exception as e:
                    logger.error(f"同步新闻 {news_id} 浏览量失败: {e}")
                    
    except Exception as e:
        logger.error(f"批量同步新闻浏览量失败: {e}")
        raise
    
    return updated_count

def sync_policy_view_counts(redis_counts: dict) -> int:
    """同步政策浏览量
    
    Args:
        redis_counts: Redis中的浏览量数据 {policy_id: view_count}
        
    Returns:
        更新的记录数
    """
    if not redis_counts:
        return 0
    
    updated_count = 0
    
    try:
        with transaction.atomic():
            for policy_id, redis_view_count in redis_counts.items():
                try:
                    policy = Policy.objects.get(id=policy_id, is_active=True)
                    
                    # 只有当Redis中的浏览量大于数据库中的浏览量时才更新
                    if redis_view_count > policy.view_count:
                        # 计算增量
                        increment = redis_view_count - policy.view_count
                        
                        # 更新数据库
                        Policy.objects.filter(id=policy_id).update(
                            view_count=redis_view_count
                        )
                        
                        updated_count += 1
                        logger.debug(f"政策 {policy_id} 浏览量更新: {policy.view_count} -> {redis_view_count} (+{increment})")
                        
                        # 清除Redis缓存（可选，也可以保留一段时间）
                        # redis_client.delete_view_count('policy', policy_id)
                        
                except Policy.DoesNotExist:
                    logger.warning(f"政策 {policy_id} 不存在，跳过同步")
                    # 清除无效的Redis缓存
                    redis_client.delete_view_count('policy', policy_id)
                    
                except Exception as e:
                    logger.error(f"同步政策 {policy_id} 浏览量失败: {e}")
                    
    except Exception as e:
        logger.error(f"批量同步政策浏览量失败: {e}")
        raise
    
    return updated_count

@shared_task
def cleanup_old_view_count_cache():
    """清理过期的浏览量缓存
    
    定期清理Redis中长时间未更新的浏览量缓存，
    避免内存无限增长。
    """
    logger.info("开始清理过期的浏览量缓存")
    
    try:
        # 这里可以实现更复杂的清理逻辑
        # 比如清理超过一定时间未更新的缓存
        # 或者清理已经同步到数据库的缓存
        
        # 简单实现：获取所有缓存键并检查其TTL
        news_pattern = "news:view_count:*"
        policy_pattern = "policy:view_count:*"
        
        cleaned_count = 0
        
        if redis_client.is_available():
            # 清理新闻缓存
            news_keys = redis_client.redis_client.keys(news_pattern)
            for key in news_keys:
                ttl = redis_client.redis_client.ttl(key)
                if ttl == -1:  # 没有设置过期时间的键
                    redis_client.redis_client.expire(key, 7 * 24 * 3600)  # 设置7天过期
                    cleaned_count += 1
            
            # 清理政策缓存
            policy_keys = redis_client.redis_client.keys(policy_pattern)
            for key in policy_keys:
                ttl = redis_client.redis_client.ttl(key)
                if ttl == -1:  # 没有设置过期时间的键
                    redis_client.redis_client.expire(key, 7 * 24 * 3600)  # 设置7天过期
                    cleaned_count += 1
        
        logger.info(f"浏览量缓存清理完成，处理了 {cleaned_count} 个键")
        
        return {
            'status': 'success',
            'cleaned_count': cleaned_count
        }
        
    except Exception as e:
        logger.error(f"清理浏览量缓存失败: {e}")
        return {
            'status': 'error',
            'message': str(e)
        }

@shared_task
def update_search_index():
    """更新搜索索引
    
    如果将来需要使用更高级的搜索引擎（如Elasticsearch），
    可以在这里实现索引更新逻辑。
    """
    logger.info("开始更新搜索索引")
    
    try:
        # 这里可以实现搜索索引的更新逻辑
        # 目前使用数据库搜索，暂时不需要特殊处理
        
        logger.info("搜索索引更新完成")
        
        return {
            'status': 'success',
            'message': '搜索索引更新完成'
        }
        
    except Exception as e:
        logger.error(f"更新搜索索引失败: {e}")
        return {
            'status': 'error',
            'message': str(e)
        }