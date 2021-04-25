from django.conf.urls import url
from django.contrib import admin
from django.views.static import serve

from BBS import settings
from app01 import views

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    # 注册
    url(r'^register/', views.register, name='reg'),

    # 登录
    url(r'^login/', views.login, name='login'),

    # 图片验证码相关操作
    url(r'^get_code/', views.get_code, name='gc'),

    # 首页
    url(r'^home/', views.home, name='home'),
    url(r'^$', views.home, name='home'),

    # 修改密码
    url(r'^set_password/', views.set_password, name='set_pwd'),

    # 退出登陆
    url(r'^logout/', views.logout, name='logout'),

    # 暴露后端指定文件夹资源
    url(r'^media/(?P<path>.*)', serve, {'document_root': settings.MEDIA_ROOT}),

    # 点赞点踩
    url(r'^up_or_down/', views.up_or_down, name='up_or_down'),
    # 评论
    url(r'^comment/', views.comment, name='comment'),

    # 后台管理
    url(r'^backend/', views.backend, name='backend'),

    # 添加文章
    url(r'^add/article/', views.add_article, name='add_article'),
    url(r'^delete/article/(\d+)', views.delete_article, name='delete_article'),
    url(r'^edit/article/(\d+)', views.edit_article, name='edit_article'),

    # 编辑器上传图片接口
    url(r'^upload_image/', views.upload_image, name='upload_image'),

    # 修改用户头像
    url(r'^set/avatar/', views.set_avatar, name='set_avatar'),

    # 个人站点页面搭建
    url(r'^(?P<username>\w+)/$', views.site, name='site'),

    url(r'^(?P<username>\w+)/(?P<condition>category|tag|archive)/(?P<param>.*)/', views.site),

    # 文章详情页
    url(r'^(?P<username>\w+)/article/(?P<article_id>\d+)/', views.article_detail, name='article_detail'),

    url(r'^happy/', views.joke, name='joke'),

]
