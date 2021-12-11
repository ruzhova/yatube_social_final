from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from yatube.settings import NUM_OF_POSTS

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User


def paginator_func(request, posts):
    paginator = Paginator(posts, NUM_OF_POSTS)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


def index(request):
    post_list = Post.objects.all()
    page_obj = paginator_func(request, post_list)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    page_obj = paginator_func(request, posts)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    writer = get_object_or_404(User, username=username)
    writers_posts = writer.posts.all()
    page_obj = paginator_func(request, writers_posts)

    if (request.user.is_authenticated and Follow.objects.filter(
            user=request.user, author=writer)):
        following = True
    else:
        following = False

    context = {
        'writer': writer,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    first_symbols = post.text[:30]
    form = CommentForm(request.POST or None)
    comments = post.comments.all()
    context = {
        'post': post,
        'first_symbols': first_symbols,
        'form': form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            new_post = form.save(commit=False)
            new_post.author = request.user
            new_post.save()
            return redirect('posts:profile', username=request.user)
        return render(request, 'posts/create_post.html', {'form': form})
    form = PostForm()
    context = {
        'form': form
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    editable_post = get_object_or_404(Post, id=post_id)
    if request.user != editable_post.author:
        return redirect('posts:post_detail', post_id)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=editable_post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)

    context = {
        'is_edit': True,
        'form': form,
        'editable_post': editable_post,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    following = Post.objects.filter(author__following__user=request.user)
    page_obj = paginator_func(request, following)
    context = {
        'page_obj': page_obj
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    writer = get_object_or_404(User, username=username)
    if writer != request.user:
        Follow.objects.get_or_create(user=request.user, author=writer)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    writer = get_object_or_404(User, username=username)
    if writer != request.user:
        Follow.objects.filter(user=request.user, author=writer).delete()
    return redirect('posts:profile', username=username)
