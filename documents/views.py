from django.shortcuts import render

# Create your views here.


def render_tos(request):
    return render(request, 'docs/tos.html')


def render_prop(request):
    return render(request, 'docs/proposal.html')


def render_faq(request):
    return render(request, 'docs/FAQ.html')