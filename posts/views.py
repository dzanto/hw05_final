from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect, get_list_or_404
from .models import Post, Group, User, Comment, Follow
from .forms import PostForm, CommentForm
from django.core.paginator import Paginator


def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, 10)

    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'index.html',
        {'page': page, 'paginator': paginator}
    )


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'group.html',
        {"group": group, 'page': page, 'paginator': paginator}
    )


@login_required
def new_post(request):
    title_post = "Добавить запись"
    button_post = "Добавить"

    if request.method != "POST":
        form = PostForm()
        return render(request, "post_new.html", {"form": form, "title_post": title_post, "button_post": button_post})

    form = PostForm(request.POST)
    if not form.is_valid():
        return render(request, "post_new.html", {"form": form, "title_post": title_post, "button_post": button_post})

    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect("index")


def profile(request, username):
    author = get_object_or_404(User, username=username)
    counter = author.posts.count()

    follower_counter = author.follower.count()
    following_counter = author.following.count()

    post_list = author.posts.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)

    if request.user.is_authenticated:
        following = Follow.objects.filter(user=request.user).filter(author=author).exists()
        context = {
            "author": author,
            "counter": counter,
            'page': page,
            'paginator': paginator,
            "follower_counter": follower_counter,
            "following_counter": following_counter,
            'following': following,
            }
    else:
        context = {
            "author": author,
            "counter": counter,
            'page': page,
            'paginator': paginator,
            "follower_counter": follower_counter,
            "following_counter": following_counter,
            }

    return render(request, 'profile.html', context)


def post_view(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)

    author = get_object_or_404(User, username=username)

    comment_list = post.comments.all()

    counter = author.posts.count()

    if request.method != "POST":
        form = CommentForm()
        return render(request, 'post.html', {
            "author": author,
            "counter": counter,
            "post": post,
            "form": form,
            'items': comment_list,
        })

    form = CommentForm(request.POST)
    if not form.is_valid():
        return render(request, 'post.html', {
            "author": author,
            "counter": counter,
            "post": post,
            "form": form,
            'items': comment_list,
        })


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    author = get_object_or_404(User, username=username)

    title_post = "Редактировать запись"
    button_post = "Сохранить запись"

    if author != request.user:
        return redirect("post", username=username, post_id=post_id)

    form = PostForm(request.POST or None, files=request.FILES or None, instance=post)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect("post", username=username, post_id=post_id)

    return render(request, "post_new.html",
                  {"form": form,
                   "post": post,
                   "title_post": title_post,
                   "button_post": button_post})


def page_not_found(request, exception):

    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)


@login_required
def add_comment(request, username, post_id):
    if request.method != "POST":
        return redirect("post", username=f"{username}", post_id=f"{post_id}")

    post = get_object_or_404(Post, id=post_id, author__username=username)

    comment = Comment()
    comment.text = request.POST.get("text")
    comment.author = request.user
    comment.post = post
    comment.save()
    return redirect("post", username=f"{username}", post_id=f"{post_id}")


@login_required
def follow_index(request):
    follows = get_list_or_404(Follow, user=request.user)
    authors = [follow.author for follow in follows]
    post_list = Post.objects.filter(author__in=authors)

    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'follow.html',
        {'page': page, 'paginator': paginator}
    )


@login_required
def profile_follow(request, username):

    author = get_object_or_404(User, username=username)

    if author == request.user:
        return redirect("profile", username=username)

    following = Follow.objects.filter(user=request.user).filter(author=author).exists()
    if following:
        return redirect("profile", username=username)

    follow = Follow()
    follow.author = author
    follow.user = request.user
    follow.save()
    return redirect("profile", username=username)


@login_required
def profile_unfollow(request, username):

    author = get_object_or_404(User, username=username)

    follow = get_object_or_404(Follow, author=author, user=request.user)
    follow.delete()

    return redirect("profile", username=username)