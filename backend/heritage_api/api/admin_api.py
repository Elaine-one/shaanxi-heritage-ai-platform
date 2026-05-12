from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser, AllowAny
from rest_framework.response import Response
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.db.models import Q, Count
from rest_framework.pagination import PageNumberPagination
from django.core.cache import cache
from django.utils import timezone
import logging

from ..models import AdminOperationLog
from ..forum_models import (
    ForumPost, ForumComment, ForumTag, ForumReport,
    ForumAnnouncement, ForumRule
)
from ..creation_models import UserCreation

logger = logging.getLogger(__name__)


class AdminUserPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def log_admin_operation(request, action, resource_type, resource_id=None, resource_name='', detail=None):
    AdminOperationLog.objects.create(
        user=request.user if request.user.is_authenticated else None,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        resource_name=resource_name,
        detail=detail or {},
        ip_address=get_client_ip(request),
    )


# ==================== 认证 API ====================

@api_view(['POST'])
@permission_classes([AllowAny])
def admin_login(request):
    username = request.data.get('username')
    password = request.data.get('password')
    remember_me = request.data.get('remember_me', False)

    if not username or not password:
        return Response(
            {'message': '请提供用户名和密码'},
            status=status.HTTP_400_BAD_REQUEST
        )

    ip = get_client_ip(request)
    cache_key = f'admin_login_attempts_{ip}'
    attempts = cache.get(cache_key, 0)
    if attempts >= 5:
        return Response(
            {'message': '登录尝试次数过多，请1分钟后再试'},
            status=status.HTTP_429_TOO_MANY_REQUESTS
        )

    user = authenticate(username=username, password=password)

    if user is None:
        cache.set(cache_key, attempts + 1, 60)
        logger.warning(f'管理后台登录失败: {username}')
        return Response(
            {'message': '用户名或密码错误'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    if not user.is_active:
        return Response(
            {'message': '账户已被禁用'},
            status=status.HTTP_403_FORBIDDEN
        )

    if not user.is_staff and not user.is_superuser:
        return Response(
            {'message': '您没有管理后台的访问权限'},
            status=status.HTTP_403_FORBIDDEN
        )

    cache.delete(cache_key)
    login(request, user)

    if remember_me:
        request.session.set_expiry(30 * 24 * 60 * 60)
    else:
        request.session.set_expiry(0)

    log_admin_operation(request, 'login', 'auth', resource_name=username)

    logger.info(f'管理后台登录成功: {username}')

    return Response({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'is_staff': user.is_staff,
        'is_superuser': user.is_superuser,
        'message': '登录成功'
    })


# ==================== 统计 API ====================

@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_stats(request):
    from ..models import Heritage, News

    today = timezone.now().date()
    week_ago = today - timezone.timedelta(days=7)

    return Response({
        'heritage_count': Heritage.objects.count(),
        'news_count': News.objects.count(),
        'user_count': User.objects.count(),
        'post_count': ForumPost.objects.count(),
        'creation_count': UserCreation.objects.count(),
        'today_user_count': User.objects.filter(date_joined__date=today).count(),
        'week_post_count': ForumPost.objects.filter(created_at__date__gte=week_ago).count(),
        'pending_report_count': ForumReport.objects.filter(status='pending').count(),
    })


# ==================== 操作记录 API ====================

@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_operation_log_list(request):
    from django.contrib.admin.models import LogEntry

    action_map = {1: 'create', 2: 'update', 3: 'delete'}

    custom_logs = AdminOperationLog.objects.select_related('user').all()
    django_logs = LogEntry.objects.select_related('user', 'content_type').all()

    resource_type = request.query_params.get('resource_type')
    action_filter = request.query_params.get('action')

    if resource_type:
        custom_logs = custom_logs.filter(resource_type=resource_type)
        django_logs = django_logs.filter(content_type__model__icontains=resource_type)
    if action_filter:
        custom_logs = custom_logs.filter(action=action_filter)

    combined = []

    for log in custom_logs[:50]:
        combined.append({
            'id': f'custom_{log.id}',
            'source': 'vue_admin',
            'user': log.user.username if log.user else '未知',
            'action': log.action,
            'action_display': log.get_action_display(),
            'resource_type': log.resource_type,
            'resource_id': log.resource_id,
            'resource_name': log.resource_name,
            'detail': log.detail,
            'ip_address': log.ip_address,
            'created_at': log.created_at.isoformat(),
        })

    for log in django_logs[:50]:
        combined.append({
            'id': f'django_{log.id}',
            'source': 'django_admin',
            'user': log.user.username if log.user else '未知',
            'action': action_map.get(log.action_flag, 'update'),
            'action_display': log.get_action_flag_display(),
            'resource_type': log.content_type.model if log.content_type else '',
            'resource_id': log.object_id,
            'resource_name': log.object_repr,
            'detail': {'change_message': log.change_message},
            'ip_address': None,
            'created_at': log.action_time.isoformat(),
        })

    combined.sort(key=lambda x: x['created_at'], reverse=True)

    paginator = AdminUserPagination()
    page = paginator.paginate_queryset(combined, request)
    return paginator.get_paginated_response(page)


# ==================== 用户管理 API ====================

@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_user_list(request):
    users = User.objects.select_related('profile').all().order_by('-date_joined')

    search = request.query_params.get('search')
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search)
        )

    is_active = request.query_params.get('is_active')
    if is_active is not None:
        users = users.filter(is_active=is_active.lower() == 'true')

    is_staff = request.query_params.get('is_staff')
    if is_staff is not None:
        users = users.filter(is_staff=is_staff.lower() == 'true')

    paginator = AdminUserPagination()
    page = paginator.paginate_queryset(users, request)

    data = []
    for u in page:
        data.append({
            'id': u.id,
            'username': u.username,
            'email': u.email,
            'is_active': u.is_active,
            'is_staff': u.is_staff,
            'is_superuser': u.is_superuser,
            'date_joined': u.date_joined.isoformat() if u.date_joined else None,
            'last_login': u.last_login.isoformat() if u.last_login else None,
        })

    return paginator.get_paginated_response(data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def admin_user_create(request):
    username = request.data.get('username')
    password = request.data.get('password')
    email = request.data.get('email', '')

    if not username or not password:
        return Response({'message': '用户名和密码不能为空'}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username=username).exists():
        return Response({'message': '用户名已存在'}, status=status.HTTP_400_BAD_REQUEST)

    if email and User.objects.filter(email=email).exists():
        return Response({'message': '邮箱已存在'}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(
        username=username,
        password=password,
        email=email,
        is_active=request.data.get('is_active', True),
        is_staff=request.data.get('is_staff', False),
    )

    log_admin_operation(request, 'create', 'user', user.id, username)

    return Response({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'is_active': user.is_active,
        'is_staff': user.is_staff,
        'message': '创建成功'
    }, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PATCH'])
@permission_classes([IsAdminUser])
def admin_user_detail(request, pk):
    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response({'message': '用户不存在'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_active': user.is_active,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'date_joined': user.date_joined.isoformat() if user.date_joined else None,
            'last_login': user.last_login.isoformat() if user.last_login else None,
        })

    if request.method == 'PATCH':
        allowed_fields = ['is_active', 'is_staff']
        if request.user.is_superuser and 'is_staff' in request.data:
            pass
        elif not request.user.is_superuser and 'is_staff' in request.data:
            return Response({'message': '仅超级管理员可修改员工状态'}, status=status.HTTP_403_FORBIDDEN)

        changed_fields = {}
        for field in allowed_fields:
            if field in request.data:
                old_val = getattr(user, field)
                new_val = request.data[field]
                if old_val != new_val:
                    changed_fields[field] = {'old': old_val, 'new': new_val}
                setattr(user, field, new_val)
        user.save()

        if changed_fields:
            log_admin_operation(
                request, 'update', 'user', user.id, user.username,
                detail={'changed_fields': changed_fields}
            )

        return Response({'message': '更新成功'})


@api_view(['POST'])
@permission_classes([IsAdminUser])
def admin_user_reset_password(request, pk):
    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response({'message': '用户不存在'}, status=status.HTTP_404_NOT_FOUND)

    new_password = request.data.get('new_password')
    if not new_password:
        return Response({'message': '新密码不能为空'}, status=status.HTTP_400_BAD_REQUEST)

    if len(new_password) < 6:
        return Response({'message': '密码长度不能少于6位'}, status=status.HTTP_400_BAD_REQUEST)

    user.set_password(new_password)
    user.save()

    log_admin_operation(
        request, 'update', 'user', user.id, user.username,
        detail={'action': 'reset_password'}
    )

    return Response({'message': '密码重置成功'})


# ==================== 论坛标签管理 API ====================

@api_view(['GET', 'POST'])
@permission_classes([IsAdminUser])
def admin_forum_tag_list(request):
    if request.method == 'GET':
        tags = ForumTag.objects.all().order_by('id')
        search = request.query_params.get('search')
        if search:
            tags = tags.filter(name__icontains=search)
        data = []
        for t in tags:
            data.append({
                'id': t.id,
                'name': t.name,
                'color': t.color,
                'description': t.description,
                'post_count': t.post_count if hasattr(t, 'post_count') else t.posts.count(),
                'created_at': t.created_at.isoformat() if hasattr(t, 'created_at') and t.created_at else None,
            })
        return Response(data)

    if request.method == 'POST':
        name = request.data.get('name')
        if not name:
            return Response({'message': '标签名称不能为空'}, status=status.HTTP_400_BAD_REQUEST)
        if ForumTag.objects.filter(name=name).exists():
            return Response({'message': '标签名称已存在'}, status=status.HTTP_400_BAD_REQUEST)
        tag = ForumTag.objects.create(
            name=name,
            color=request.data.get('color', '#409EFF'),
            description=request.data.get('description', ''),
        )
        log_admin_operation(request, 'create', 'tag', tag.id, name)
        return Response({
            'id': tag.id,
            'name': tag.name,
            'color': tag.color,
            'description': tag.description,
            'message': '创建成功'
        }, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAdminUser])
def admin_forum_tag_detail(request, pk):
    try:
        tag = ForumTag.objects.get(pk=pk)
    except ForumTag.DoesNotExist:
        return Response({'message': '标签不存在'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response({
            'id': tag.id,
            'name': tag.name,
            'color': tag.color,
            'description': tag.description,
        })

    if request.method in ('PUT', 'PATCH'):
        for field in ['name', 'color', 'description']:
            if field in request.data:
                setattr(tag, field, request.data[field])
        tag.save()
        log_admin_operation(request, 'update', 'tag', tag.id, tag.name)
        return Response({'message': '更新成功'})

    if request.method == 'DELETE':
        name = tag.name
        tag.delete()
        log_admin_operation(request, 'delete', 'tag', pk, name)
        return Response({'message': '删除成功'})


# ==================== 论坛公告管理 API ====================

@api_view(['GET', 'POST'])
@permission_classes([IsAdminUser])
def admin_forum_announcement_list(request):
    if request.method == 'GET':
        announcements = ForumAnnouncement.objects.all().order_by('-is_pinned', '-publish_date')
        data = []
        for a in announcements:
            data.append({
                'id': a.id,
                'title': a.title,
                'content': a.content,
                'is_active': a.is_active,
                'is_pinned': a.is_pinned,
                'order': a.order if hasattr(a, 'order') else 0,
                'publish_date': a.publish_date.isoformat() if a.publish_date else None,
            })
        return Response(data)

    if request.method == 'POST':
        announcement = ForumAnnouncement.objects.create(
            title=request.data.get('title', ''),
            content=request.data.get('content', ''),
            is_active=request.data.get('is_active', True),
            is_pinned=request.data.get('is_pinned', False),
            order=request.data.get('order', 0),
        )
        log_admin_operation(request, 'create', 'announcement', announcement.id, announcement.title)
        return Response({
            'id': announcement.id,
            'title': announcement.title,
            'message': '创建成功'
        }, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAdminUser])
def admin_forum_announcement_detail(request, pk):
    try:
        announcement = ForumAnnouncement.objects.get(pk=pk)
    except ForumAnnouncement.DoesNotExist:
        return Response({'message': '公告不存在'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response({
            'id': announcement.id,
            'title': announcement.title,
            'content': announcement.content,
            'is_active': announcement.is_active,
            'is_pinned': announcement.is_pinned,
            'order': announcement.order if hasattr(announcement, 'order') else 0,
        })

    if request.method in ('PUT', 'PATCH'):
        for field in ['title', 'content', 'is_active', 'is_pinned', 'order']:
            if field in request.data:
                setattr(announcement, field, request.data[field])
        announcement.save()
        log_admin_operation(request, 'update', 'announcement', announcement.id, announcement.title)
        return Response({'message': '更新成功'})

    if request.method == 'DELETE':
        title = announcement.title
        announcement.delete()
        log_admin_operation(request, 'delete', 'announcement', pk, title)
        return Response({'message': '删除成功'})


# ==================== 论坛版规管理 API ====================

@api_view(['GET', 'POST'])
@permission_classes([IsAdminUser])
def admin_forum_rule_list(request):
    if request.method == 'GET':
        rules = ForumRule.objects.all().order_by('order', 'id')
        data = []
        for r in rules:
            data.append({
                'id': r.id,
                'content': r.content,
                'is_active': r.is_active,
                'order': r.order if hasattr(r, 'order') else 0,
            })
        return Response(data)

    if request.method == 'POST':
        rule = ForumRule.objects.create(
            content=request.data.get('content', ''),
            is_active=request.data.get('is_active', True),
            order=request.data.get('order', 0),
        )
        log_admin_operation(request, 'create', 'rule', rule.id, rule.content[:50])
        return Response({
            'id': rule.id,
            'content': rule.content,
            'message': '创建成功'
        }, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAdminUser])
def admin_forum_rule_detail(request, pk):
    try:
        rule = ForumRule.objects.get(pk=pk)
    except ForumRule.DoesNotExist:
        return Response({'message': '版规不存在'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response({
            'id': rule.id,
            'content': rule.content,
            'is_active': rule.is_active,
            'order': rule.order if hasattr(rule, 'order') else 0,
        })

    if request.method in ('PUT', 'PATCH'):
        for field in ['content', 'is_active', 'order']:
            if field in request.data:
                setattr(rule, field, request.data[field])
        rule.save()
        log_admin_operation(request, 'update', 'rule', rule.id, rule.content[:50])
        return Response({'message': '更新成功'})

    if request.method == 'DELETE':
        content = rule.content[:50]
        rule.delete()
        log_admin_operation(request, 'delete', 'rule', pk, content)
        return Response({'message': '删除成功'})


# ==================== 举报管理 API ====================

@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_forum_report_list(request):
    reports = ForumReport.objects.select_related('reporter', 'post', 'handler').all().order_by('-created_at')
    status_filter = request.query_params.get('status')
    if status_filter:
        reports = reports.filter(status=status_filter)

    data = []
    for r in reports:
        report_data = {
            'id': r.id,
            'reason': r.reason,
            'description': r.description if hasattr(r, 'description') else '',
            'status': r.status,
            'handler_note': r.handler_note if hasattr(r, 'handler_note') else '',
            'created_at': r.created_at.isoformat() if hasattr(r, 'created_at') and r.created_at else None,
        }
        if hasattr(r, 'reporter') and r.reporter:
            report_data['reporter_id'] = r.reporter.id
            report_data['reporter_name'] = r.reporter.username
        if hasattr(r, 'post') and r.post:
            report_data['post_id'] = r.post.id
            report_data['post_title'] = r.post.title
        if hasattr(r, 'handler') and r.handler:
            report_data['handler_name'] = r.handler.username
        data.append(report_data)

    return Response(data)


@api_view(['GET', 'PATCH'])
@permission_classes([IsAdminUser])
def admin_forum_report_detail(request, pk):
    try:
        report = ForumReport.objects.get(pk=pk)
    except ForumReport.DoesNotExist:
        return Response({'message': '举报不存在'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        data = {
            'id': report.id,
            'reason': report.reason,
            'description': report.description if hasattr(report, 'description') else '',
            'status': report.status,
            'handler_note': report.handler_note if hasattr(report, 'handler_note') else '',
            'created_at': report.created_at.isoformat() if hasattr(report, 'created_at') and report.created_at else None,
            'handled_at': report.handled_at.isoformat() if hasattr(report, 'handled_at') and report.handled_at else None,
        }
        if hasattr(report, 'reporter') and report.reporter:
            data['reporter_id'] = report.reporter.id
            data['reporter_name'] = report.reporter.username
        if hasattr(report, 'post') and report.post:
            data['post_id'] = report.post.id
            data['post_title'] = report.post.title
        if hasattr(report, 'comment') and report.comment:
            data['comment_id'] = report.comment.id
            data['comment_preview'] = report.comment.content[:50]
        if hasattr(report, 'handler') and report.handler:
            data['handler_name'] = report.handler.username
        return Response(data)

    if request.method == 'PATCH':
        new_status = request.data.get('status')
        if new_status:
            report.status = new_status
        if 'handler_note' in request.data:
            report.handler_note = request.data['handler_note']
        report.handler = request.user
        report.handled_at = timezone.now()
        report.save()
        log_admin_operation(
            request, 'update', 'report', report.id,
            detail={'status': new_status, 'handler_note': request.data.get('handler_note', '')}
        )
        return Response({'message': '处理成功'})


# ==================== 帖子管理 API ====================

@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_forum_post_list(request):
    posts = ForumPost.objects.select_related('author').prefetch_related('tags').all().order_by('-created_at')

    status_filter = request.query_params.get('status')
    if status_filter:
        posts = posts.filter(status=status_filter)

    search = request.query_params.get('search')
    if search:
        posts = posts.filter(Q(title__icontains=search) | Q(author__username__icontains=search))

    is_pinned = request.query_params.get('is_pinned')
    if is_pinned is not None:
        posts = posts.filter(is_pinned=is_pinned.lower() == 'true')

    is_featured = request.query_params.get('is_featured')
    if is_featured is not None:
        posts = posts.filter(is_featured=is_featured.lower() == 'true')

    paginator = AdminUserPagination()
    page = paginator.paginate_queryset(posts, request)

    data = []
    for p in page:
        data.append({
            'id': p.id,
            'title': p.title,
            'author': p.author.username,
            'status': p.status,
            'is_pinned': p.is_pinned,
            'is_featured': p.is_featured,
            'is_locked': p.is_locked,
            'view_count': p.view_count,
            'like_count': p.like_count,
            'comment_count': p.comment_count,
            'tags': [t.name for t in p.tags.all()],
            'created_at': p.created_at.isoformat(),
            'updated_at': p.updated_at.isoformat(),
        })

    return paginator.get_paginated_response(data)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAdminUser])
def admin_forum_post_detail(request, pk):
    try:
        post = ForumPost.objects.select_related('author').prefetch_related('tags').get(pk=pk)
    except ForumPost.DoesNotExist:
        return Response({'message': '帖子不存在'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response({
            'id': post.id,
            'title': post.title,
            'content': post.content,
            'author': post.author.username,
            'author_id': post.author.id,
            'status': post.status,
            'is_pinned': post.is_pinned,
            'is_featured': post.is_featured,
            'is_locked': post.is_locked,
            'view_count': post.view_count,
            'like_count': post.like_count,
            'comment_count': post.comment_count,
            'favorite_count': post.favorite_count,
            'tags': [t.name for t in post.tags.all()],
            'created_at': post.created_at.isoformat(),
            'updated_at': post.updated_at.isoformat(),
            'last_reply_at': post.last_reply_at.isoformat() if post.last_reply_at else None,
        })

    if request.method == 'PATCH':
        allowed_fields = ['status', 'is_pinned', 'is_featured', 'is_locked']
        changed = {}
        for field in allowed_fields:
            if field in request.data:
                old_val = getattr(post, field)
                new_val = request.data[field]
                if old_val != new_val:
                    changed[field] = {'old': old_val, 'new': new_val}
                setattr(post, field, new_val)
        post.save()
        if changed:
            log_admin_operation(
                request, 'update', 'post', post.id, post.title,
                detail={'changed_fields': changed}
            )
        return Response({'message': '更新成功'})

    if request.method == 'DELETE':
        title = post.title
        post.status = 'deleted'
        post.save()
        log_admin_operation(request, 'delete', 'post', post.id, title)
        return Response({'message': '删除成功'})


# ==================== 创作管理 API ====================

@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_creation_list(request):
    creations = UserCreation.objects.select_related('author').all().order_by('-created_at')

    status_filter = request.query_params.get('status')
    if status_filter:
        creations = creations.filter(status=status_filter)

    creation_type = request.query_params.get('type')
    if creation_type:
        creations = creations.filter(type=creation_type)

    search = request.query_params.get('search')
    if search:
        creations = creations.filter(Q(title__icontains=search) | Q(author__username__icontains=search))

    is_featured = request.query_params.get('is_featured')
    if is_featured is not None:
        creations = creations.filter(is_featured=is_featured.lower() == 'true')

    paginator = AdminUserPagination()
    page = paginator.paginate_queryset(creations, request)

    data = []
    for c in page:
        data.append({
            'id': c.id,
            'title': c.title,
            'author': c.author.username,
            'type': c.type,
            'status': c.status,
            'is_featured': c.is_featured,
            'is_public': c.is_public,
            'view_count': c.view_count,
            'like_count': c.like_count,
            'comment_count': c.comment_count,
            'created_at': c.created_at.isoformat(),
        })

    return paginator.get_paginated_response(data)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAdminUser])
def admin_creation_detail(request, pk):
    try:
        creation = UserCreation.objects.select_related('author', 'heritage').get(pk=pk)
    except UserCreation.DoesNotExist:
        return Response({'message': '创作不存在'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response({
            'id': creation.id,
            'title': creation.title,
            'description': creation.description,
            'type': creation.type,
            'status': creation.status,
            'author': creation.author.username,
            'author_id': creation.author.id,
            'heritage_id': creation.heritage_id,
            'heritage_name': creation.heritage.name if creation.heritage else None,
            'is_featured': creation.is_featured,
            'is_public': creation.is_public,
            'view_count': creation.view_count,
            'like_count': creation.like_count,
            'comment_count': creation.comment_count,
            'share_count': creation.share_count,
            'tags': creation.tags,
            'created_at': creation.created_at.isoformat(),
            'updated_at': creation.updated_at.isoformat(),
            'published_at': creation.published_at.isoformat() if creation.published_at else None,
        })

    if request.method == 'PATCH':
        allowed_fields = ['status', 'is_featured', 'is_public']
        changed = {}
        for field in allowed_fields:
            if field in request.data:
                old_val = getattr(creation, field)
                new_val = request.data[field]
                if old_val != new_val:
                    changed[field] = {'old': old_val, 'new': new_val}
                setattr(creation, field, new_val)
        creation.save()
        if changed:
            log_admin_operation(
                request, 'update', 'creation', creation.id, creation.title,
                detail={'changed_fields': changed}
            )
        return Response({'message': '更新成功'})

    if request.method == 'DELETE':
        title = creation.title
        creation.delete()
        log_admin_operation(request, 'delete', 'creation', creation.id, title)
        return Response({'message': '删除成功'})
