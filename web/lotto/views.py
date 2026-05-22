import json
import random
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .models import LottoDraw, LottoTicket


def login_view(request):
    if request.user.is_authenticated:
        return redirect('index')
    error = ''
    if request.method == 'POST':
        user = authenticate(request,
                            username=request.POST.get('username', ''),
                            password=request.POST.get('password', ''))
        if user:
            login(request, user)
            return redirect('index')
        error = '아이디 또는 비밀번호가 올바르지 않습니다.'
    return render(request, 'lotto/login.html', {'error': error})


def logout_view(request):
    logout(request)
    return redirect('login')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('index')
    error = ''
    if request.method == 'POST':
        username  = request.POST.get('username', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        if not username:
            error = '아이디를 입력하세요.'
        elif User.objects.filter(username=username).exists():
            error = '이미 사용 중인 아이디입니다.'
        elif len(password1) < 4:
            error = '비밀번호는 4자 이상이어야 합니다.'
        elif password1 != password2:
            error = '비밀번호가 일치하지 않습니다.'
        else:
            User.objects.create_user(username=username, password=password1)
            user = authenticate(request, username=username, password=password1)
            login(request, user)
            return redirect('index')
    return render(request, 'lotto/register.html', {'error': error})


@login_required
def index(request):
    latest = LottoDraw.objects.order_by('-draw_number').first()
    return render(request, 'lotto/index.html', {'latest': latest})


@login_required
def buy_manual(request):
    error = ''
    if request.method == 'POST':
        try:
            nums = [int(request.POST.get(f'n{i}', 0)) for i in range(1, 7)]
            if len(set(nums)) != 6 or not all(1 <= n <= 45 for n in nums):
                error = '1~45 사이의 중복 없는 숫자 6개를 입력하세요.'
            else:
                LottoTicket.objects.create(
                    user=request.user,
                    numbers=json.dumps(sorted(nums)),
                    is_auto=False,
                )
                return redirect('index')
        except (ValueError, TypeError):
            error = '숫자만 입력하세요.'
    return render(request, 'lotto/buy_manual.html', {'error': error})


@login_required
@require_POST
def buy_auto(request):
    nums = sorted(random.sample(range(1, 46), 6))
    LottoTicket.objects.create(
        user=request.user,
        numbers=json.dumps(nums),
        is_auto=True,
    )
    return redirect('index')


def _calc_rank(my_nums, draw):
    my      = set(my_nums)
    win     = set(draw.get_numbers())
    matched = len(my & win)
    bonus   = draw.bonus in my
    if matched == 6:           return 1
    if matched == 5 and bonus: return 2
    if matched == 5:           return 3
    if matched == 4:           return 4
    if matched == 3:           return 5
    return 0


@login_required
def check(request):
    draw    = LottoDraw.objects.order_by('-draw_number').first()
    tickets = []
    if draw:
        for t in LottoTicket.objects.filter(user=request.user).order_by('-purchased_at'):
            rank = _calc_rank(t.get_numbers(), draw)
            tickets.append({'numbers': t.get_numbers(), 'rank': rank})
    return render(request, 'lotto/check.html', {'draw': draw, 'tickets': tickets})


def _admin_required(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            return redirect('index')
        return view_func(request, *args, **kwargs)
    return wrapper


@_admin_required
def admin_sales(request):
    tickets = LottoTicket.objects.select_related('user').order_by('-purchased_at')
    return render(request, 'lotto/admin_sales.html', {'tickets': tickets})


@_admin_required
def admin_draw(request):
    message = ''
    if request.method == 'POST':
        nums  = sorted(random.sample(range(1, 46), 6))
        bonus = random.choice([n for n in range(1, 46) if n not in nums])
        last  = LottoDraw.objects.order_by('-draw_number').first()
        draw  = LottoDraw.objects.create(
            draw_number=last.draw_number + 1 if last else 1,
            numbers=json.dumps(nums),
            bonus=bonus,
        )
        for t in LottoTicket.objects.filter(draw__isnull=True):
            t.draw = draw
            t.rank = _calc_rank(t.get_numbers(), draw)
            t.save()
        message = f'{draw.draw_number}회차 추첨 완료! 당첨번호: {nums}  보너스: {bonus}'
    draws = LottoDraw.objects.order_by('-draw_number')
    return render(request, 'lotto/admin_draw.html', {'draws': draws, 'message': message})


@_admin_required
def admin_winners(request):
    tickets = (LottoTicket.objects
               .filter(rank__isnull=False, rank__gt=0)
               .select_related('user', 'draw')
               .order_by('rank', '-draw__draw_number'))
    return render(request, 'lotto/admin_winners.html', {'tickets': tickets})
