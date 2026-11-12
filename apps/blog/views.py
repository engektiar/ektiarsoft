from django.core.paginator import Paginator
from django.db.models import F, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, render

from apps.core.models import PageContent

from .models import Category, Post


def post_list(request, category_slug=None, tag=None):
    blog_page = PageContent.get("blog")
    if not blog_page.is_published and not request.user.has_perm("core.change_pagecontent"):
        raise Http404
    posts = Post.objects.published().select_related("author", "category")
    category = None
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        posts = posts.filter(category=category)
    if tag:
        posts = posts.filter(tags__icontains=tag)
    q = request.GET.get("q", "").strip()
    if q:
        posts = posts.filter(Q(title__icontains=q) | Q(body__icontains=q) | Q(tags__icontains=q))
    page = Paginator(posts, 9).get_page(request.GET.get("page"))
    return render(request, "blog/list.html", {
        "page_obj": page, "category": category, "tag": tag, "q": q,
        "categories": Category.objects.all(),
        "page": blog_page,
        "sections": blog_page.sections.filter(is_active=True),
    })


def post_detail(request, slug):
    post = get_object_or_404(Post.objects.published().select_related("author", "category"), slug=slug)
    Post.objects.filter(pk=post.pk).update(views=F("views") + 1)
    related = Post.objects.published().filter(category=post.category).exclude(pk=post.pk)[:3]
    return render(request, "blog/detail.html", {"post": post, "related": related})
