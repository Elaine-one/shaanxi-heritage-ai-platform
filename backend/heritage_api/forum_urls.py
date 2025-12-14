from django.urls import path, include
from . import forum_views

app_name = 'forum'

urlpatterns = [
    # 帖子相关
    path('posts/', forum_views.ForumPostListView.as_view(), name='post-list'),
    path('posts/<int:pk>/', forum_views.ForumPostDetailView.as_view(), name='post-detail'),
    path('posts/<int:post_id>/like/', forum_views.toggle_post_like, name='post-like'),
    path('posts/<int:post_id>/favorite/', forum_views.toggle_post_favorite, name='post-favorite'),
    path('posts/<int:post_id>/report/', forum_views.report_post, name='post-report'),
    path('posts/<int:post_id>/view/', forum_views.increment_post_view, name='post-view'),
    
    # 管理员功能
    path('posts/<int:post_id>/pin/', forum_views.toggle_post_pin, name='post-pin'),
    path('posts/<int:post_id>/feature/', forum_views.toggle_post_feature, name='post-feature'),
    
    # 评论相关
    path('posts/<int:post_id>/comments/', forum_views.ForumCommentListCreateView.as_view(), name='comment-list'),
    path('comments/<int:comment_id>/like/', forum_views.toggle_comment_like, name='comment-like'),
    path('comments/<int:comment_id>/report/', forum_views.report_comment, name='comment-report'),
    path('comments/<int:comment_id>/delete/', forum_views.delete_comment, name='comment-delete'),
    
    # 标签和公告
    path('tags/', forum_views.ForumTagListView.as_view(), name='tag-list'),
    path('announcements/', forum_views.ForumAnnouncementListView.as_view(), name='announcement-list'),
    
    # 用户相关
    path('users/<int:user_id>/follow-status/', forum_views.check_user_follow_status, name='check-user-follow-status'),
    path('users/<int:user_id>/follow/', forum_views.toggle_user_follow, name='user-follow'),
    path('users/<int:user_id>/posts/', forum_views.user_posts, name='user-posts'),
    path('users/search/', forum_views.search_users, name='user-search'),
    path('users/active/', forum_views.active_users, name='active-users'),
    path('users/stats/', forum_views.ForumUserStatsListView.as_view(), name='user-stats'),
    
    # 个人中心
    path('my/favorites/', forum_views.user_favorites, name='my-favorites'),
    path('my/notifications/', forum_views.user_notifications, name='my-notifications'),
    path('my/following/', forum_views.user_following_list, name='my-following'),
    path('my/followers/', forum_views.user_followers_list, name='my-followers'),
    
    # 文件上传
    path('upload/image/', forum_views.upload_image, name='upload-image'),
]