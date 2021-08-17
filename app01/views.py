import json
import os
import random
import uuid
from io import BytesIO
from django.views.decorators.clickjacking import xframe_options_sameorigin
from PIL import Image, ImageDraw, ImageFont
from bs4 import BeautifulSoup
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F
from django.http import JsonResponse
from django.shortcuts import render, HttpResponse, redirect

from BBS import settings
from app01 import models
from app01.myforms.register_forms import MyRegForm
from app01.utils.mytags import Pagination


def register(request):
    
    form_obj = MyRegForm()
    if request.method == 'POST':
        back_dic = {"code": 1000, 'msg': ''}
        # 校验数据是否合法
        form_obj = MyRegForm(request.POST)
        # 判断数据是否合法
        if form_obj.is_valid():
            # 将校验通过的数据字典赋值给一个变量
            clean_data = form_obj.cleaned_data
            # 将字典里面的confirm_password键值对删除
            clean_data.pop('confirm_password')
            # 用户头像
            file_obj = request.FILES.get('avatar')
            """针对用户头像一定要判断是否传值 不能直接添加到字典里面去"""
            if file_obj:
                clean_data['avatar'] = file_obj
            # 站点名=用户名
            clean_data['blog'] = models.Blog.objects.create(site_name=clean_data.get('username'))
            # 直接操作数据库保存数据
            models.UserInfo.objects.create_user(**clean_data)
            back_dic['url'] = '/login/'
        else:
            back_dic['code'] = 2000
            back_dic['msg'] = form_obj.errors
        return JsonResponse(back_dic)
    return render(request, 'register.html', locals())


def login(request):
    if request.method == 'POST':
        back_dic = {'code': 1000, 'msg': ''}
        username = request.POST.get('username')
        password = request.POST.get('password')
        code = request.POST.get('code')
        # 1 先校验验证码是否正确      自己决定是否忽略            统一转大写或者小写再比较
        if request.session.get('code').upper() == code.upper():
            # 2 校验用户名和密码是否正确
            user_obj = auth.authenticate(
                request, username=username, password=password)
            if user_obj:
                # 保存用户状态
                auth.login(request, user_obj)
                back_dic['url'] = '/home/'
            else:
                back_dic['code'] = 2000
                back_dic['msg'] = '用户名或密码错误'
        else:
            back_dic['code'] = 3000
            back_dic['msg'] = '验证码错误'
        return JsonResponse(back_dic)
    return render(request, 'login.html')


def get_random():
    return random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)


def get_code(request):
    # 图片验证码
    img_obj = Image.new('RGB', (430, 35), get_random())
    img_draw = ImageDraw.Draw(img_obj)  # 产生一个画笔对象
    img_font = ImageFont.truetype('static/font/222.ttf', 30)  # 字体样式 大小

    # 随机验证码  五位数的随机验证码  数字 小写字母 大写字母
    code = ''
    for i in range(5):
        random_upper = chr(random.randint(65, 90))
        random_lower = chr(random.randint(97, 122))
        random_int = str(random.randint(0, 9))
        # 从上面三个里面随机选择一个
        tmp = random.choice([random_lower, random_upper, random_int])
        # 将产生的随机字符串写入到图片上
        """
        一个个写能够控制每个字体的间隙 而生成好之后再写的话间隙就没法控制了
        """
        img_draw.text((i * 60 + 60, -2), tmp, get_random(), img_font)
        # 拼接随机字符串
        code += tmp
    print(code)
    # 随机验证码在登陆的视图函数里面需要用到 要比对 所以要找地方存起来并且其他视图函数也能拿到
    request.session['code'] = code
    io_obj = BytesIO()
    img_obj.save(io_obj, 'png')
    return HttpResponse(io_obj.getvalue())


def home(request):
    # 查询本网站所有的文章数据展示的前端页面 这里可以使用分页器做分页 但是我不做了 你们自己课下加
    article_queryset = models.Article.objects.all()
    return render(request, 'home.html', locals())


@login_required
def set_password(request):
    if request.is_ajax():
        back_dic = {'code': 1000, 'msg': ''}
        if request.method == 'POST':
            old_password = request.POST.get('old_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            is_right = request.user.check_password(old_password)
            if is_right:
                if new_password == confirm_password:
                    request.user.set_password(new_password)
                    request.user.save()
                    back_dic['msg'] = '修改成功'
                else:
                    back_dic['code'] = 1001
                    back_dic['msg'] = '两次密码不一致'
            else:
                back_dic['code'] = 1002
                back_dic['msg'] = '原密码错误'
        return JsonResponse(back_dic)


@login_required
def logout(request):
    auth.logout(request)
    return redirect('/home/')


def site(request, username, **kwargs):
    """
    :param request:
    :param username:
    :param kwargs: 如果该参数有值 也就意味着需要对article_list做额外的筛选操作
    :return:
    """
    # 先校验当前用户名对应的个人站点是否存在
    user_obj = models.UserInfo.objects.filter(username=username).first()
    # 用户如果不存在应该返回一个404页面
    if not user_obj:
        return render(request, 'errors.html')
    blog = user_obj.blog
    # 查询当前个人站点下的所有的文章
    # queryset对象 侧边栏的筛选其实就是对article_list再进一步筛选
    article_list = models.Article.objects.filter(blog=blog)
    if kwargs:
        # print(kwargs)  # {'condition': 'tag', 'param': '1'}
        condition = kwargs.get('condition')
        param = kwargs.get('param')
        # 判断用户到底想按照哪个条件筛选数据
        if condition == 'category':
            article_list = article_list.filter(category_id=param)
        elif condition == 'tag':
            article_list = article_list.filter(tags__id=param)
        else:
            year, month = param.split('-')  # 2020-11  [2020,11]
            article_list = article_list.filter(create_time__year=year, create_time__month=month)
    return render(request, 'site.html', locals())


def article_detail(request, username, article_id):
    """
    应该需要校验username和article_id是否存在,但是我们这里先只完成正确的情况
    默认不会瞎搞
    :param request:
    :param username:
    :param article_id:
    :return:
    """
    user_obj = models.UserInfo.objects.filter(username=username).first()
    blog = user_obj.blog
    # 先获取文章对象
    article_obj = models.Article.objects.filter(pk=article_id, blog__userinfo__username=username).first()
    if not article_obj:
        return render(request, 'errors.html')
    # 获取当前 文章所有的评论内容
    comment_list = models.Comment.objects.filter(article=article_obj)
    return render(request, 'article_detail.html', locals())


def up_or_down(request):
    """
    1.校验用户是否登陆
    2.判断当前文章是否是当前用户自己写的(自己不能点自己的文章)
    3.当前用户是否已经给当前文章点过了
    4.操作数据库了
    :param request:
    :return:
    """
    if request.is_ajax():
        back_dic = {'code': 1000, 'msg': ''}
        # 1 先判断当前用户是否登陆
        if request.user.is_authenticated:
            article_id = request.POST.get('article_id')
            is_up = request.POST.get('is_up')
            # print(is_up,type(is_up))  # true <class 'str'>
            is_up = json.loads(is_up)  # 记得转换
            # print(is_up, type(is_up))  # True <class 'bool'>
            # 2 判断当前文章是否是当前用户自己写的  根据文章id查询文章对象 根据文章对象查作者 根request.user比对
            article_obj = models.Article.objects.filter(pk=article_id).first()
            if not article_obj.blog.userinfo == request.user:
                # 3 校验当前用户是否已经点了      哪个地方记录了用户到底点没点
                is_click = models.UpAndDown.objects.filter(user=request.user, article=article_obj)
                if not is_click:
                    # 4 操作数据库 记录数据      要同步操作普通字段
                    # 判断当前用户点了赞还是踩 从而决定给哪个字段加一
                    if is_up:
                        # 给点赞数加一
                        models.Article.objects.filter(pk=article_id).update(up_num=F('up_num') + 1)
                        back_dic['msg'] = '点赞成功'
                    else:
                        # 给点踩数加一
                        models.Article.objects.filter(pk=article_id).update(down_num=F('down_num') + 1)
                        back_dic['msg'] = '点踩成功'
                    # 操作点赞点踩表
                    models.UpAndDown.objects.create(user=request.user, article=article_obj, is_up=is_up)
                else:
                    back_dic['code'] = 1001
                    # 这里你可以做的更加的详细 提示用户到底点了赞还是点了踩
                    back_dic['msg'] = '你已经点过了,不能再点了'
            else:
                back_dic['code'] = 1002
                back_dic['msg'] = '你个臭不要脸的!不能给自己点赞'
        else:
            back_dic['code'] = 1003
            back_dic['msg'] = '请先<a href="/login/">登陆</a>'
        return JsonResponse(back_dic)


def comment(request):
    # 自己也可以给自己的文章评论内容
    if request.is_ajax():
        back_dic = {'code': 1000, 'msg': ""}
        if request.method == 'POST':
            if request.user.is_authenticated:
                article_id = request.POST.get('article_id')
                content = request.POST.get("content")
                parent_id = request.POST.get('parent_id')
                # 直接操作评论表 存储数据      两张表
                with transaction.atomic():
                    models.Article.objects.filter(pk=article_id).update(comment_num=F('comment_num') + 1)
                    models.Comment.objects.create(user=request.user, article_id=article_id, content=content,                                                  parent_id=parent_id)
                back_dic['msg'] = '评论成功'
            else:
                back_dic['code'] = 1001
                back_dic['msg'] = '用户未登陆'
            return JsonResponse(back_dic)


@login_required
def backend(request):
    # 获取当前用户对象所有的文章展示到页面
    article_list = models.Article.objects.filter(blog=request.user.blog)

    page_obj = Pagination(current_page=request.GET.get('page', 1), all_count=article_list.count())
    page_queryset = article_list[page_obj.start:page_obj.end]
    return render(request, 'backend/backend.html', locals())


from django.views.decorators.csrf import csrf_exempt


@login_required
def add_article(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        # print(content)
        category_id = request.POST.get("category")
        tag_id_list = request.POST.getlist('tag')
        # 模块使用
        soup = BeautifulSoup(content, 'html.parser')
        tags = soup.find_all()
        # 获取所有的标签
        for tag in tags:
            # print(tag.name)  # 获取页面所有的标签
            # 针对script标签 直接删除
            if tag.name == 'script':
                # 删除标签
                tag.name = '#script'
        # 文章简介
        # 1 先简单暴力的直接切去content 150个字符
        # desc = content[0:150]
        # 2 截取文本150个
        desc = soup.text[0:150]
        article_obj = models.Article.objects.create(
            title=title,
            content=str(soup),
            desc=desc,
            category_id=category_id,
            blog=request.user.blog
        )
        # 文章和标签的关系表 是我们自己创建的 没法使用add set remove clear方法
        # 自己去操作关系表   一次性可能需要创建多条数据      批量插入bulk_create()
        article_obj_list = []
        for i in tag_id_list:
            tag_article_obj = models.Article2Tag(article=article_obj, tag_id=i)
            article_obj_list.append(tag_article_obj)
        # 批量插入数据
        models.Article2Tag.objects.bulk_create(article_obj_list)
        # 跳转到后台管理文章展示页
        return redirect('/backend/')
    category_list = models.Category.objects.filter(blog=request.user.blog)
    tag_list = models.Tag.objects.filter(blog=request.user.blog)
    return render(request, 'backend/add_article.html', locals())


@login_required
def edit_article(request, edit_id):
    """
    编辑文章，需要文章id
    """
    edit_obj = models.Article.objects.filter(pk=edit_id).first()
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        print(content)
        category_id = request.POST.get("category")
        tag_id_list = request.POST.getlist('tag')
        soup = BeautifulSoup(content, 'html.parser')
        tags = soup.find_all()
        for tag in tags:
            if tag.name == 'script':
                tag.name = '#script'

        desc = soup.text[0:150]
        article_obj = models.Article.objects.filter(pk=edit_id).update(
            title=title,
            content=str(soup),
            desc=desc,
            category_id=category_id,
            blog=request.user.blog
        )

        return redirect('/backend/')

    category_list = models.Category.objects.filter(blog=request.user.blog)
    tag_list = models.Tag.objects.filter(blog=request.user.blog)
    return render(request, 'backend/edit_article.html', locals())


@login_required
def delete_article(request, delete_id):
    models.Article.objects.filter(pk=delete_id).delete()
    return redirect('/backend/')


@xframe_options_sameorigin
@csrf_exempt
def upload_image(request):
    back_dic = {"success": 1}  # 先提前定义返回给编辑器的数据格式
    # 用户写文章上传的图片 也算静态资源 也应该防盗media文件夹下
    if request.method == "POST":
        # print(request)
        file_obj = request.FILES.get('imgFile') or request.FILES.get('editormd-image-file')
        filename = str(uuid.uuid4()) + file_obj.name

        file_path = os.path.join(settings.BASE_DIR, 'media', 'article_img')

        if not os.path.isdir(file_path):
            os.mkdir(file_path)  # 创建一层目录结构  article_img
        file_dir = os.path.join(file_path, filename)
        with open(file_dir, 'wb') as f:
            for line in file_obj:
                f.write(line)
        print(file_path)
        back_dic['url'] = '/media/article_img/%s' % filename
    back_dic["message"] = "2313"
    print(back_dic)
    return JsonResponse(back_dic)


@login_required
def set_avatar(request):
    if request.method == 'POST':
        file_obj = request.FILES.get('avatar')
        user_obj = request.user
        user_obj.avatar = file_obj
        user_obj.save()
        return redirect('/home/')
    blog = request.user.blog
    username = request.user.username
    return render(request, 'set_avatar.html', locals())


def joke(request):
    article_list = models.Joke.objects.all()
    return render(request, 'joke.html', locals())
