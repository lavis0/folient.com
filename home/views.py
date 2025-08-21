from django.shortcuts import render, HttpResponse, HttpResponseRedirect, redirect, get_object_or_404
from django.http import Http404
from home.models import Blog
from django.contrib import messages
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.db.models import Q
from blogApp.settings import DEFAULT_FROM_EMAIL
import random
import re
import markdown

def index(request):
    blogs = Blog.objects.all().order_by('-time')[:3]
    context = {'blogs': blogs}

    return render(request, 'index.html', context)


def about (request):
    return render(request, 'about.html')

def thanks(request):
    return render(request, 'thanks.html')

def contact (request):
    context = {}
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        message = request.POST.get('message')
        invalid_imput = ['', ' ']
        if name in invalid_imput or email in invalid_imput or phone in invalid_imput or message in invalid_imput:
            messages.error(request, 'One or more fields are empty!')
            context.update({
                'name': name,
                'email': email,
                'phone': phone,
                'message': message,
            })
        else:
            email_pattern = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
            phone_pattern = re.compile(r'^\+?(?=(?:[\s\d]*\d){10,15}$)[\d\s]+$') # (r'^\+?\d{10,12}$')

            is_email_valid = bool(email and email_pattern.match(email))
            is_phone_valid = bool(phone and phone_pattern.match(phone))

            if is_email_valid or is_phone_valid:
                form_data = {
                'name':name,
                'email':email,
                'phone':phone,
                'message':message,
                }
                message = '''
                From:\n\t\t{}\n
                Message:\n\t\t{}\n
                Email:\n\t\t{}\n
                Phone:\n\t\t{}\n
                '''.format(form_data['name'], form_data['message'], form_data['email'],form_data['phone'])
                send_mail('folient: Contact Me', message, DEFAULT_FROM_EMAIL, ['josh@folient.com'], fail_silently=False)
                messages.success(request, 'Your message was sent.')
                # return HttpResponseRedirect('/thanks')
            else:
                messages.error(request, 'Email or Phone is Invalid!')
                context.update({
                    'name': name,
                    'email': email,
                    'phone': phone,
                    'message': message,
                })
    return render(request, 'contact.html', context)

def projects (request):
    return redirect('https://github.com/lavis0', permanent=True)
    # return render(request, 'projects.html')

def blog(request):
    blogs = Blog.objects.all().order_by('-time')
    paginator = Paginator(blogs, 3)
    page = request.GET.get('page')
    blogs = paginator.get_page(page)
    context = {'blogs': blogs}
    return render(request, 'blog.html', context)

def category(request, category):
    category_posts = Blog.objects.filter(category=category).order_by('-time')
    if not category_posts:
        message = f"No posts found in category: '{category}'"
        return render(request, "category.html", {"message": message})
    paginator = Paginator(category_posts, 3)
    page = request.GET.get('page')
    category_posts = paginator.get_page(page)
    return render(request, "category.html", {"category": category, 'category_posts': category_posts})

def categories(request):
    all_categories = Blog.objects.values('category').distinct().order_by('category')
    return render(request, "categories.html", {'all_categories': all_categories})

def search(request):
    query = request.GET.get('q')
    query_list = query.split()
    results = Blog.objects.none()
    for word in query_list:
        results = results | Blog.objects.filter(Q(title__contains=word) | Q(content__contains=word)).order_by('-time')
    paginator = Paginator(results, 3)
    page = request.GET.get('page')
    results = paginator.get_page(page)
    if len(results) == 0:
        message = "Sorry, no results found for your search query."
    else:
        message = ""
    return render(request, 'search.html', {'results': results, 'query': query, 'message': message})


def blogpost (request, slug):
    md = markdown.Markdown(extensions=["extra", "codehilite", 'pymdownx.blocks.admonition',
                                       'pymdownx.blocks.details', 'pymdownx.blocks.tab',
                                       'pymdownx.emoji', "nl2br"])
    try:
        blog_post = Blog.objects.get(slug=slug)
        blog_post.content = md.convert(blog_post.content)
        content = blog_post.content

        # Find admonitions and restructure them
        pattern = r'<div class="admonition ([^"]+)">\s*<p class="admonition-title">([^<]+)</p>\s*(.*?)\s*</div>'

        def replace_admonition(match):
            adm_type = match.group(1)
            title = match.group(2)
            content = match.group(3)

            return f'''<div class="admonition {adm_type}">
                        <div class="admonition-title">{title}</div>
                        <div class="admonition-content">{content}</div>
                    </div>'''

        blog_post.content = re.sub(pattern, replace_admonition, content, flags=re.DOTALL)

        context = {'blog': blog_post}
        return render(request, 'blogpost.html', context)
    except Blog.DoesNotExist:
        context = {'message': 'Blog post not found'}
        return render(request, '404.html', context, status=404)
