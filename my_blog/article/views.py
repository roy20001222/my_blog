# 重定向模块
from django.shortcuts import render, redirect
from django.http import HttpResponse
# 引入刚才定义的ArticlePostForm表单类
from .forms import ArticlePostForm
# User模型
from django.contrib.auth.models import User
from .models import ArticlePost
import markdown
from django.contrib.auth.decorators import login_required
# 分页模块
from django.core.paginator import Paginator
# 引入 Q 对象
from django.db.models import Q
from comment.models import Comment
# Create your views here.


def index(request):
    return render(request, '3D场景.html')


def article_list(request):
    search = request.GET.get('search')
    order = request.GET.get('order')
    # 用户搜索逻辑
    if search:
        if order == 'total_views':
            # 用 Q对象 进行联合搜索
            article_list = ArticlePost.objects.filter(
                Q(title__icontains=search) |
                Q(body__icontains=search)
            ).order_by('-total_views')
        else:
            article_list = ArticlePost.objects.filter(
                Q(title__icontains=search) |
                Q(body__icontains=search)
            )
    else:
        # 将 search 参数重置为空
        search = ''
        if order == 'total_views':
            article_list = ArticlePost.objects.all().order_by('-total_views')
        else:
            article_list = ArticlePost.objects.all()
    # 每页显示1篇文章
    paginator = Paginator(article_list, 3)
    # 获取url中页码
    page = request.GET.get('page')
    # 将导航对象相应的页码内容返回给 articles
    articels = paginator.get_page(page)
    # 需要传递给模板（templates）的对象
    context = {'articles': articels, 'order': order, 'search': search}
    # render函数：载入模板，并返回context对象
    return render(request, 'article/list.html', context)


def article_detail(request, id):
    article = ArticlePost.objects.get(id=id)
    comments = Comment.objects.filter(article=id)
    # 浏览量+=1
    article.total_views += 1
    article.save(update_fields=['total_views'])
    article.body = markdown.markdown(
        article.body,
        extensions=[
            # 包含 缩写、表格等常用扩展
            'markdown.extensions.extra',
            # 语法高亮扩展
            'markdown.extensions.codehilite',
            # 目录扩展
            'markdown.extensions.toc',
        ]
    )
    md = markdown.Markdown(
        extensions=[
        'markdown.extensions.extra',
        'markdown.extensions.codehilite',
        'markdown.extensions.toc',
        ]
    )
    article.body = md.convert(article.body)
    context = {'article': article, 'toc': md.toc, 'comments': comments}
    return render(request, 'article/detail.html', context)


# 文章视图
@login_required(login_url='/userprofile/login/')
def article_create(request):
    # # 判断用户是否提交数据
    if request.method == 'POST':
        # 将提交的数据赋值到表单实例中
        article_post_form = ArticlePostForm(data=request.POST)
        # 判断提交的数据是否满足模型的要求
        if article_post_form.is_valid():
            # 保存数据，但暂时不提交到数据库中
            new_article = article_post_form.save(commit=False)
            # 此时请重新创建用户，并传入此用户的id
            # 指定目前登录的用户为作者
            new_article.author = User.objects.get(id=request.user.id)
            # 保存至数据库
            new_article.save()
            # 返回列表  重定向
            return redirect("article:article_list")
        # 错误提示
        else:
            return HttpResponse('表单内容有误，重写')
    # 如果用户请求获取数据
    else:
        # 创建表单实例
        article_post_form = ArticlePostForm()
        # 赋值上下文
        context = {'article_post_form': article_post_form}
        # 返回模板
        return render(request, 'article/create.html', context)


# 删除
def article_delete(request, id):
    # 根据id删除
    article = ArticlePost.objects.get(id=id)
    # 调用delete()方法
    article.delete()
    # 重定向
    return redirect('article:article_list')


# safe_delete
def article_safe_delete(request, id):
    if request.method == "POST":
        article = ArticlePost.objects.get(id=id)
        article.delete()
        return redirect('article:article_list')
    else:
        return HttpResponse('ALLOW POST')


# 更新文章
@login_required(login_url='/userprofile/login/')
def article_update(request, id):
    """
       更新文章的视图函数
       通过POST方法提交表单，更新titile、body字段
       GET方法进入初始表单页面
       id： 文章的 id
    """
    article = ArticlePost.objects.get(id=id)
    # 过滤非作者的用户
    if request.user != article.author:
        return HttpResponse("抱歉，你无权修改这篇文章。")
    if request.method == 'POST':
        # 将提交的数据赋值到表单实例中
        article_post_form = ArticlePostForm(data=request.POST)
        # 判断数据是否满足数据要求
        if article_post_form.is_valid():
            article.title = request.POST['title']
            article.body = request.POST['body']
            article.save()
            # 重定向 返回文章详情页， 需要传id
            return redirect('article:article_detail', id=id)
        else:
            return HttpResponse('内容有误')
    else:
        # 创建表单实例
        article_post_form = ArticlePostForm()
        # 赋值上下文，将 article 文章对象也传递进去，以便提取旧的内容
        context = {'article': article, 'article_post_form': article_post_form}
        return render(request, 'article/update.html', context)












